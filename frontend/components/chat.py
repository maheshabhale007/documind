import json
import os

import requests
import streamlit as st

from components.citations import render_citations

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def render_chat():
    st.header("Ask your documents")

    # Display chat history
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("citations"):
                render_citations(message["citations"])

    # Chat input
    if prompt := st.chat_input("Ask anything about your documents..."):
        # Show user message
        st.session_state.setdefault("messages", []).append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        model = st.session_state.get("selected_model", "llama3.2:3b")

        # Stream assistant response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            accumulated = ""
            citations = []

            try:
                with requests.post(
                    f"{BACKEND_URL}/api/v1/query/stream",
                    json={"query": prompt, "top_k": 5, "model": model},
                    stream=True,
                    timeout=120,
                ) as resp:
                    for raw_line in resp.iter_lines():
                        if not raw_line:
                            continue
                        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                        if line == "data: [DONE]":
                            break
                        if line.startswith("data: "):
                            try:
                                event = json.loads(line[6:])
                            except json.JSONDecodeError:
                                continue

                            if event["type"] == "token":
                                accumulated += event["content"]
                                placeholder.markdown(accumulated + "▌")
                            elif event["type"] == "citations":
                                citations = event["data"]
                            elif event["type"] == "error":
                                accumulated = f"Error: {event.get('message', 'Unknown error')}"

            except Exception as e:
                accumulated = f"Could not reach backend: {e}"

            placeholder.markdown(accumulated)
            if citations:
                render_citations(citations)

        st.session_state["messages"].append(
            {"role": "assistant", "content": accumulated, "citations": citations}
        )

    # Clear button
    if st.session_state.get("messages"):
        if st.button("Clear conversation"):
            st.session_state["messages"] = []
            st.rerun()
