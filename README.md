# 💼 Multi‑Agent Project Automation System

> **Tự động hoá vòng đời tác vụ trong dự án IT** bằng LangGraph, Streamlit và các MCP (Model Context Protocol) Server.  
> • Gán & theo dõi task • Phát triển • Kiểm thử • Sinh tài liệu • Báo cáo cuối ngày  
> → tất cả được điều phối bởi các *agent* phân tầng thông minh.

---

## 📐 Kiến trúc tổng quan
```
Streamlit UI ─► Router ─► LangGraph ─► Agents
                                    │ ├─ Host (Q&A chung)
                                    │ ├─ PM (Progress Manager)
                                    │ ├─ QA (Tester & Unit test)
                                    │ ├─ Dev (Copilot IDE)
                                    │ └─ Jira / Confluence (Task & Docs)
                                    └─ MCP Tools (GitHub, Qodo Cover, …)
```

- **UI (app/)**: Giao diện chọn agent tương tác hoặc chế độ tự động.
- **LangGraph**: Điều phối agent theo đồ thị phân tầng.
- **MCP Server**: Lớp trung gian kết nối Jira, GitHub, Qodo, đảm bảo tách biệt agent ↔ API.

---

## 🗂️ Cấu trúc thư mục

```
project/
├── app/ # Streamlit UI
├── data/ # Sample data, file test
├── docker/ # Cấu hình MCP (github, jira, qodo)
├── report/ # Báo cáo LaTeX + hình ảnh kiến trúc
├── src/
│ ├── agents/ # Các agent (QA, PM, Dev, Host, ...)
│ ├── configs/ # config loader, base.yml
│ ├── services/ # MCP client, task manager, test_tool
│ └── utils/ # script phụ trợ
├── tests/ # Unit tests
├── pyproject.toml # Poetry hoặc setuptools config
├── requirements.txt
└── README.md # (file này)
```

---

## 🚀 Cài đặt nhanh

```bash
# 1. Clone repository
git clone https://github.com/<your-username>/multi_agent.git
cd multi_agent

# 2. Tạo môi trường ảo
python -m venv .venv
source .venv/bin/activate

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Tạo file môi trường
cp docker/mcp-atlassian.env.example docker/mcp-atlassian.env

---

## 🐳 Khởi chạy MCP Servers

```bash
# MCP GitHub Server (nếu dùng GitHub Copilot nội bộ)
docker compose -f docker/github_mcp.yml up -d

# MCP Atlassian (Jira & Confluence)
docker run -d --env-file docker/mcp-atlassian.env -p 8405:80 mcp/atlassian:latest
```

Mỗi server expose endpoint `/mcp` để client trong `services/` tự động lấy *tools*.

---

## 🏃‍♂️ Chạy ứng dụng

```bash
# Trong virtualenv đã kích hoạt
$ streamlit run app/main.py
```

Mở http://localhost:8501 để truy cập giao diện.
• Chọn Auto Mode để hệ thống tự điều phối agent phù hợp.
• Hoặc chọn PM / QA / Dev để điều khiển thủ công

---

## 🧪 Test & CI

```bash
# Unit + integration tests
$ pytest -q tests/
```

• *Chưa* cấu hình CI – bạn có thể thêm GitHub Actions tuỳ ý.

---

## 🔧 Tuỳ chỉnh & mở rộng

| Bạn muốn…       | Cách thực hiện                                         |
| --------------- | ------------------------------------------------------ |
| Thêm Agent mới  | Tạo folder trong `src/agents/`, gán node vào LangGraph |
| Dùng LLM khác   | Chỉnh `configs/base.yml` và `config_loader.py`         |
| Kết nối DB thật | Sửa `task_manager.py` → tích hợp PostgreSQL / MongoDB  |
| Mở rộng công cụ | Viết tool mới & đăng ký qua `MCP Server`               |
| Gắn thêm alert  | Dùng `task_manager.py` + webhook đến Slack / Email     |
