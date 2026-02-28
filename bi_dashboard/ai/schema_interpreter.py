import json
import os
from typing import Any, Dict, List, Optional

import anthropic

from ai.prompts import JSON_FIX_PROMPT, SCHEMA_SYSTEM, SCHEMA_USER

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

def interpret_schema(column_profiles_json: str) -> Dict[str, Any]:
    """
    Send column profiles to Claude and receive a structured schema interpretation.
    Includes one automatic retry if the response is malformed JSON.
    Raises RuntimeError with a user-friendly message if both attempts fail.
    """
    client = _get_client()
    user_prompt = SCHEMA_USER.format(column_profile_json=column_profiles_json)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SCHEMA_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_text = response.content[0].text

        try:
            return _parse_json(raw_text)
        except json.JSONDecodeError:
            # One retry asking Claude to fix the JSON
            retry = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SCHEMA_SYSTEM,
                messages=[
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": raw_text},
                    {"role": "user", "content": JSON_FIX_PROMPT},
                ],
            )
            return _parse_json(retry.content[0].text)

    except anthropic.APIError as e:
        raise RuntimeError(
            f"AI analysis service is unavailable. Please check your API key and try again. ({e})"
        ) from e


def build_column_map(schema: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Build a lookup dict: original_column_name → {business_label, role, description}.
    Used throughout the app to translate raw names to friendly labels.
    """
    return {
        col["original_name"]: {
            "business_label": col.get("business_label", col["original_name"]),
            "role": col.get("role", "text"),
            "description": col.get("description", ""),
        }
        for col in schema.get("columns", [])
    }


def get_columns_by_role(schema: Dict[str, Any]) -> Dict[str, List[str]]:
    """Return {role: [original_column_names]} mapping from schema."""
    by_role: Dict[str, List[str]] = {}
    for col in schema.get("columns", []):
        role = col.get("role", "text")
        by_role.setdefault(role, []).append(col["original_name"])
    return by_role


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> Dict[str, Any]:
    """Strip markdown fences if present and parse JSON."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first line (``` or ```json) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner)
    return json.loads(text)
