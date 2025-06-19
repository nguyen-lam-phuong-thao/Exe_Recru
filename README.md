
# `cv_extraction` Module — Technical Documentation

Module `cv_extraction` chịu trách nhiệm **trích xuất thông tin từ CV** bằng AI, bao gồm:
- Phân tích nội dung CV dạng text hoặc file PDF
- Làm sạch, phân đoạn, nhận diện các section
- Trích xuất dữ liệu có cấu trúc (học vấn, kinh nghiệm, kỹ năng…)
- Suy luận đặc điểm người dùng (soft skills, vai trò phù hợp…)
- Chuyển đổi kết quả sang dạng API/DB để lưu trữ hoặc hiển thị

## Cấu trúc tổng thể thư mục

```
cv_extraction/
├── repositories/
│   ├── cv_repo.py
│   └── cv_agent/
│       ├── __init__.py
│       ├── ai_to_api_mapper.py
│       ├── agent_schema.py
│       ├── prompts.py
│       ├── llm_setup.py
│       └── cv_processor/
│           └── __init__.py
└── schemas/
    └── cv.py
```

## 1. `schemas/cv.py` — API & DB Schemas

Chứa các schema phục vụ việc gửi/nhận dữ liệu từ/to API hoặc DB:

- `ProcessCVRequest`: Input từ người dùng gồm `cv_file_url`.
- `CVBase`, `CVCreate`, `CVResponse`: Các schema mô tả dữ liệu CV chuẩn hóa dùng cho DB/API.
- Các sub-schema như `EducationEntry`, `ExperienceEntry`, `ProjectEntry`, v.v.

> **Lưu ý**: Đây là *chuẩn hóa cuối cùng*, khác với kết quả từ AI (AI output thường phức tạp và mô tả chi tiết hơn).

## 2. `repositories/cv_repo.py` — Entry Point chính

Chịu trách nhiệm:
- Tải file CV (PDF) từ `cv_file_url`
- Trích xuất text từ file (dùng `PDFToTextConverter`)
- Gọi `CVAnalyzer` để phân tích nội dung text
- Trả về `APIResponse` chứa text gốc + kết quả phân tích

Không thao tác DB, **chỉ xử lý nội dung và chuẩn hóa kết quả**.

## 3. `repositories/cv_agent/` — Lõi xử lý AI

### a. `agent_schema.py` — AI Output Schema
Định nghĩa kết quả đầu ra từ AI:
- `CVAnalysisResult`: Kết quả tổng hợp từ AI
- Các schema nhỏ như `PersonalInfoItem`, `ListEducationItem`, `ListWorkExperienceItem`, v.v.
- Thiết kế chi tiết, thân thiện với LLM, bao quát các dạng dữ liệu phong phú.

### b. `prompts.py` — Prompt templates
Lưu trữ tất cả các prompt sử dụng để giao tiếp với LLM:
- Làm sạch CV (`CV_CLEANING_PROMPT`)
- Nhận diện section (`SECTION_IDENTIFICATION_PROMPT`)
- Trích xuất chi tiết theo schema (`EXTRACT_SECTION_PROMPT_TEMPLATE`)
- Suy luận đặc điểm (`INFERENCE_PROMPT`), rút trích từ khóa (`EXTRACT_KEYWORDS_PROMPT`), tóm tắt CV (`CV_SUMMARY_PROMPT`)

> Dễ dàng nâng cấp, thay đổi prompt hoặc thêm version mới để A/B test.

### c. `llm_setup.py` — Cấu hình LLM
Khởi tạo đối tượng Gemini thông qua:
```python
ChatGoogleGenerativeAI(model='gemini-2.0-flash', api_key=GOOGLE_API_KEY, ...)
```
Dễ thay thế bằng OpenAI hoặc mô hình khác nếu cần.

### d. `cv_processor/__init__.py` — LangGraph Workflow
Là “engine” trung tâm điều khiển toàn bộ pipeline xử lý AI:
- Gồm các `node` đại diện cho từng bước:
  - `input_handler_node`, `cv_parser_node`, `section_identifier_node`
  - `llm_chunk_decision_node`, `information_extractor_node`, `characteristic_inference_node`
  - `output_aggregator_node`
- Sử dụng `LangGraph` để tạo graph pipeline, dễ mở rộng, thay đổi luồng xử lý
- Theo dõi token, chi phí sử dụng LLM

Trả về `CVAnalysisResult` (hoặc error nếu thất bại).

## 4. `cv_agent/__init__.py` — CVAnalyzer

Là lớp wrapper để xử lý:
- Nhận nội dung text CV
- Khởi tạo `CVProcessorWorkflow`
- Trả về `CVAnalysisResult` hoặc thông báo lỗi

Được gọi trong `cv_repo.py`.

## 5. `ai_to_api_mapper.py` — Chuyển đổi kết quả AI → API Schema

Cầu nối giữa `CVAnalysisResult` (AI output) và `CVBase`/`CVResponse` (API schema):
- Mapping tên field: `personal_information.full_name` → `name`
- Flatten danh sách: `ListEducationItem.items` → `education: List[EducationEntry]`
- Chuyển đổi kiểu dữ liệu: `str → datetime`, `list → str`, v.v.

Dễ mở rộng nếu schema thay đổi.

## Luồng xử lý tổng thể

```
[API Request]
    ↓
[cv_repo.py]
    ↓
Tải file từ URL → Đọc nội dung
    ↓
[CVAnalyzer]
    ↓
[CVProcessorWorkflow]
    ↓
[LLM → Prompt → Structured Output]
    ↓
Tổng hợp: Text gốc + kết quả trích xuất + inference
    ↓
Trả về APIResponse
```

Nếu cần lưu vào DB:
```
CVAnalysisResult → (qua ai_to_cvbase) → CVCreate → DAL.save()
```


## Gợi ý mở rộng

| Mục tiêu | Gợi ý |
|---------|-------|
| Thêm LLM khác | Viết `llm_setup_openai.py` và thêm config chuyển đổi |
| Lưu kết quả CV vào DB | Dùng `ai_to_cvbase()` → gọi DAL trong repo |
| Gợi ý việc làm phù hợp | Thêm node `job_recommendation_node` vào workflow |
| Tăng tốc xử lý | Parallel hóa trích xuất từng section |
| Multi-language CVs | Thêm LLM translation trước khi phân tích |

## Tổng kết

`cv_extraction` là module phức tạp và mạnh mẽ, kết hợp:
- Xử lý file
- Phân tích ngôn ngữ tự nhiên (NLP)
- AI workflow engine
- Chuẩn hóa schema và cấu trúc hóa dữ liệu


