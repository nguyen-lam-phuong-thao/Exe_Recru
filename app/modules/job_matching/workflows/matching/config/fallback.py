"""
Fallback data cho Job Matching Module
"""

from typing import Dict, Any, List

class JobMatchingFallback:
    """Class chứa tất cả fallback data cho job matching"""
    
    @staticmethod
    def get_fallback_response(context: str = "general") -> Dict[str, Any]:
        """
        Lấy fallback response dựa trên context
        
        Args:
            context: Context của fallback (general, courses, jobs, career_path, etc.)
            
        Returns:
            Dict chứa fallback data
        """
        if context == "courses" or "khóa học" in context.lower():
            return JobMatchingFallback._get_courses_fallback()
        elif context == "jobs" or "công việc" in context.lower():
            return JobMatchingFallback._get_jobs_fallback()
        elif context == "career_path" or "lộ trình" in context.lower():
            return JobMatchingFallback._get_career_path_fallback()
        elif context == "missing_skills" or "kỹ năng" in context.lower():
            return JobMatchingFallback._get_missing_skills_fallback()
        else:
            return JobMatchingFallback._get_general_fallback()
    
    @staticmethod
    def _get_general_fallback() -> Dict[str, Any]:
        """Fallback chung cho tất cả trường hợp"""
        return {
            "missing_skills": ["Kỹ năng giao tiếp", "Quản lý thời gian"],
            "suggested_courses": [
                {
                    "course_name": "Kỹ năng mềm cơ bản",
                    "platform": "Coursera",
                    "description": "Phát triển kỹ năng giao tiếp và làm việc nhóm",
                    "estimated_duration": "4 tuần",
                    "url": "https://coursera.org/soft-skills"
                }
            ],
            "suggested_jobs": [
                {
                    "job_title": "Nhân viên văn phòng",
                    "company_name": "Công ty đa ngành",
                    "required_skills": ["Excel", "Word", "Giao tiếp"],
                    "salary_range": "8-15 triệu VND",
                    "description": "Hỗ trợ công việc văn phòng cơ bản",
                    "url": "https://jobsite.vn/job/van-phong-123"
                }
            ],
            "career_path_analysis": {
                "career_path": "Phát triển nghề nghiệp tổng quát",
                "short_term_goals": ["Học kỹ năng cơ bản", "Tìm hiểu thị trường"],
                "long_term_goals": ["Xác định hướng đi rõ ràng", "Phát triển chuyên môn"],
                "priority_skills": ["Giao tiếp", "Học hỏi", "Thích ứng"],
                "estimated_timeline": "6-12 tháng"
            }
        }
    
    @staticmethod
    def _get_missing_skills_fallback() -> List[str]:
        """Fallback cho missing skills"""
        return ["Kỹ năng giao tiếp", "Quản lý thời gian", "Làm việc nhóm"]
    
    @staticmethod
    def _get_courses_fallback() -> List[Dict[str, str]]:
        """Fallback cho suggested courses"""
        return [
            {
                "course_name": "Kỹ năng mềm cơ bản",
                "platform": "Coursera",
                "description": "Phát triển kỹ năng giao tiếp và làm việc nhóm",
                "estimated_duration": "4 tuần",
                "url": "https://coursera.org/soft-skills"
            },
            {
                "course_name": "Quản lý thời gian hiệu quả",
                "platform": "Udemy",
                "description": "Học cách quản lý thời gian và tăng năng suất",
                "estimated_duration": "3 tuần",
                "url": "https://udemy.com/time-management"
            }
        ]
    
    @staticmethod
    def _get_jobs_fallback() -> List[Dict[str, Any]]:
        """Fallback cho suggested jobs"""
        return [
            {
                "job_title": "Nhân viên văn phòng",
                "company_name": "Công ty đa ngành",
                "required_skills": ["Excel", "Word", "Giao tiếp"],
                "salary_range": "8-15 triệu VND",
                "description": "Hỗ trợ công việc văn phòng cơ bản",
                "url": "https://jobsite.vn/job/van-phong-123"
            },
            {
                "job_title": "Trợ lý hành chính",
                "company_name": "Công ty vừa và nhỏ",
                "required_skills": ["Word", "Excel", "Quản lý thời gian"],
                "salary_range": "6-12 triệu VND",
                "description": "Hỗ trợ công việc hành chính và văn phòng",
                "url": "https://jobsite.vn/job/tro-ly-456"
            }
        ]
    
    @staticmethod
    def _get_career_path_fallback() -> Dict[str, Any]:
        """Fallback cho career path analysis"""
        return {
            "career_path": "Phát triển nghề nghiệp tổng quát",
            "short_term_goals": ["Học kỹ năng cơ bản", "Tìm hiểu thị trường"],
            "long_term_goals": ["Xác định hướng đi rõ ràng", "Phát triển chuyên môn"],
            "priority_skills": ["Giao tiếp", "Học hỏi", "Thích ứng"],
            "estimated_timeline": "6-12 tháng"
        }
    
    @staticmethod
    def get_data_science_fallback() -> Dict[str, Any]:
        """Fallback đặc biệt cho Data Science"""
        return {
            "missing_skills": ["Machine Learning", "Deep Learning", "Apache Spark", "AWS"],
            "suggested_courses": [
                {
                    "course_name": "Machine Learning for Beginners",
                    "platform": "Coursera",
                    "description": "Khóa học ML cơ bản cho người mới bắt đầu",
                    "estimated_duration": "8 tuần",
                    "url": "https://coursera.org/ml-beginners"
                },
                {
                    "course_name": "Deep Learning Specialization",
                    "platform": "Coursera",
                    "description": "Chuyên sâu về Deep Learning",
                    "estimated_duration": "12 tuần",
                    "url": "https://coursera.org/deep-learning"
                }
            ],
            "suggested_jobs": [
                {
                    "job_title": "Senior Data Analyst",
                    "company_name": "Tech Company",
                    "required_skills": ["SQL", "Python", "PowerBI"],
                    "salary_range": "20-35 triệu VND",
                    "description": "Phân tích dữ liệu nâng cao và tạo báo cáo",
                    "url": "https://jobsite.vn/job/data-analyst-789"
                },
                {
                    "job_title": "Data Scientist",
                    "company_name": "AI Startup",
                    "required_skills": ["Python", "Machine Learning", "SQL"],
                    "salary_range": "30-50 triệu VND",
                    "description": "Phát triển mô hình ML và phân tích dữ liệu",
                    "url": "https://jobsite.vn/job/data-scientist-101"
                }
            ],
            "career_path_analysis": {
                "career_path": "Data Science",
                "short_term_goals": ["Học Machine Learning cơ bản", "Làm quen với AWS"],
                "long_term_goals": ["Trở thành Senior Data Scientist"],
                "priority_skills": ["Machine Learning", "Deep Learning", "AWS"],
                "estimated_timeline": "12-18 tháng"
            }
        }
    
    @staticmethod
    def get_software_development_fallback() -> Dict[str, Any]:
        """Fallback đặc biệt cho Software Development"""
        return {
            "missing_skills": ["React", "Node.js", "Docker", "AWS"],
            "suggested_courses": [
                {
                    "course_name": "React for Beginners",
                    "platform": "Udemy",
                    "description": "Học React từ cơ bản đến nâng cao",
                    "estimated_duration": "10 tuần",
                    "url": "https://udemy.com/react-for-beginners"
                },
                {
                    "course_name": "Node.js Backend Development",
                    "platform": "Coursera",
                    "description": "Phát triển backend với Node.js",
                    "estimated_duration": "8 tuần",
                    "url": "https://coursera.org/nodejs-backend"
                }
            ],
            "suggested_jobs": [
                {
                    "job_title": "Frontend Developer",
                    "company_name": "Tech Startup",
                    "required_skills": ["JavaScript", "React", "HTML/CSS"],
                    "salary_range": "15-25 triệu VND",
                    "description": "Phát triển giao diện người dùng",
                    "url": "https://jobsite.vn/job/frontend-202"
                },
                {
                    "job_title": "Full Stack Developer",
                    "company_name": "Software Company",
                    "required_skills": ["JavaScript", "Node.js", "React", "SQL"],
                    "salary_range": "20-35 triệu VND",
                    "description": "Phát triển cả frontend và backend",
                    "url": "https://jobsite.vn/job/fullstack-303"
                }
            ],
            "career_path_analysis": {
                "career_path": "Software Development",
                "short_term_goals": ["Học React", "Làm quen với Node.js"],
                "long_term_goals": ["Trở thành Senior Full Stack Developer"],
                "priority_skills": ["React", "Node.js", "Docker"],
                "estimated_timeline": "12-18 tháng"
            }
        } 