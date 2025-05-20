import logging
import uuid
from typing import Dict, List, Any, Optional
from pydantic import BaseModel  # Added import for BaseModel

from app.modules.cv_extraction.repository.cv_agent.agent_schema import (
	CVState,
	PersonalInfoItem,
	EducationItem,
	WorkExperienceItem,
	SkillItem,
	ProjectItem,
	CertificateItem,
	InterestItem,
	InferredCharacteristicItem,
	CVAnalysisResult,
)
from app.modules.cv_extraction.repository.cv_agent.llm_setup import initialize_llm
from app.modules.cv_extraction.repository.cv_agent.prompts import (
	CV_CLEANING_PROMPT,
	SECTION_IDENTIFICATION_PROMPT,
	GENERAL_EXTRACTION_SYSTEM_PROMPT,
	EXTRACT_SECTION_PROMPT_TEMPLATE,
	EXTRACT_KEYWORDS_PROMPT,
	CV_SUMMARY_PROMPT,
	INFERENCE_SYSTEM_PROMPT,
	INFERENCE_PROMPT,
)
from app.modules.cv_extraction.repository.cv_agent.utils import (
	TokenTracker,
	count_tokens,
	calculate_price,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


class CVProcessorWorkflow:
	"""
	Manages the LangGraph workflow for CV analysis, including node definitions
	and graph construction based on the PlantUML diagram.
	"""

	def __init__(self, api_key: str):
		self.logger = logging.getLogger(self.__class__.__name__)
		self.llm = initialize_llm(api_key)
		self.token_tracker = TokenTracker()
		self.memory = MemorySaver()  # In-memory checkpointer for state
		self.workflow = self._build_graph()

	# --- Node Definitions ---

	async def input_handler_node(self, state: CVState) -> Dict[str, Any]:
		"""Handles initial input and starts the process."""
		self.logger.info('InputHandlerNode: Starting CV analysis.')
		# raw_cv_content is expected to be in the initial state
		if not state.get('raw_cv_content'):
			self.logger.error('InputHandlerNode: No raw_cv_content provided.')
			# Potentially raise an error or set a flag
			return {'raw_cv_content': ''}  # Ensure it's not None for next steps
		return {
			'raw_cv_content': state['raw_cv_content'],
			'messages': [SystemMessage(content='CV analysis process started.')],
		}

	async def cv_parser_node(self, state: CVState) -> Dict[str, Any]:
		"""Cleans and structures the raw CV content."""
		self.logger.info('CVParserNode: Parsing and cleaning CV content.')
		raw_cv_content = state.get('raw_cv_content', '')

		prompt = CV_CLEANING_PROMPT.format(raw_cv_content=raw_cv_content)
		input_tokens = count_tokens(prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens)

		response = await self.llm.ainvoke(prompt)
		processed_cv_text = response.content

		output_tokens = count_tokens(processed_cv_text, 'gemini')
		self.token_tracker.add_output_tokens(output_tokens)

		self.logger.info(f'CVParserNode: CV content cleaned. Length: {len(processed_cv_text)}')
		return {
			'processed_cv_text': processed_cv_text,
			'messages': state.get('messages', []) + [AIMessage(content=f'CV parsed. Cleaned text length: {len(processed_cv_text)}')],
		}

	async def section_identifier_node(self, state: CVState) -> Dict[str, Any]:
		"""Identifies sections within the processed CV text."""
		self.logger.info('SectionIdentifierNode: Identifying CV sections.')
		processed_cv_text = state.get('processed_cv_text', '')

		prompt = SECTION_IDENTIFICATION_PROMPT.format(processed_cv_text=processed_cv_text)
		input_tokens = count_tokens(prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens)

		# Assuming LLM returns a list-like string, e.g., "['Education', 'Experience']"
		# or a more structured format if using with_structured_output for a simple list model
		response = await self.llm.ainvoke(prompt)
		identified_sections_str = response.content
		output_tokens = count_tokens(identified_sections_str, 'gemini')
		self.token_tracker.add_output_tokens(output_tokens)

		try:
			# Basic parsing for a string representation of a list
			# For more robust parsing, consider a Pydantic model for the LLM to output
			identified_sections = eval(identified_sections_str) if identified_sections_str.startswith('[') else [s.strip() for s in identified_sections_str.split(',')]
		except Exception as e:
			self.logger.error(f'SectionIdentifierNode: Error parsing identified sections: {e}. Defaulting to empty list.')
			identified_sections = []

		self.logger.info(f'SectionIdentifierNode: Identified sections: {identified_sections}')
		return {
			'identified_sections': identified_sections,
			'messages': state.get('messages', []) + [AIMessage(content=f'Identified sections: {", ".join(identified_sections)}')],
		}

	async def _extract_structured_data(self, cv_text_portion: str, schema: type, section_title: str) -> List[BaseModel]:
		"""Helper to extract data for a given schema using with_structured_output."""
		self.logger.info(f"InformationExtractorNode: Extracting data for section '{section_title}' with schema {schema.__name__}.")

		system_prompt_with_schema = f'{GENERAL_EXTRACTION_SYSTEM_PROMPT}\n\nThe output MUST be structured according to the following Pydantic schema: \n{schema.schema_json(indent=2)}'

		user_prompt = EXTRACT_SECTION_PROMPT_TEMPLATE.format(section_title=section_title, cv_text_portion=cv_text_portion)

		full_prompt_for_tokens = system_prompt_with_schema + '\n' + user_prompt
		input_tokens = count_tokens(full_prompt_for_tokens, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens)

		structured_llm = self.llm.with_structured_output(schema)

		try:
			extracted_data = await structured_llm.ainvoke([
				SystemMessage(content=system_prompt_with_schema),
				HumanMessage(content=user_prompt),
			])

			if not isinstance(extracted_data, list) and extracted_data is not None:
				extracted_data = [extracted_data]
			elif extracted_data is None:
				extracted_data = []

			output_tokens = count_tokens(str(extracted_data), 'gemini')
			self.token_tracker.add_output_tokens(output_tokens)
			self.logger.info(f"InformationExtractorNode: Successfully extracted {len(extracted_data)} items for '{section_title}'.")
			return extracted_data
		except Exception as e:
			self.logger.error(f"InformationExtractorNode: Error extracting '{section_title}': {e}")
			return []

	async def information_extractor_node(self, state: CVState) -> Dict[str, Any]:
		"""Extracts detailed information from CV sections using Pydantic schemas."""
		self.logger.info('InformationExtractorNode: Starting information extraction.')
		processed_cv_text = state.get('processed_cv_text', '')
		identified_sections = state.get('identified_sections', [])

		extracted_data_update = {
			'personal_info_item': None,
			'education_items': [],
			'work_experience_items': [],
			'skill_items': [],
			'project_items': [],
			'certificate_items': [],
			'interest_items': [],
			'other_extracted_data': {},
			'extracted_keywords': [],
			'cv_summary': '',
		}

		section_to_schema_map = {
			('personal information', 'contact', 'about me'): (
				PersonalInfoItem,
				'personal_info_item',
			),
			('education', 'academic background', 'qualifications'): (
				List[EducationItem],
				'education_items',
			),
			(
				'work experience',
				'experience',
				'employment history',
				'professional experience',
			): (List[WorkExperienceItem], 'work_experience_items'),
			('skills', 'technical skills', 'languages'): (
				List[SkillItem],
				'skill_items',
			),
			('projects', 'personal projects', 'portfolio'): (
				List[ProjectItem],
				'project_items',
			),
			('certifications', 'courses', 'licenses'): (
				List[CertificateItem],
				'certificate_items',
			),
			('interests', 'hobbies'): (List[InterestItem], 'interest_items'),
		}

		current_messages = state.get('messages', [])

		for section_title in identified_sections:
			matched = False
			for keywords, (schema, state_key) in section_to_schema_map.items():
				if any(keyword in section_title.lower() for keyword in keywords):
					extracted_items = await self._extract_structured_data(processed_cv_text, schema, section_title)

					if state_key == 'personal_info_item':
						extracted_data_update[state_key] = extracted_items[0] if extracted_items else None
					else:
						extracted_data_update[state_key] = extracted_items

					current_messages.append(AIMessage(content=f'Extracted {len(extracted_items)} items for section: {section_title}'))
					matched = True
					break
			if not matched:
				self.logger.info(f"InformationExtractorNode: Section '{section_title}' not mapped to a specific schema. Storing as other data.")
				current_messages.append(AIMessage(content=f"Section '{section_title}' noted as other data."))

		keyword_prompt = EXTRACT_KEYWORDS_PROMPT.format(processed_cv_text=processed_cv_text)
		input_tokens_kw = count_tokens(keyword_prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens_kw)
		keyword_response = await self.llm.ainvoke(keyword_prompt)
		extracted_keywords_str = keyword_response.content
		output_tokens_kw = count_tokens(extracted_keywords_str, 'gemini')
		self.token_tracker.add_output_tokens(output_tokens_kw)
		try:
			extracted_data_update['extracted_keywords'] = eval(extracted_keywords_str) if extracted_keywords_str.startswith('[') else [s.strip() for s in extracted_keywords_str.split(',')]
		except:
			extracted_data_update['extracted_keywords'] = []
		current_messages.append(AIMessage(content=f'Extracted keywords: {extracted_data_update["extracted_keywords"]}'))

		summary_prompt = CV_SUMMARY_PROMPT.format(processed_cv_text=processed_cv_text)
		input_tokens_sum = count_tokens(summary_prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens_sum)
		summary_response = await self.llm.ainvoke(summary_prompt)
		extracted_data_update['cv_summary'] = summary_response.content
		output_tokens_sum = count_tokens(extracted_data_update['cv_summary'], 'gemini')
		self.token_tracker.add_output_tokens(output_tokens_sum)
		current_messages.append(AIMessage(content=f'Generated CV summary.'))

		extracted_data_update['messages'] = current_messages
		self.logger.info('InformationExtractorNode: Information extraction phase complete.')
		return extracted_data_update

	async def characteristic_inference_node(self, state: CVState) -> Dict[str, Any]:
		"""Infers candidate characteristics based on extracted CV data."""
		self.logger.info('CharacteristicInferenceNode: Inferring characteristics.')

		inference_prompt_filled = INFERENCE_PROMPT.format(
			personal_info=state.get('personal_info_item'),
			education_history=state.get('education_items'),
			work_experience=state.get('work_experience_items'),
			skills=state.get('skill_items'),
			projects=state.get('project_items'),
			certificates=state.get('certificate_items'),
			interests=state.get('interest_items'),
			other_sections_data=state.get('other_extracted_data'),
			cv_summary=state.get('cv_summary'),
			extracted_keywords=state.get('extracted_keywords'),
		)

		system_prompt_with_schema = (
			f'{INFERENCE_SYSTEM_PROMPT}\n\nThe output MUST be structured according to the following Pydantic schema: \n{List[InferredCharacteristicItem].__args__[0].schema_json(indent=2)}'
		)

		full_prompt_for_tokens = system_prompt_with_schema + '\n' + inference_prompt_filled
		input_tokens = count_tokens(full_prompt_for_tokens, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens)

		structured_llm = self.llm.with_structured_output(List[InferredCharacteristicItem])
		try:
			inferred_characteristics = await structured_llm.ainvoke([
				SystemMessage(content=system_prompt_with_schema),
				HumanMessage(content=inference_prompt_filled),
			])
			if inferred_characteristics is None:
				inferred_characteristics = []
			output_tokens = count_tokens(str(inferred_characteristics), 'gemini')
			self.token_tracker.add_output_tokens(output_tokens)
			self.logger.info(f'CharacteristicInferenceNode: Inferred {len(inferred_characteristics)} characteristics.')
		except Exception as e:
			self.logger.error(f'CharacteristicInferenceNode: Error inferring characteristics: {e}')
			inferred_characteristics = []

		return {
			'inferred_characteristics': inferred_characteristics,
			'messages': state.get('messages', []) + [AIMessage(content=f'Inferred {len(inferred_characteristics)} characteristics.')],
		}

	async def output_aggregator_node(self, state: CVState) -> Dict[str, Any]:
		"""Aggregates all data into the final CVAnalysisResult model."""
		self.logger.info('OutputAggregatorNode: Aggregating final results.')

		final_result = CVAnalysisResult(
			raw_cv_content=state.get('raw_cv_content'),
			processed_cv_text=state.get('processed_cv_text'),
			identified_sections=state.get('identified_sections', []),
			personal_information=state.get('personal_info_item'),
			education_history=state.get('education_items', []),
			work_experience_history=state.get('work_experience_items', []),
			skills_summary=state.get('skill_items', []),
			projects_showcase=state.get('project_items', []),
			certificates_and_courses=state.get('certificate_items', []),
			interests_and_hobbies=state.get('interest_items', []),
			other_sections_data=state.get('other_extracted_data', {}),
			cv_summary=state.get('cv_summary'),
			extracted_keywords=state.get('extracted_keywords', []),
			inferred_characteristics=state.get('inferred_characteristics', []),
			llm_token_usage={
				'input_tokens': self.token_tracker.input_tokens,
				'output_tokens': self.token_tracker.output_tokens,
				'total_tokens': self.token_tracker.total_tokens,
				'price_usd': round(
					calculate_price(
						self.token_tracker.input_tokens,
						self.token_tracker.output_tokens,
					),
					6,
				),
			},
		)
		self.logger.info('OutputAggregatorNode: Final result aggregated.')
		return {
			'final_analysis_result': final_result,
			'messages': state.get('messages', []) + [AIMessage(content='CV analysis complete. Final result aggregated.')],
		}

	def _build_graph(self) -> StateGraph:
		"""Constructs the LangGraph StateGraph for CV processing."""
		self.logger.info('Building CV analysis workflow graph.')
		workflow = StateGraph(CVState)

		# Add nodes based on the PlantUML diagram
		workflow.add_node('InputHandler', self.input_handler_node)
		workflow.add_node('CVParser', self.cv_parser_node)
		workflow.add_node('SectionIdentifier', self.section_identifier_node)
		workflow.add_node('InformationExtractor', self.information_extractor_node)
		workflow.add_node('CharacteristicInference', self.characteristic_inference_node)
		workflow.add_node('OutputAggregator', self.output_aggregator_node)

		# Define edges for the workflow
		workflow.add_edge(START, 'InputHandler')
		workflow.add_edge('InputHandler', 'CVParser')
		workflow.add_edge('CVParser', 'SectionIdentifier')
		workflow.add_edge('SectionIdentifier', 'InformationExtractor')
		workflow.add_edge('InformationExtractor', 'CharacteristicInference')
		workflow.add_edge('CharacteristicInference', 'OutputAggregator')
		workflow.add_edge('OutputAggregator', END)

		return workflow.compile(checkpointer=self.memory)

	async def analyze_cv(self, cv_content: str) -> Optional[CVAnalysisResult]:
		"""Public method to process a CV and return the analysis result."""
		self.logger.info(f'Starting CV analysis for content of length: {len(cv_content)}')
		self.token_tracker.reset()

		thread_id = str(uuid.uuid4())
		config = {'configurable': {'thread_id': thread_id}}

		initial_state = CVState(
			messages=[],
			raw_cv_content=cv_content,
			processed_cv_text=None,
			identified_sections=None,
			personal_info_item=None,
			education_items=None,
			work_experience_items=None,
			skill_items=None,
			project_items=None,
			certificate_items=None,
			interest_items=None,
			other_extracted_data=None,
			extracted_keywords=None,
			cv_summary=None,
			inferred_characteristics=None,
			token_usage=None,
			final_analysis_result=None,
		)

		try:
			final_state_result = await self.workflow.ainvoke(initial_state, config=config)
			if final_state_result and 'final_analysis_result' in final_state_result:
				self.logger.info('CV analysis completed successfully.')
				return final_state_result['final_analysis_result']
			else:
				self.logger.error('CV analysis finished but no final_analysis_result found in state.')
				return None
		except Exception as e:
			self.logger.exception(f'Error during CV analysis workflow: {e}')
			error_result = CVAnalysisResult(
				raw_cv_content=cv_content,
				processed_cv_text=initial_state.get('processed_cv_text'),
				cv_summary=f'Error during analysis: {str(e)}',
				llm_token_usage={
					'input_tokens': self.token_tracker.input_tokens,
					'output_tokens': self.token_tracker.output_tokens,
					'total_tokens': self.token_tracker.total_tokens,
					'price_usd': round(
						calculate_price(
							self.token_tracker.input_tokens,
							self.token_tracker.output_tokens,
						),
						6,
					),
				},
			)
			return error_result
