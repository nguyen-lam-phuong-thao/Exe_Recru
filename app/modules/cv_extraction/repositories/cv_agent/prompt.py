"""
This module contains prompts for the CV Analysis LangGraph Agent.
Prompts are designed to be:
- Flexible for evaluating CVs from any industry
- Aligned with the latest agent_schema and mapping logic
- Ready for structured extraction and inference
- Easy to extend for new sections or industry-specific needs
"""

# --- CV Cleaning Prompt ---
CV_CLEANING_PROMPT = """
Please clean and structure the following CV content.
- Correct any obvious OCR errors or formatting issues.
- Convert Markdown-like syntax to plain text if necessary, but preserve structure (lists, paragraphs, etc.).
- Ensure the text is readable and well-formatted for further analysis.

CV Content:
{raw_cv_content}
"""

# --- Section Identification Prompt ---
SECTION_IDENTIFICATION_PROMPT = """
Analyze the following processed CV text and identify the main sections.
Return a list of section titles found in the CV. Be flexible and include any industry-specific or uncommon sections.
Examples: Personal Information, Contact, Summary, Objective, Education, Work Experience, Experience, Skills, Projects, Certifications, Awards, Publications, References, Interests, Hobbies, Languages, Volunteer Work, Industry-Specific Sections (e.g., Research, Patents, Clinical Experience).

Processed CV Text:
{processed_cv_text}

Identified Sections (should be a list of strings):
"""

# --- General Extraction System Prompt ---
GENERAL_EXTRACTION_SYSTEM_PROMPT = """
You are an expert CV information extractor. Your task is to extract specific information from the provided CV text or a section of it,
and structure it according to the provided Pydantic schema.
- Only extract information explicitly present in the text. Do not infer or add information not found.
- If a field is optional and the information is not present, omit it or set it to null/None as appropriate for the schema.
- For lists of items (like multiple education entries or jobs), ensure each item is a distinct object within the list.
- Be ready to handle and extract new or industry-specific sections if present.
"""

# --- Section Extraction Prompt Template ---
EXTRACT_SECTION_PROMPT_TEMPLATE = """
From the following CV text, extract all information relevant to the '{section_title}' section.
- Use the provided schema for structuring the output.
- If the section is industry-specific or uncommon, extract as much structured information as possible.

CV Text (or relevant portion):
{cv_text_portion}
"""

# --- Keyword Extraction Prompt ---
EXTRACT_KEYWORDS_PROMPT = """
Based on the entire processed CV text provided below, extract a list of relevant keywords.
These keywords should represent the key skills, technologies, roles, concepts, and any industry-specific terms mentioned in the CV.
Return a list of strings.

Processed CV Text:
{processed_cv_text}
"""

CV_JD_ALIGNMENT_PROMPT = """
You are a hiring expert. Evaluate how well the following candidate's CV matches the provided job description.
Response with only the following information:
1. **Key Matches**: Mention specific qualifications, experiences, or skills in the CV that align with job requirements.
2. **Missing Elements**: Highlight any important qualifications or skills required in the JD that are missing from the CV.
3. **Overall Match Score** (0–100): Estimate how well the candidate fits the role.
4. **Suggestions for Improvement**: Advise how the candidate can tailor their resume better for this job.

Processed CV Text:
{processed_cv_text}

Job Description:
{job_description}
"""

# --- CV Summary Prompt ---
CV_SUMMARY_PROMPT = """
Based on the entire processed CV text provided below, generate a concise professional summary of the candidate’s CV, focusing on how it aligns with the given job description.
- Highlight key experiences, skills, and career objectives if apparent.
- Highlight key overlapping experiences, skills, and potential gaps.
Aim for 3-5 sentences.

Processed CV Text:
{processed_cv_text}

Job Description:
{job_description}
"""

# --- Characteristic Inference System Prompt ---
INFERENCE_SYSTEM_PROMPT = """
You are an expert career analyst. Based on the structured information extracted from the CV,
your task is to infer characteristics about the candidate.
- These characteristics can include potential job roles, key strengths, notable soft skills, technical expertise, and potential areas for development if evident from the CV.
- For each inferred characteristic, provide a statement and, if possible, list evidence or snippets from the CV that support your inference.
- Be ready to infer industry-specific characteristics if the CV is for a specialized field.
Structure your output according to the provided schema.
"""

# --- Characteristic Inference Prompt ---
INFERENCE_PROMPT = """
Here is the structured data extracted from the CV:

Personal Information: {personal_info}
Education History: {education_history}
Work Experience: {work_experience}
Skills: {skills}
Projects: {projects}
Certificates: {certificates}
Interests: {interests}
Other Sections: {other_sections_data}
CV Summary: {cv_summary}
Keywords: {extracted_keywords}

Based on all this information, please infer characteristics about the candidate as per the system prompt and the required output schema.
- If the CV includes industry-specific sections or data, include relevant inferences.
"""

# --- Extensibility Note ---
# To add new industry-specific prompts or section templates, simply define them below using the same pattern.
