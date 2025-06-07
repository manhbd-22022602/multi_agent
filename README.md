# 💼 Multi‑Agent Project Automation System

> **Tự động hoá vòng đời tác vụ trong dự án IT** bằng LangGraph, Streamlit và các MCP (Model Context Protocol) Server.
>
> • Gán & theo dõi task • Phát triển • Kiểm thử • Sinh tài liệu • Báo cáo cuối ngày  — tất cả do các *agent* đảm nhận.

---

## 📐 Kiến trúc tổng quan

```
Streamlit UI  ─►  Router  ─►  LangGraph  ─►  Agents
                              │              ├─ Host (Q&A chung)
                              │              ├─ PM (Supervisor)
                              │              ├─ Dev (Implementation)
                              │              ├─ QA (Testing)
                              │              ├─ Doc (Documentation)
                              │              └─ Report (Daily report)
                              └─  MCP Tools (GitHub, Jira, …)
```

* **UI (app/)**: Dropdown cho phép chọn chế độ *Auto* hoặc từng agent.
* **LangGraph (agents/** & **graph/)**: Xây đồ thị trạng thái, điều phối luồng công việc.
* **MCP Servers (services/** & **docker/)**: Kết nối GitHub / Atlassian qua chuẩn MCP để gọi API an toàn.

---

## 🗂️ Cấu trúc thư mục

```
project/
├── app/               # Streamlit UI
├── agents/            # Mỗi agent nằm trong sub‑package riêng
│   ├── Dev/
│   ├── Doc/
│   ├── Host/
│   ├── PM/
│   ├── QA/
│   └── Report/
├── graph/             # Node, Edge, State, build_graph.py
├── services/          # Kết nối MCP & logic phụ trợ
│   ├── github_mcp.py
│   ├── atlassian_mcp.py
│   └── task_manager.py
├── configs/           # settings.py, load .env
├── data/              # sample_tasks.json, mock DB
├── docker/            # docker-compose & YAML cho MCP servers
├── tests/             # PyTest suites
├── requirements.txt
├── README.md          # (file này)
└── .env               # Biến môi trường
```

## 🚀 Cài đặt nhanh

```bash
# 1) Clone repo
$ git clone https://github.com/<you>/multi_agent.git && cd multi_agent

# 2) Tạo virtualenv & cài phụ thuộc
$ python -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt  # hoặc poetry install

# 3) Tạo file .env
$ cp .env.example .env  # rồi điền API keys
```

---

## 🐳 Khởi chạy MCP Servers

```bash
# GitHub MCP (stdio mode)
$ docker compose -f docker/github_mcp.yml up -d

# Atlassian MCP (Jira / Confluence)
$ docker run -d --env-file mcp-atlassian.env -p 8405:80 mcp/atlassian:latest
```

Mỗi server expose endpoint `/mcp` để client trong `services/` tự động lấy *tools*.

---

## 🏃‍♂️ Chạy ứng dụng

```bash
# Trong virtualenv đã kích hoạt
$ streamlit run app/main.py
```

Truy cập `http://localhost:8501` ➜ chọn **Auto** để để hệ thống tự phối hợp tất cả agents, hoặc chọn cụ thể **PM / Dev / QA …** tuỳ ngữ cảnh.

---

## 🧪 Test & CI

```bash
# Unit + integration tests
$ pytest -q tests/
```

• *Chưa* cấu hình CI – bạn có thể thêm GitHub Actions tuỳ ý.

---

## 🔧 Tuỳ chỉnh & mở rộng

* **Thêm Agent mới**: tạo sub‑folder trong `agents/`, implement logic & đăng ký node vào `graph/build_graph.py`.
* **Thay LLM**: chỉnh `configs/settings.py` – hỗ trợ OpenAI, Gemma, v.v.
* **DB thực**: thay mock JSON bằng PostgreSQL / MongoDB qua `services/task_manager.py`.

