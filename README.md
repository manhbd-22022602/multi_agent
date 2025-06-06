```
project/
├── app/                          # App chính (nơi chạy Streamlit UI)
│   ├── __init__.py
│   ├── main.py                   # File chạy Streamlit (streamlit run app/main.py)
│   └── pages/                    # Nếu dùng nhiều page trong Streamlit
│       └── dashboard.py
│
├── agents/                       # Định nghĩa các Agent dùng trong LangGraph
│   ├── __init__.py
│   ├── host.py            # Auto-mode, Q&A chung
│   ├── project_manager.py # Supervisor (PM)
│   ├── developer.py       # Dev-Agent
│   ├── qa.py              # QA-Agent
│   ├── docu.py            # Doc-Agent
│   └── report.py          # Báo cáo cuối ngày
│
├── graph/                        # Logic xây dựng và compile LangGraph
│   ├── __init__.py
│   ├── nodes.py                  # Các node function
│   ├── edges.py                  # Nếu tách riêng edge logic
│   ├── state.py                  # Định nghĩa State (TypedDict hoặc BaseModel)
│   └── build_graph.py            # Tạo và compile graph
│
├── data/                         # Data mẫu, cấu hình, mô phỏng DB
│   └── sample_tasks.json
│
├── services/                     # Các dịch vụ phụ trợ (DB, API, xử lý I/O...)
│   ├── __init__.py
│   └── task_manager.py
│
├── utils/                        # Tiện ích chung (formatting, validation, logs,...)
│   ├── __init__.py
│   └── helpers.py
│
├── configs/                      # Cấu hình hệ thống (API key, env, graph setup,...)
│   └── settings.py
│
├── tests/                        # Unit test, integration test
│   └── test_graph.py
│
├── requirements.txt              # Thư viện cần cài
├── README.md                     # Tài liệu mô tả dự án
└── .env                          # Biến môi trường (nếu cần)
```