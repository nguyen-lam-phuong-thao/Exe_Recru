import json
import os
import logging
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import GOOGLE_API_KEY

# Thiết lập logger
logger = logging.getLogger(__name__)

def initialize_llm():
    """Khởi tạo LLM cho job matching"""
    return ChatGoogleGenerativeAI(
        model='gemini-2.0-flash',
        api_key=GOOGLE_API_KEY,
        temperature=0.7,
    )

# Prompt cho gợi ý việc làm
JOB_SUGGESTION_PROMPT = """
Bạn là chuyên gia tư vấn nghề nghiệp. Dựa trên thông tin CV của ứng viên, hãy gợi ý các vị trí việc làm phù hợp.

**Thông tin CV:**
- Kỹ năng: {skills}
- Kinh nghiệm làm việc: {experience}
- Dự án: {projects}
- Chứng chỉ: {certifications}
- Tóm tắt: {summary}

**Yêu cầu:**
1. Gợi ý 5 vị trí việc làm phù hợp nhất 
2. Cho mỗi vị trí, đưa ra:
   - Tên vị trí
   - Mô tả ngắn gọn
   - Công ty
   - Địa điểmđiểm
   - Lý do phù hợp (dựa trên kỹ năng/kinh nghiệm)
   - Mức độ phù hợp (1-10)
3. Sắp xếp theo mức độ phù hợp giảm dần

**QUAN TRỌNG: Chỉ trả về JSON thuần túy, không có markdown formatting, không có text giải thích.**

**Định dạng trả về (chỉ JSON):**
{{
  "job_suggestions": [
    {{
      "position": "Tên vị trí",
      "description": "Mô tả ngắn gọn",
      "company": "Tên công ty",
      "location": "Địa điểm",
      "reason": "Lý do phù hợp",
      "match_score": 8,
      "required_skills": ["skill1", "skill2"],
      "missing_skills": ["skill3", "skill4"]
    }}
  ]
}}
"""

# Prompt cho gợi ý khóa học
COURSE_SUGGESTION_PROMPT = """
Bạn là chuyên gia tư vấn đào tạo. Dựa trên thông tin CV và các kỹ năng còn thiếu, hãy gợi ý các khóa học phù hợp.

**Thông tin CV:**
- Kỹ năng hiện tại: {current_skills}
- Kỹ năng còn thiếu: {missing_skills}
- Mục tiêu nghề nghiệp: {career_goals}

**Yêu cầu:**
1. Gợi ý 5 khóa học phù hợp nhất
2. Cho mỗi khóa học, đưa ra:
   - Tên khóa học
   - Nhà cung cấp (Coursera, Udemy, edX, etc.)
   - Kỹ năng sẽ học được
   - Thời gian học ước tính
   - Mức độ phù hợp (1-10)
3. Ưu tiên các khóa học bổ sung kỹ năng còn thiếu

**Định dạng trả về (JSON):**
{{
  "course_suggestions": [
    {{
      "course_name": "Tên khóa học",
      "provider": "Nhà cung cấp",
      "skills_covered": ["skill1", "skill2"],
      "duration": "4-6 tuần",
      "match_score": 9,
      "description": "Mô tả ngắn gọn khóa học"
    }}
  ]
}}
"""

