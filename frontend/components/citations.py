import streamlit as st


def render_citations(citations: list[dict]):
    if not citations:
        return
    with st.expander(f"Sources ({len(citations)})", expanded=False):
        for i, c in enumerate(citations, start=1):
            score_pct = int(c.get("relevance_score", 0) * 100)
            st.markdown(
                f"**[{i}] {c['filename']}** — page {c['page']} "
                f"· chunk {c['chunk_index']} · relevance {score_pct}%"
            )
            st.caption(c.get("excerpt", ""))
            if i < len(citations):
                st.divider()
