import json
import logging
import asyncio
import time
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import GOOGLE_API_KEY
from app.modules.job_matching.workflows.matching.engine.llm_setup import initialize_llm
from app.modules.job_matching.workflows.matching.engine.utils import TokenTracker, count_tokens
from app.modules.job_matching.workflows.matching.config.prompts import JobMatchingPrompts
from app.modules.job_matching.workflows.matching.config.fallback import JobMatchingFallback
from app.modules.job_matching.workflows.matching.config.workflow_config import JobMatchingWorkflowConfig
from app.modules.job_matching.workflows.matching.schemas.matching import (
    JobMatchingState,
    CourseSuggestion,
    JobSuggestion,
    CareerPathAnalysis
)

logger = logging.getLogger(__name__)

class JobMatchingAgent:
    """Agent xử lý job matching - nhận dữ liệu từ cv_extraction và sinh gợi ý"""
    
    def __init__(self, config: JobMatchingWorkflowConfig):
        self.config = config
        self.token_tracker = TokenTracker()
        
        # Khởi tạo LLM giống như cv_extraction
        self.llm = initialize_llm(self.config.google_api_key)
        
        # Circuit breaker state
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0
        self.circuit_breaker_threshold = 3
        self.circuit_breaker_timeout = 60  # 60 seconds
        
        # Rate limiting
        self.last_api_call = 0
        self.min_call_interval = 1  # 1 second between calls
        
        logger.info("JobMatchingAgent initialized successfully")
    
    def _is_circuit_breaker_open(self) -> bool:
        """Kiểm tra circuit breaker có đang mở không"""
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            time_since_last_failure = time.time() - self.circuit_breaker_last_failure
            if time_since_last_failure < self.circuit_breaker_timeout:
                logger.warning(f"Circuit breaker is open. Time remaining: {self.circuit_breaker_timeout - time_since_last_failure:.1f}s")
                return True
            else:
                # Reset circuit breaker after timeout
                logger.info("Circuit breaker timeout reached, resetting...")
                self.circuit_breaker_failures = 0
                return False
        return False
    
    def _record_failure(self):
        """Ghi nhận lỗi cho circuit breaker"""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
        logger.warning(f"Circuit breaker failure count: {self.circuit_breaker_failures}")
    
    def _record_success(self):
        """Ghi nhận thành công cho circuit breaker"""
        self.circuit_breaker_failures = 0
        logger.info("Circuit breaker reset due to success")
    
    async def _rate_limit(self):
        """Rate limiting để tránh quá tải API"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_call_interval:
            wait_time = self.min_call_interval - time_since_last_call
            logger.info(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        self.last_api_call = time.time()
    
    async def _call_llm(self, prompt: str, max_retries: int = 3) -> str:
        """Gọi LLM với prompt - cải thiện error handling và retry logic"""
        
        # Kiểm tra circuit breaker
        if self._is_circuit_breaker_open():
            logger.warning("Circuit breaker is open, using fallback immediately")
            return '{}'
        
        for attempt in range(max_retries):
            try:
                # Rate limiting
                await self._rate_limit()
                
                logger.info(f"=== CALLING LLM (Attempt {attempt + 1}/{max_retries}) ===")
                logger.info(f"Prompt length: {len(prompt)}")
                
                # Đếm tokens
                input_tokens = count_tokens(prompt, 'gemini-2.0-flash')
                self.token_tracker.add_input_tokens(input_tokens)
                
                # Gọi LLM API
                logger.info("Calling LLM API...")
                response = await self.llm.ainvoke(prompt)
                
                # Đếm output tokens
                output_tokens = count_tokens(response.content, 'gemini-2.0-flash')
                self.token_tracker.add_output_tokens(output_tokens)
                
                # In chi tiết kết quả từ LLM ra terminal
                print("\n" + "="*80)
                print("🔍 LLM RESPONSE DETAILS")
                print("="*80)
                print(f"📄 Response content: {response.content}")
                print(f"🔤 Response content type: {type(response.content)}")
                print(f"📏 Response content length: {len(response.content) if response.content else 0}")
                print("="*80)
                
                # Log chi tiết
                logger.info(f"Response content: {response.content}")
                logger.info(f"Response content type: {type(response.content)}")
                logger.info(f"Response content length: {len(response.content) if response.content else 0}")
                
                # Kiểm tra response content
                if not response.content:
                    print("⚠️  Empty response from LLM")
                    self._record_failure()
                    if attempt < max_retries - 1:
                        print(f"🔄 Retrying... (Attempt {attempt + 2}/{max_retries})")
                        continue
                    else:
                        print("⚠️  All retries failed, using fallback")
                        logger.warning("All retries failed, using fallback")
                        return '{}'
                
                # Kiểm tra nếu response có chứa JSON
                content = response.content.strip()
                
                # Kiểm tra nếu có JSON trong markdown code block hoặc pure JSON
                if '```json' in content or (content.startswith('{') and content.endswith('}')):
                    print("✅ LLM response received successfully")
                    self._record_success()  # Reset circuit breaker
                    return response.content
                else:
                    print("⚠️  Response is not JSON format")
                    print(f"Response starts with: {content[:50]}...")
                    
                    if attempt < max_retries - 1:
                        print(f"🔄 Retrying with clearer prompt... (Attempt {attempt + 2}/{max_retries})")
                        # Thêm instruction rõ ràng hơn
                        enhanced_prompt = prompt + "\n\nQUAN TRỌNG: Chỉ trả về JSON, không có text nào khác!"
                        continue
                    else:
                        print("⚠️  All retries failed, using fallback")
                        self._record_failure()
                        return '{}'
                
            except Exception as e:
                logger.error(f"Error calling LLM (Attempt {attempt + 1}): {e}")
                logger.error(f"Exception type: {type(e)}")
                
                # Ghi nhận lỗi cho circuit breaker
                self._record_failure()
                
                # Xử lý các loại lỗi cụ thể
                if "ResourceExhausted" in str(e):
                    print(f"⚠️  ResourceExhausted error detected")
                    print(f"⚠️  This usually means API quota exceeded or rate limit hit")
                    
                    # Exponential backoff cho ResourceExhausted
                    wait_time = min(2 ** attempt, 30)  # Max 30 seconds
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    
                elif "QuotaExceeded" in str(e):
                    print(f"⚠️  Quota exceeded error")
                    print(f"⚠️  Using fallback immediately")
                    return '{}'
                    
                elif "RateLimitExceeded" in str(e):
                    print(f"⚠️  Rate limit exceeded")
                    wait_time = min(5 * (attempt + 1), 60)  # Max 60 seconds
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying after error... (Attempt {attempt + 2}/{max_retries})")
                    continue
                else:
                    print("⚠️  All retries failed, using fallback")
                    return '{}'
        
        # Fallback nếu tất cả retry đều thất bại
        return '{}'
    
    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON response từ LLM - luôn trả về dict"""
        try:
            response = response.strip()
            
            # Loại bỏ markdown code block nếu có
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.rfind('```')
                if end > start:
                    response = response[start:end].strip()
                    print(f"🔍 Extracted JSON from markdown: {response[:100]}...")
            elif '```' in response:
                start = response.find('```') + 3
                end = response.rfind('```')
                if end > start:
                    response = response[start:end].strip()
                    print(f"🔍 Extracted JSON from code block: {response[:100]}...")
            
            # Parse JSON
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                print("✅ JSON parsed successfully")
                return parsed
            else:
                print("⚠️  Parsed result is not dict, using fallback")
                return JobMatchingFallback.get_fallback_response("not_dict")
                
        except Exception as e:
            print(f"❌ JSON parse error: {e}")
            print(f"❌ Response content: {response[:200]}...")
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Response content: {response}")
            return JobMatchingFallback.get_fallback_response("error")
    
    def _fix_json_string(self, json_str: str) -> str:
        """Fix common JSON formatting issues"""
        try:
            # Remove extra whitespace and newlines
            json_str = json_str.replace('\n', ' ').replace('\r', ' ')
            json_str = ' '.join(json_str.split())
            
            # Fix trailing commas
            json_str = json_str.rstrip(',')
            
            # Fix missing quotes around keys
            import re
            # Pattern to match unquoted keys
            pattern = r'(\s*)(\w+)(\s*):'
            json_str = re.sub(pattern, r'\1"\2"\3:', json_str)
            
            # Fix single quotes to double quotes
            json_str = json_str.replace("'", '"')
            
            # Fix missing quotes around string values
            # Pattern to match unquoted string values
            pattern = r':\s*([^",\{\}\[\]\d][^,\{\}\[\]]*[^",\{\}\[\]\s])\s*([,\}\]])'
            json_str = re.sub(pattern, r': "\1"\2', json_str)
            
            logger.info(f"Fixed JSON string: {json_str}")
            return json_str
        except Exception as e:
            logger.warning(f"Error fixing JSON string: {e}")
            return json_str
    
    async def process_job_matching(self, jd_alignment: str, cv_analysis_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process job matching - nhận dữ liệu từ cv_extraction và sinh gợi ý"""
        logger.info("Starting job matching process")
        
        try:
            # Import cần thiết
            import uuid
            from datetime import datetime
            
            # Kiểm tra input và log chi tiết
            logger.info(f"JD Alignment: {jd_alignment}")
            logger.info(f"CV Analysis Result: {cv_analysis_result}")
            logger.info(f"CV Analysis Result type: {type(cv_analysis_result)}")
            
            if not cv_analysis_result:
                logger.warning("No CV analysis result provided - using JD-only analysis")
                # Tạo CV data mẫu dựa trên JD để LLM có thể phân tích
                cv_analysis_result = {
                    "name": "Ứng viên",
                    "summary": "Thông tin CV chưa được cung cấp",
                    "skills": [],
                    "experience": [],
                    "education": []
                }
            
            # Kiểm tra xem cv_analysis_result có dữ liệu thực sự không
            if isinstance(cv_analysis_result, dict):
                has_real_data = any([
                    cv_analysis_result.get('name') and cv_analysis_result.get('name') != 'Ứng viên',
                    cv_analysis_result.get('skills'),
                    cv_analysis_result.get('experience'),
                    cv_analysis_result.get('education')
                ])
                
                if not has_real_data:
                    logger.warning("CV analysis result is empty or has no meaningful data")
                    cv_analysis_result = {
                        "name": "Ứng viên",
                        "summary": "Thông tin CV chưa được cung cấp đầy đủ",
                        "skills": [],
                        "experience": [],
                        "education": []
                    }
            
            # Tạo prompt với dữ liệu từ cv_extraction
            prompt = JobMatchingPrompts.create_job_matching_prompt(cv_analysis_result, jd_alignment)
            logger.info(f"Created prompt with length: {len(prompt)}")
            
            # In prompt ra terminal để debug
            print("\n" + "="*80)
            print("📝 PROMPT GỬI LLM (JOB MATCHING)")
            print("="*80)
            print(prompt)
            print("="*80)
            
            logger.info("Calling LLM for job matching analysis")
            
            # Gọi LLM
            response = await self._call_llm(prompt)
            
            # Parse response
            parsed_result = self._parse_json_response(response)
            
            logger.info(f"LLM response parsed successfully: {type(parsed_result)}")
            logger.info(f"Parsed result keys: {list(parsed_result.keys()) if isinstance(parsed_result, dict) else 'Not a dict'}")
            
            # Kiểm tra xem kết quả có rỗng không
            is_empty_result = (
                not parsed_result.get("missing_skills") and
                not parsed_result.get("suggested_courses") and
                not parsed_result.get("suggested_jobs") and
                not parsed_result.get("career_path_analysis", {}).get("career_path")
            )
            
            if is_empty_result:
                logger.warning("LLM returned empty result, using fallback")
                # Sử dụng fallback dựa trên JD alignment
                if "data" in jd_alignment.lower() or "analyst" in jd_alignment.lower():
                    parsed_result = JobMatchingFallback.get_data_science_fallback()
                elif "developer" in jd_alignment.lower() or "programmer" in jd_alignment.lower():
                    parsed_result = JobMatchingFallback.get_software_development_fallback()
                else:
                    parsed_result = JobMatchingFallback.get_general_fallback()
                logger.info("Applied fallback data")
            
            # Validate và format kết quả
            result = {
                "missing_skills": parsed_result.get("missing_skills", []),
                "suggested_courses": parsed_result.get("suggested_courses", []),
                "suggested_jobs": parsed_result.get("suggested_jobs", []),
                "career_path_analysis": parsed_result.get("career_path_analysis", {}),
                "processing_status": "completed",
                "session_id": str(uuid.uuid4()),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Log kết quả
            logger.info(f"Job matching completed. Found {len(result['missing_skills'])} missing skills, "
                       f"{len(result['suggested_courses'])} courses, {len(result['suggested_jobs'])} jobs")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in job matching process: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return error result
            return {
                "missing_skills": [],
                "suggested_courses": [],
                "suggested_jobs": [],
                "career_path_analysis": {},
                "processing_status": "error",
                "error_message": str(e),
                "session_id": str(uuid.uuid4()),
                "analysis_timestamp": datetime.now().isoformat()
            } 