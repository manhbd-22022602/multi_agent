# app/main.py
import streamlit as st
from agents.graph.core_graph import graph_router              # backend router
from configs.settings import AVAILABLE_AGENTS

st.set_page_config(page_title="Multi-Agent Demo", layout="wide")

agent_choice = st.sidebar.selectbox(
    "Choose chat mode", ["Auto"] + list(AVAILABLE_AGENTS.keys())
)

user_input = st.chat_input("Send a message…")

# History container
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    st.chat_message(m["role"]).markdown(m["content"])

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ↓↓↓ call router (async safe) ↓↓↓
    response = graph_router(
        text=user_input,
        target_agent=None if agent_choice == "Auto" else AVAILABLE_AGENTS[agent_choice],
    )

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.experimental_rerun()
