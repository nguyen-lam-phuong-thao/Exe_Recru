"""
Prompts cho Job Matching Module
"""

from typing import Dict, Any

class JobMatchingPrompts:
    """Class chứa tất cả prompts cho job matching"""
    
    @staticmethod
    def create_job_matching_prompt(cv_data: Dict[str, Any], jd_alignment: str) -> str:
        """
        Tạo prompt cho job matching dựa trên CV data và JD alignment
        
        Args:
            cv_data: Dữ liệu CV đã được phân tích
            jd_alignment: JD alignment từ cv_extraction
            
        Returns:
            Prompt string để gửi cho LLM
        """
        # Format CV data ngắn gọn
        cv_formatted = JobMatchingPrompts._format_cv_analysis_simple(cv_data)
        
        # Kiểm tra xem có CV data thực sự không
        has_cv_data = cv_data and any([
            cv_data.get('name') and cv_data.get('name') != 'Ứng viên',
            cv_data.get('skills'),
            cv_data.get('experience'),
            cv_data.get('education')
        ])
        
        if has_cv_data:
            return JobMatchingPrompts._create_full_analysis_prompt(cv_formatted, jd_alignment)
        else:
            return JobMatchingPrompts._create_jd_only_prompt(jd_alignment)
    
    @staticmethod
    def _create_full_analysis_prompt(cv_formatted: str, jd_alignment: str) -> str:
        """Tạo prompt cho phân tích đầy đủ với CV data"""
        return f"""Phân tích CV của ứng viên và JD để gợi ý nghề nghiệp phù hợp với trình độ.

CV: {cv_formatted}
JD: {jd_alignment}

Trả về JSON:
{{
    "missing_skills": ["skill1", "skill2"],
    "suggested_courses": [
        {{
            "course_name": "tên khóa học",
            "platform": "nền tảng",
            "description": "mô tả ngắn",
            "estimated_duration": "thời gian",
            "url": "link khóa học"
        }}
    ],
    "suggested_jobs": [
        {{
            "job_title": "tên vị trí",
            "company_name": "tên công ty cụ thể",
            "required_skills": ["skill1", "skill2"],
            "salary_range": "mức lương",
            "description": "mô tả công việc cụ thể",
            "url": "link bài đăng tuyển dụng"
        }}
    ],
    "career_path_analysis": {{
        "career_path": "lộ trình nghề nghiệp",
        "short_term_goals": ["mục tiêu ngắn hạn"],
        "long_term_goals": ["mục tiêu dài hạn"],
        "priority_skills": ["kỹ năng ưu tiên"],
        "estimated_timeline": "thời gian dự kiến"
    }}
}}

Chỉ trả về JSON, không có text khác."""
    
    @staticmethod
    def _create_jd_only_prompt(jd_alignment: str) -> str:
        """Tạo prompt chỉ dựa trên JD khi không có CV data"""
        return f"""Dựa trên JD để gợi ý 3 nghề nghiệp  ở các công ty Việt Nam và 3 khóa học phù hợp để cải thiện các kĩ năng còn thiếu.

JD_alignment: {jd_alignment}

QUAN TRỌNG: Ngay cả khi không có thông tin CV cụ thể, hãy đưa ra gợi ý dựa trên yêu cầu của JD_alignment. Không trả về mảng rỗng.

Trả về theo format JSON:
{{
    "missing_skills": ["kỹ năng cần thiết cho vị trí này", "kỹ năng phổ biến trong ngành"],
    "suggested_courses": [
        {{
            "course_name": "tên khóa học cụ thể",
            "platform": "nền tảng (Coursera, Udemy, edX, etc.)",
            "description": "mô tả ngắn về khóa học",
            "estimated_duration": "thời gian (ví dụ: 4 tuần, 8 tuần)",
            "url": "Tìm kiếm trên các nền tảng cụ thể (Coursera, Udemy, edX, etc.) để đưa link khóa học "
        }},
        {{
            "course_name": "khóa học thứ 2",
            "platform": "nền tảng",
            "description": "mô tả ngắn",
            "estimated_duration": "thời gian",
            "url": "Tìm kiếm trên các nền tảng cụ thể (Coursera, Udemy, edX, etc.) để đưa link khóa học "
        }}
    ],
    "suggested_jobs": [
        {{
            "job_title": "tên vị trí cụ thể trên trang tuyển dụng",
            "company_name": "tên công ty cụ thể ở Vietnam ",
            "required_skills": ["skill1", "skill2", "skill3"],
            "salary_range": "mức lương (ví dụ: 15-25 triệu VND)",
            "description": "mô tả công việc cụ thể",
            "url": "Tìm kiếm trong các trang web tuyển dụng của (VietnamWorks, TopCv, Linkedin, etc.) để đưa ra bài đăng tuyển dụng còn thời hạn ứng tuyển của công ty cho vị trí đó"
        }},
        {{
            "job_title": "vị trí thứ 2",
            "company_name": "tên công ty khác",
            "required_skills": ["skill1", "skill2"],
            "salary_range": "mức lương",
            "description": "mô tả công việc",
            "url": "Tìm kiếm trong các trang web tuyển dụng của (VietnamWorks, TopCv, Linkedin, etc.) để đưa ra bài đăng tuyển dụng còn thời hạn ứng tuyển của công ty cho vị trí đó"
        }}
    ],
    "career_path_analysis": {{
        "career_path": "lộ trình nghề nghiệp cụ thể cho các vị trí khác nhau đã được gợi ý",
        "short_term_goals": ["mục tiêu ngắn hạn 1", "mục tiêu ngắn hạn 2"],
        "long_term_goals": ["mục tiêu dài hạn 1", "mục tiêu dài hạn 2"],
        "priority_skills": ["kỹ năng ưu tiên 1", "kỹ năng ưu tiên 2"],
        "estimated_timeline": "thời gian dự kiến (ví dụ: 6-12 tháng)"
    }}
}}

LƯU Ý: 
- Luôn đưa ra ít nhất 3 khóa học và 3 công việc
- Đưa ra kỹ năng cụ thể, không để mảng rỗng
- Tập trung vào thị trường Vietnam
- Mô tả chi tiết và thực tế
- Các đường link url phải là link thực tế và không phải là Not Found hoặc 404
"""
    
    @staticmethod
    def _format_cv_analysis_simple(cv_analysis: Dict[str, Any]) -> str:
        """Format CV analysis đơn giản và ngắn gọn"""
        try:
            if not cv_analysis:
                return "Không có thông tin CV"
            
            # Lấy thông tin cơ bản
            name = cv_analysis.get('name', 'N/A')
            summary = cv_analysis.get('summary', 'N/A')
            skills = ', '.join(cv_analysis.get('skills', []))
            
            # Kinh nghiệm ngắn gọn
            experience = cv_analysis.get('experience', [])
            exp_summary = ""
            if experience:
                exp_summary = f"{len(experience)} vị trí: " + ", ".join([
                    f"{exp.get('title', 'N/A')} tại {exp.get('company', 'N/A')}"
                    for exp in experience[:3]  # Chỉ lấy 3 vị trí gần nhất
                ])
            else:
                exp_summary = "Không có kinh nghiệm"
            
            # Học vấn ngắn gọn
            education = cv_analysis.get('education', [])
            edu_summary = ""
            if education:
                edu_summary = ", ".join([
                    f"{edu.get('degree', 'N/A')} tại {edu.get('institution', 'N/A')}"
                    for edu in education[:2]  # Chỉ lấy 2 bằng cấp cao nhất
                ])
            else:
                edu_summary = "Không có thông tin học vấn"
            
            # Format ngắn gọn
            formatted = f"Tên: {name}. Tóm tắt: {summary}. Kỹ năng: {skills}. Kinh nghiệm: {exp_summary}. Học vấn: {edu_summary}."
            
            return formatted.strip()
            
        except Exception as e:
            return "Lỗi format CV analysis" 