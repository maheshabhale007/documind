import streamlit as st

from components.sidebar import render_sidebar
from components.chat import render_chat

st.set_page_config(
    page_title="DocuMind",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "documents" not in st.session_state:
    st.session_state["documents"] = []
if "docs_dirty" not in st.session_state:
    st.session_state["docs_dirty"] = True
if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = "llama3.2:3b"

render_sidebar()
render_chat()
