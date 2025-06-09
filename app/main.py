# app/main.py
import os, sys

# Đưa thư mục project root và src vào path
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
srcdir = os.path.join(basedir, "src")
sys.path.insert(0, srcdir)
sys.path.insert(0, basedir)

import streamlit as st
from agents.master.core_graph import graph_router              # backend router
from configs.config_loader import AVAILABLE_AGENTS

# Thiết lập trang và giao diện
st.set_page_config(page_title="Multi-Agent Demo", layout="wide")

# CSS tuý chỉnh cho các thành phần
st.markdown("""
<style>
/* Button Ẩn/Hiện lịch sử */
.hide-btn {
    position: absolute;
    top: 10px;
    right: 10px;
}
/* Chat input bo góc */
div[data-testid="stChatInput"] {
    border-radius: 20px !important;
    width: 60% !important;
    margin: 0 auto !important;
}
/* Agent dropdown fixed */
.agent-dropdown {
    position: fixed !important;
    bottom: 20px !important;
    right: 20px !important;
    width: 180px !important;
}
</style>
""", unsafe_allow_html=True)

# Khởi tạo session_state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_history" not in st.session_state:
    st.session_state.show_history = True
if "agent_choice" not in st.session_state:
    st.session_state.agent_choice = "Auto"

# Hàm chuyển đổi ẩn/hiện lịch sử
def toggle_history():
    st.session_state.show_history = not st.session_state.show_history

async def main():
    # Sidebar hiển thị lịch sử chat
    with st.sidebar:
        if st.session_state.show_history:
            st.markdown("## Lịch sử chat")

    # Vùng chat chính
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            st.chat_message(msg['role']).markdown(msg['content'])

    # Ô nhập tin nhắn
    user_input = st.chat_input("Gửi tin nhắn…", key="chat_input")

    if user_input:
        # Lưu tin nhắn user
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Gọi graph router
        target = None if st.session_state.agent_choice == "Auto" else AVAILABLE_AGENTS[st.session_state.agent_choice]
        response = await graph_router(text=user_input, target_agent=target)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # Dropdown chọn Agent ở góc dưới bên phải
    with st.container():
        # chèn cái div mở
        st.markdown('<div class="agent-dropdown">', unsafe_allow_html=True)
        st.selectbox(
            "Chọn agent",
            ["Auto"] + list(AVAILABLE_AGENTS.keys()),
            key='agent_choice',
            label_visibility="collapsed"
        )
        # đóng div
        st.markdown('</div>', unsafe_allow_html=True)

        # CSS ở đầu file
        st.markdown("""
        <style>
        .agent-dropdown {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 180px;
        }
        </style>
        """, unsafe_allow_html=True)
        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())