class JobMatchingService:
    def __init__(self):
        self.llm = initialize_llm()
    
    async def get_result_cv_extraction(self, filename: str) -> Optional[Dict[str, Any]]:
        """Lấy kết quả phân tích CV từ file JSON đã lưu"""
        try:
            # Đường dẫn đến file JSON
            json_file_path = os.path.join("results", f"{filename}.json")
            logger.info(f"Looking for CV result file: {json_file_path}")
            
            if not os.path.exists(json_file_path):
                logger.warning(f"CV result file not found: {json_file_path}")
                return None
            
            # Đọc file JSON
            with open(json_file_path, 'r', encoding='utf-8') as f:
                cv_data = json.load(f)
            
            logger.info(f"Successfully loaded CV data from {json_file_path}")
            return cv_data
            
        except Exception as e:
            logger.error(f"Error reading CV result file: {e}")
            return None
    
    def _extract_skills(self, cv_result: Dict[str, Any]) -> List[str]:
        """Trích xuất kỹ năng từ kết quả CV"""
        try:
            if isinstance(cv_result, dict):
                cv_analysis = cv_result.get("data", {}).get("cv_analysis_result", {})
                # Thử cấu trúc mới trước
                if cv_analysis and cv_analysis.get("skills"):
                    return cv_analysis["skills"]
                # Fallback về cấu trúc cũ
                elif cv_analysis and cv_analysis.get("skills_summary", {}).get("items"):
                    return [skill.get("skill_name", "") for skill in cv_analysis["skills_summary"]["items"]]
            return []
        except Exception as e:
            logger.error(f"Error extracting skills: {e}")
            return []
    
    def _extract_experience(self, cv_result: Dict[str, Any]) -> List[str]:
        """Trích xuất kinh nghiệm từ kết quả CV"""
        try:
            if isinstance(cv_result, dict):
                cv_analysis = cv_result.get("data", {}).get("cv_analysis_result", {})
                # Thử cấu trúc mới trước
                if cv_analysis and cv_analysis.get("experience"):
                    return [exp.get("description", "") for exp in cv_analysis["experience"]]
                # Fallback về cấu trúc cũ
                elif cv_analysis and cv_analysis.get("work_experience_history", {}).get("items"):
                    return [exp.get("description", "") for exp in cv_analysis["work_experience_history"]["items"]]
            return []
        except Exception as e:
            logger.error(f"Error extracting experience: {e}")
            return []
    
    def _extract_education(self, cv_result: Dict[str, Any]) -> List[str]:
        """Trích xuất học vấn từ kết quả CV"""
        try:
            if isinstance(cv_result, dict):
                cv_analysis = cv_result.get("data", {}).get("cv_analysis_result", {})
                # Thử cấu trúc mới trước
                if cv_analysis and cv_analysis.get("education"):
                    return [edu.get("description", "") for edu in cv_analysis["education"]]
                # Fallback về cấu trúc cũ
                elif cv_analysis and cv_analysis.get("education_history", {}).get("items"):
                    return [edu.get("description", "") for edu in cv_analysis["education_history"]["items"]]
            return []
        except Exception as e:
            logger.error(f"Error extracting education: {e}")
            return []
    
    def _extract_projects(self, cv_result: Dict[str, Any]) -> List[str]:
        """Trích xuất dự án từ kết quả CV"""
        try:
            if isinstance(cv_result, dict):
                cv_analysis = cv_result.get("data", {}).get("cv_analysis_result", {})
                if cv_analysis and cv_analysis.get("projects"):
                    return [proj.get("description", "") for proj in cv_analysis["projects"]]
            return []
        except Exception as e:
            logger.error(f"Error extracting projects: {e}")
            return []
    
    def _extract_certifications(self, cv_result: Dict[str, Any]) -> List[str]:
        """Trích xuất chứng chỉ từ kết quả CV"""
        try:
            if isinstance(cv_result, dict):
                cv_analysis = cv_result.get("data", {}).get("cv_analysis_result", {})
                if cv_analysis and cv_analysis.get("certifications"):
                    return [cert.get("name", "") for cert in cv_analysis["certifications"]]
            return []
        except Exception as e:
            logger.error(f"Error extracting certifications: {e}")
            return []
    
    def _extract_summary(self, cv_result: Dict[str, Any]) -> str:
        """Trích xuất tóm tắt từ kết quả CV"""
        try:
            if isinstance(cv_result, dict):
                cv_analysis = cv_result.get("data", {}).get("cv_analysis_result", {})
                if cv_analysis and cv_analysis.get("summary"):
                    return cv_analysis["summary"]
            return ""
        except Exception as e:
            logger.error(f"Error extracting summary: {e}")
            return ""
    
    def _create_job_matching_prompt(self, skills: List[str], experience: List[str], education: List[str], projects: List[str] = None, certifications: List[str] = None, summary: str = "") -> str:
        """Tạo prompt cho job matching"""
        if projects is None:
            projects = []
        if certifications is None:
            certifications = []
            
        return JOB_SUGGESTION_PROMPT.format(
            skills=", ".join(skills),
            experience="; ".join(experience),
            projects="; ".join(projects),
            certifications=", ".join(certifications),
            summary=summary
        )
    
    async def _call_llm(self, prompt: str):
        """Gọi LLM với prompt"""
        try:
            response = await self.llm.ainvoke(prompt)
            return response
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise

    async def match_jobs(self, filename: str) -> List[Dict[str, Any]]:
        """Match jobs based on CV analysis results"""
        logger.info(f"Starting job matching for filename: {filename}")
        
        try:
            # Lấy kết quả phân tích CV
            cv_result = await self.get_result_cv_extraction(filename)
            logger.info(f"CV extraction result type: {type(cv_result)}")
            logger.info(f"CV extraction result: {json.dumps(cv_result, indent=2, ensure_ascii=False, default=str)}")
            
            if not cv_result:
                logger.warning("No CV result found, returning empty suggestions")
                return []
            
            # Kiểm tra cấu trúc dữ liệu CV
            if isinstance(cv_result, dict):
                logger.info(f"CV result keys: {list(cv_result.keys())}")
                if 'skills' in cv_result:
                    logger.info(f"Skills found: {cv_result['skills']}")
                if 'experience' in cv_result:
                    logger.info(f"Experience found: {cv_result['experience']}")
                if 'education' in cv_result:
                    logger.info(f"Education found: {cv_result['education']}")
            elif isinstance(cv_result, list):
                logger.info(f"CV result is a list with {len(cv_result)} items")
                if cv_result:
                    logger.info(f"First item: {json.dumps(cv_result[0], indent=2, ensure_ascii=False, default=str)}")
            
            # Trích xuất thông tin từ CV
            skills = self._extract_skills(cv_result)
            experience = self._extract_experience(cv_result)
            education = self._extract_education(cv_result)
            projects = self._extract_projects(cv_result)
            certifications = self._extract_certifications(cv_result)
            summary = self._extract_summary(cv_result)
            
            logger.info(f"Extracted skills: {skills}")
            logger.info(f"Extracted experience: {experience}")
            logger.info(f"Extracted education: {education}")
            logger.info(f"Extracted projects: {projects}")
            logger.info(f"Extracted certifications: {certifications}")
            logger.info(f"Extracted summary: {summary[:200]}..." if summary else "No summary")
            
            # Tạo prompt cho LLM
            prompt = self._create_job_matching_prompt(skills, experience, education, projects, certifications, summary)
            logger.info(f"Created prompt: {prompt}")
            
            # Gọi LLM
            response = await self._call_llm(prompt)
            logger.info(f"LLM response type: {type(response)}")
            logger.info(f"LLM response content: {response.content}")
            
            # Parse JSON response
            try:
                # Thử parse trực tiếp
                result = json.loads(response.content)
                job_suggestions = result.get("job_suggestions", [])
                logger.info(f"Successfully parsed JSON directly, found {len(job_suggestions)} job suggestions")
                logger.info(f"Job suggestions: {json.dumps(job_suggestions, indent=2, ensure_ascii=False)}")
                return job_suggestions
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Raw LLM response: {response.content}")
                
                # Thử extract JSON từ markdown format
                try:
                    content = response.content
                    logger.info(f"Attempting to extract JSON from markdown, content length: {len(content)}")
                    
                    # Tìm JSON block trong markdown
                    if "```json" in content:
                        logger.info("Found ```json marker, extracting...")
                        start = content.find("```json") + 7
                        end = content.find("```", start)
                        if end != -1:
                            json_str = content[start:end].strip()
                            logger.info(f"Extracted JSON string: {json_str}")
                            result = json.loads(json_str)
                            job_suggestions = result.get("job_suggestions", [])
                            logger.info(f"Successfully extracted JSON from markdown, found {len(job_suggestions)} job suggestions")
                            logger.info(f"Job suggestions: {json.dumps(job_suggestions, indent=2, ensure_ascii=False)}")
                            return job_suggestions
                        else:
                            logger.error("Could not find closing ``` marker")
                    
                    # Thử tìm JSON object trong text
                    logger.info("Attempting regex extraction...")
                    import re
                    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                    json_matches = re.findall(json_pattern, content)
                    logger.info(f"Found {len(json_matches)} potential JSON matches with regex")
                    
                    for i, json_str in enumerate(json_matches):
                        try:
                            logger.info(f"Trying to parse regex match {i+1}: {json_str[:100]}...")
                            result = json.loads(json_str)
                            if "job_suggestions" in result:
                                job_suggestions = result.get("job_suggestions", [])
                                logger.info(f"Successfully extracted JSON using regex, found {len(job_suggestions)} job suggestions")
                                logger.info(f"Job suggestions: {json.dumps(job_suggestions, indent=2, ensure_ascii=False)}")
                                return job_suggestions
                        except Exception as regex_error:
                            logger.error(f"Failed to parse regex match {i+1}: {regex_error}")
                            continue
                            
                except Exception as extract_error:
                    logger.error(f"Failed to extract JSON from markdown: {extract_error}")
                
                # Fallback nếu LLM không trả về JSON hợp lệ
                logger.warning("Returning empty job suggestions due to JSON parsing failure")
                return []
                
        except Exception as e:
            logger.error(f"Error in match_jobs: {e}")
            return []

    async def match_courses(self, filename: str) -> List[Dict[str, Any]]:
        """Gợi ý khóa học phù hợp dựa trên CV"""
        logger.info(f"Starting course matching for filename: {filename}")
        
        try:
            # Lấy kết quả phân tích CV
            cv_result = await self.get_result_cv_extraction(filename)
            logger.info(f"CV extraction result type: {type(cv_result)}")
            logger.info(f"CV extraction result: {json.dumps(cv_result, indent=2, ensure_ascii=False, default=str)}")
            
            if not cv_result:
                logger.warning("No CV result found, returning empty course suggestions")
                return []
            
            # Trích xuất thông tin từ CV
            current_skills = self._extract_skills(cv_result)
            experience = self._extract_experience(cv_result)
            education = self._extract_education(cv_result)
            
            logger.info(f"Extracted current skills: {current_skills}")
            logger.info(f"Extracted experience: {experience}")
            logger.info(f"Extracted education: {education}")
            
            # Lấy thông tin từ jd_alignment để xác định kỹ năng còn thiếu
            jd_alignment = ""
            if isinstance(cv_result, dict):
                jd_alignment = cv_result.get("data", {}).get("jd_alignment", "")
            
            logger.info(f"JD alignment: {jd_alignment[:200]}..." if jd_alignment else "No JD alignment found")
            
            # Tạo prompt cho course matching
            prompt = COURSE_SUGGESTION_PROMPT.format(
                current_skills=", ".join(current_skills),
                missing_skills="",  # Sẽ được xác định từ jd_alignment
                career_goals="Phát triển kỹ năng và tìm việc làm phù hợp"
            )
            logger.info(f"Created course matching prompt: {prompt}")
            
            # Gọi LLM
            response = await self._call_llm(prompt)
            logger.info(f"LLM response type: {type(response)}")
            logger.info(f"LLM response content: {response.content}")
            
            # Parse JSON response
            try:
                # Thử parse trực tiếp
                result = json.loads(response.content)
                course_suggestions = result.get("course_suggestions", [])
                logger.info(f"Successfully parsed JSON directly, found {len(course_suggestions)} course suggestions")
                logger.info(f"Course suggestions: {json.dumps(course_suggestions, indent=2, ensure_ascii=False)}")
                return course_suggestions
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Raw LLM response: {response.content}")
                
                # Thử extract JSON từ markdown format
                try:
                    content = response.content
                    logger.info(f"Attempting to extract JSON from markdown, content length: {len(content)}")
                    
                    # Tìm JSON block trong markdown
                    if "```json" in content:
                        logger.info("Found ```json marker, extracting...")
                        start = content.find("```json") + 7
                        end = content.find("```", start)
                        if end != -1:
                            json_str = content[start:end].strip()
                            logger.info(f"Extracted JSON string: {json_str}")
                            result = json.loads(json_str)
                            course_suggestions = result.get("course_suggestions", [])
                            logger.info(f"Successfully extracted JSON from markdown, found {len(course_suggestions)} course suggestions")
                            logger.info(f"Course suggestions: {json.dumps(course_suggestions, indent=2, ensure_ascii=False)}")
                            return course_suggestions
                        else:
                            logger.error("Could not find closing ``` marker")
                    
                    # Thử tìm JSON object trong text
                    logger.info("Attempting regex extraction...")
                    import re
                    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                    json_matches = re.findall(json_pattern, content)
                    logger.info(f"Found {len(json_matches)} potential JSON matches with regex")
                    
                    for i, json_str in enumerate(json_matches):
                        try:
                            logger.info(f"Trying to parse regex match {i+1}: {json_str[:100]}...")
                            result = json.loads(json_str)
                            if "course_suggestions" in result:
                                course_suggestions = result.get("course_suggestions", [])
                                logger.info(f"Successfully extracted JSON using regex, found {len(course_suggestions)} course suggestions")
                                logger.info(f"Course suggestions: {json.dumps(course_suggestions, indent=2, ensure_ascii=False)}")
                                return course_suggestions
                        except Exception as regex_error:
                            logger.error(f"Failed to parse regex match {i+1}: {regex_error}")
                            continue
                            
                except Exception as extract_error:
                    logger.error(f"Failed to extract JSON from markdown: {extract_error}")
                
                # Fallback nếu LLM không trả về JSON hợp lệ
                logger.warning("Returning empty course suggestions due to JSON parsing failure")
                return []
                
        except Exception as e:
            logger.error(f"Error in match_courses: {e}")
            return []