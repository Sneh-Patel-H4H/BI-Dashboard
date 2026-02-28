import json
import os
from typing import Any, Dict, Optional

import anthropic
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ai.prompts import JSON_FIX_PROMPT, QA_SYSTEM, QA_USER

MODEL = "claude-sonnet-4-6"

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def answer_question(
    question: str,
    df: pd.DataFrame,
    schema: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Route a plain-English question through Claude.
    Returns:
        response_type  : "chart" | "table" | "narrative" | "chart+narrative"
        fig            : Plotly figure or None
        result_df      : DataFrame or None
        insight_text   : plain-English summary
        follow_up_suggestions : list[str]
        error          : str or None
    """
    column_schema = _build_column_schema(df, schema)
    sample_rows = _safe_json(df.head(5).to_dict(orient="records"))

    system_prompt = QA_SYSTEM.format(
        sector=schema.get("sector", "Unknown"),
        org_type=schema.get("organization_type", "Unknown"),
        dataset_description=schema.get("dataset_description", ""),
        column_schema_json=json.dumps(column_schema, indent=2),
        sample_rows_json=json.dumps(sample_rows, indent=2),
    )

    client = _get_client()

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": QA_USER.format(user_question=question)}],
        )
        raw_text = response.content[0].text

        try:
            parsed = _parse_json(raw_text)
        except json.JSONDecodeError:
            retry = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": QA_USER.format(user_question=question)},
                    {"role": "assistant", "content": raw_text},
                    {"role": "user", "content": JSON_FIX_PROMPT},
                ],
            )
            parsed = _parse_json(retry.content[0].text)

        return _execute_response(parsed, df, schema)

    except anthropic.APIError as e:
        return _error_response(f"I could not connect to the AI service. Please try again. ({e})")
    except Exception as e:  # noqa: BLE001
        return _error_response(f"Something went wrong. Please try rephrasing your question. ({e})")


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def _execute_response(
    parsed: Dict[str, Any],
    df: pd.DataFrame,
    schema: Dict[str, Any],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "response_type": parsed.get("response_type", "narrative"),
        "insight_text": parsed.get("insight_text", ""),
        "follow_up_suggestions": parsed.get("follow_up_suggestions", [])[:2],
        "fig": None,
        "result_df": None,
        "error": None,
    }

    code = (parsed.get("pandas_code") or "").strip()
    if not code or result["response_type"] == "narrative":
        return result

    # Restricted namespace — single-user local tool; exec is the standard approach
    # here. Only df, pandas, plotly, and numpy are exposed to Claude's code.
    namespace: Dict[str, Any] = {
        "df": df.copy(),
        "pd": pd,
        "px": px,
        "go": go,
        "np": np,
    }

    try:
        exec(code, namespace)  # noqa: S102
        result["fig"] = namespace.get("fig")
        result["result_df"] = namespace.get("result_df")
    except Exception as exec_err:  # noqa: BLE001
        # Ask Claude to fix the code once
        fixed = _fix_code(parsed, df, str(exec_err))
        if fixed:
            return fixed
        result["error"] = "I had trouble generating that visualisation."
        result["response_type"] = "narrative"

    return result


def _fix_code(
    original: Dict[str, Any],
    df: pd.DataFrame,
    error_message: str,
) -> Optional[Dict[str, Any]]:
    """Ask Claude to correct code that failed execution."""
    fix_prompt = (
        f"The following Python code failed with this error: {error_message}\n\n"
        f"Failed code:\n{original.get('pandas_code', '')}\n\n"
        "Please provide corrected code. Rules: use 'df' for the DataFrame, "
        "'fig' for Plotly figures (using px or go), 'result_df' for DataFrames. "
        "Return only valid JSON with the same structure as before."
    )
    client = _get_client()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": fix_prompt}],
        )
        parsed = _parse_json(response.content[0].text)
        return _execute_response(parsed, df, {})
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_column_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> list:
    return [
        {
            "original_name": col["original_name"],
            "business_label": col.get("business_label", col["original_name"]),
            "role": col.get("role", "text"),
            "dtype": str(df[col["original_name"]].dtype)
            if col["original_name"] in df.columns
            else "unknown",
        }
        for col in schema.get("columns", [])
        if col["original_name"] in df.columns
    ]


def _safe_json(records: list) -> list:
    """Make a list of dicts JSON-serialisable by converting non-native types."""
    return json.loads(json.dumps(records, default=str))


def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner)
    return json.loads(text)


def _error_response(message: str) -> Dict[str, Any]:
    return {
        "response_type": "narrative",
        "insight_text": message,
        "follow_up_suggestions": [],
        "fig": None,
        "result_df": None,
        "error": message,
    }
