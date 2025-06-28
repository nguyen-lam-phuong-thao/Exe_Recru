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
   - Địa điểm
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

**QUAN TRỌNG: Chỉ trả về JSON thuần túy, không có markdown formatting, không có text giải thích.**

**Định dạng trả về (chỉ JSON):**
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