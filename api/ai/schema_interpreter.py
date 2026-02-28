import json
import os
from typing import Any, Dict, List, Optional

import anthropic

from ai.prompts import JSON_FIX, SCHEMA_SYSTEM, SCHEMA_USER

MODEL = "claude-sonnet-4-6"
_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def interpret_schema(profiles_json: str) -> Dict[str, Any]:
    """Call Claude and return structured schema interpretation. Retries once on bad JSON."""
    client = _get_client()
    user_msg = SCHEMA_USER.format(column_profile_json=profiles_json)
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=4096,
            system=SCHEMA_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = resp.content[0].text
        try:
            return _parse(raw)
        except json.JSONDecodeError:
            retry = client.messages.create(
                model=MODEL, max_tokens=4096,
                system=SCHEMA_SYSTEM,
                messages=[
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": JSON_FIX},
                ],
            )
            return _parse(retry.content[0].text)
    except anthropic.APIError as e:
        raise RuntimeError(f"AI service unavailable — please check your API key. ({e})") from e


def _parse(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner)
    return json.loads(text)


def columns_by_role(schema: Dict[str, Any]) -> Dict[str, List[str]]:
    by_role: Dict[str, List[str]] = {}
    for col in schema.get("columns", []):
        by_role.setdefault(col.get("role", "text"), []).append(col["original_name"])
    return by_role


def column_label_map(schema: Dict[str, Any]) -> Dict[str, str]:
    return {c["original_name"]: c.get("business_label", c["original_name"])
            for c in schema.get("columns", [])}
