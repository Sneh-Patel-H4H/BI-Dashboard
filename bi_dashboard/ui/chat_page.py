from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from ai.qa_pipeline import answer_question


def render() -> None:
    st.title("Ask Your Data")
    st.markdown(
        "Ask any business question in plain English. "
        "I'll respond with charts, tables, or insights automatically."
    )

    df: Optional[pd.DataFrame] = st.session_state.get("raw_df")
    schema: Optional[Dict[str, Any]] = st.session_state.get("schema")

    if df is None or schema is None:
        st.info("No data loaded yet. Head to **Upload Data** to get started.")
        return

    # ---- Process any pending question (set by input or follow-up buttons) -----
    pending = st.session_state.pop("pending_question", None)
    if pending:
        _process_question(pending, df, schema)

    # ---- Render chat history --------------------------------------------------
    history = st.session_state.get("chat_history", [])
    for idx, msg in enumerate(history):
        with st.chat_message(msg["role"]):
            if msg.get("content"):
                st.markdown(msg["content"])

            if msg.get("fig") is not None:
                st.plotly_chart(msg["fig"], use_container_width=True)
                st.caption("Chart")

            if msg.get("result_df") is not None:
                st.dataframe(msg["result_df"], use_container_width=True)
                st.caption("Table")

            # Follow-up suggestion buttons — only on the last assistant message
            if (
                msg["role"] == "assistant"
                and idx == len(history) - 1
                and msg.get("follow_up_suggestions")
            ):
                st.markdown("**You might also ask:**")
                suggestions = msg["follow_up_suggestions"][:2]
                btn_cols = st.columns(len(suggestions))
                for i, suggestion in enumerate(suggestions):
                    with btn_cols[i]:
                        if st.button(
                            f"💬 {suggestion}",
                            key=f"followup_{idx}_{i}",
                            use_container_width=True,
                        ):
                            st.session_state.pending_question = suggestion
                            st.rerun()

    # ---- Chat input ----------------------------------------------------------
    if prompt := st.chat_input("Ask a question about your data…"):
        st.session_state.pending_question = prompt
        st.rerun()


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _process_question(
    question: str,
    df: pd.DataFrame,
    schema: Dict[str, Any],
) -> None:
    """Call the Q&A pipeline, render the response, and persist to history."""
    # Add user message
    _append_history({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            response = answer_question(question, df, schema)

        insight = response.get("insight_text", "")
        fig = response.get("fig")
        result_df = response.get("result_df")
        suggestions = response.get("follow_up_suggestions", [])[:2]
        response_type = response.get("response_type", "narrative")

        if insight:
            st.markdown(insight)

        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Chart")

        if result_df is not None:
            st.dataframe(result_df, use_container_width=True)
            st.caption("Table")

        if suggestions:
            st.markdown("**You might also ask:**")
            btn_cols = st.columns(len(suggestions))
            idx_base = len(st.session_state.get("chat_history", []))
            for i, suggestion in enumerate(suggestions):
                with btn_cols[i]:
                    if st.button(
                        f"💬 {suggestion}",
                        key=f"new_followup_{idx_base}_{i}",
                        use_container_width=True,
                    ):
                        st.session_state.pending_question = suggestion
                        st.rerun()

    # Persist assistant message to history
    _append_history(
        {
            "role": "assistant",
            "content": insight,
            "visual_type": response_type,
            "fig": fig,
            "result_df": result_df,
            "follow_up_suggestions": suggestions,
        }
    )


def _append_history(msg: Dict[str, Any]) -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    st.session_state.chat_history.append(msg)
