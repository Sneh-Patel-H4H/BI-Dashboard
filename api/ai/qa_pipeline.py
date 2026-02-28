import json
import os
from typing import Any, Dict, List, Optional

import anthropic
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ai.prompts import JSON_FIX, QA_SYSTEM

MODEL = "claude-sonnet-4-6"
_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def answer(
    question: str,
    schema: Dict[str, Any],
    sample_rows: List[Dict[str, Any]],
    chat_history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Full Q&A pipeline: send question to Claude, execute any generated code,
    return {response_type, insight_text, plotly_json, table_rows, table_columns, follow_up_suggestions}.
    """
    col_schema = [
        {
            "original_name": c["original_name"],
            "business_label": c.get("business_label", c["original_name"]),
            "role": c.get("role", "text"),
        }
        for c in schema.get("columns", [])
    ]

    system = QA_SYSTEM.format(
        sector=schema.get("sector", "Unknown"),
        org_type=schema.get("organization_type", "Unknown"),
        dataset_description=schema.get("dataset_description", ""),
        column_schema_json=json.dumps(col_schema, indent=2),
        sample_rows_json=json.dumps(sample_rows[:500], default=str),
    )

    # Build message history for context
    messages: List[Dict[str, str]] = []
    for msg in chat_history[-6:]:  # last 3 exchanges for context
        messages.append({"role": msg["role"], "content": msg.get("content", "")})
    messages.append({"role": "user", "content": question})

    client = _get_client()
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=4096, system=system, messages=messages
        )
        raw = resp.content[0].text
        try:
            parsed = _parse_json(raw)
        except json.JSONDecodeError:
            retry = client.messages.create(
                model=MODEL, max_tokens=4096, system=system,
                messages=messages + [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": JSON_FIX},
                ],
            )
            parsed = _parse_json(retry.content[0].text)

        return _execute(parsed, sample_rows)

    except anthropic.APIError as e:
        return _error(f"AI service unavailable. Please try again. ({e})")
    except Exception as e:  # noqa: BLE001
        return _error(f"Something went wrong. Please rephrase your question. ({e})")


def _execute(parsed: Dict[str, Any], sample_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "response_type": parsed.get("response_type", "narrative"),
        "insight_text": parsed.get("insight_text", ""),
        "follow_up_suggestions": parsed.get("follow_up_suggestions", [])[:3],
        "plotly_json": None,
        "table_rows": None,
        "table_columns": None,
    }

    code = (parsed.get("pandas_code") or "").strip()
    if not code or result["response_type"] == "narrative":
        return result

    df = pd.DataFrame(sample_rows)
    # Coerce numeric columns
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")
    # Coerce date-like columns
    for col in df.columns:
        if df[col].dtype == object:
            try:
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="ignore")
            except Exception:
                pass

    namespace = {"df": df, "pd": pd, "px": px, "go": go, "np": np}
    try:
        exec(code, namespace)  # noqa: S102 — restricted namespace, single-user MVP
        fig: Optional[go.Figure] = namespace.get("fig")
        result_df: Optional[pd.DataFrame] = namespace.get("result_df")

        if fig is not None:
            result["plotly_json"] = fig.to_json()
        if result_df is not None and isinstance(result_df, pd.DataFrame):
            result["table_columns"] = result_df.columns.tolist()
            result["table_rows"] = result_df.head(100).to_dict(orient="records")

    except Exception as exec_err:  # noqa: BLE001
        fixed = _fix_code(parsed, sample_rows, str(exec_err))
        if fixed:
            return fixed
        result["response_type"] = "narrative"
        result["insight_text"] = (
            result["insight_text"] or
            "I found the answer but had trouble generating the visualisation. "
            "Please try rephrasing your question."
        )

    return result


def _fix_code(original: Dict[str, Any], sample_rows: List[Dict], error: str) -> Optional[Dict[str, Any]]:
    prompt = (
        f"This Python code failed: {error}\n\nFailed code:\n{original.get('pandas_code', '')}\n\n"
        "Fix it. Use 'df' for the DataFrame, 'fig' for Plotly figures, 'result_df' for DataFrames. "
        "Return only valid JSON with the same structure."
    )
    client = _get_client()
    try:
        resp = client.messages.create(model=MODEL, max_tokens=2048,
                                      messages=[{"role": "user", "content": prompt}])
        return _execute(_parse_json(resp.content[0].text), sample_rows)
    except Exception:  # noqa: BLE001
        return None


def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def _error(msg: str) -> Dict[str, Any]:
    return {
        "response_type": "narrative",
        "insight_text": msg,
        "follow_up_suggestions": [],
        "plotly_json": None,
        "table_rows": None,
        "table_columns": None,
    }
