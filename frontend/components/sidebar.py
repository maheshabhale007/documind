import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def render_sidebar():
    with st.sidebar:
        st.title("DocuMind")
        st.caption("Local AI · No API Keys · Your Data Stays Here")
        st.divider()

        # Model selector
        st.subheader("Model")
        model = st.selectbox(
            "LLM",
            options=["llama3.2:3b", "mistral:7b"],
            index=0,
            help="llama3.2:3b is faster on CPU. mistral:7b is higher quality.",
        )
        st.session_state["selected_model"] = model

        st.divider()

        # File upload
        st.subheader("Upload Document")
        uploaded = st.file_uploader(
            "PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=False,
        )
        if uploaded is not None:
            with st.spinner(f"Ingesting {uploaded.name}..."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/api/v1/documents/upload",
                        files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                        timeout=120,
                    )
                    if resp.status_code == 201:
                        meta = resp.json()
                        st.success(
                            f"Ingested **{meta['filename']}** — {meta['total_chunks']} chunks"
                        )
                        st.session_state["docs_dirty"] = True
                    else:
                        st.error(f"Upload failed: {resp.json().get('detail', resp.text)}")
                except Exception as e:
                    st.error(f"Could not reach backend: {e}")

        st.divider()

        # Document list
        st.subheader("Ingested Documents")
        if st.button("Refresh list"):
            st.session_state["docs_dirty"] = True

        if st.session_state.get("docs_dirty", True):
            try:
                resp = requests.get(f"{BACKEND_URL}/api/v1/documents/", timeout=10)
                st.session_state["documents"] = resp.json() if resp.ok else []
            except Exception:
                st.session_state["documents"] = []
            st.session_state["docs_dirty"] = False

        docs = st.session_state.get("documents", [])
        if not docs:
            st.info("No documents yet. Upload one above.")
        else:
            for doc in docs:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{doc['filename']}**  \n`{doc['total_chunks']} chunks`")
                with col2:
                    if st.button("🗑", key=f"del_{doc['document_id']}"):
                        try:
                            requests.delete(
                                f"{BACKEND_URL}/api/v1/documents/{doc['document_id']}",
                                timeout=10,
                            )
                            st.session_state["docs_dirty"] = True
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
