"""Pure helpers for edit, approval, and export gating."""

import json
from typing import Any


def serialize_content(content: Any) -> str:
    """Return editable JSON for a generated object or collection."""
    return json.dumps(content, indent=2, ensure_ascii=False)


def parse_edited_content(editor_text: str) -> Any:
    """Parse user-edited JSON and report invalid edits explicitly."""
    try:
        return json.loads(editor_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Review edits must be valid JSON: {exc.msg} (line {exc.lineno}).") from exc


def approve_content(editor_text: str) -> Any:
    """Validate edited content before it can enter the approved state."""
    content = parse_edited_content(editor_text)
    if content in ({}, [], None, ""):
        raise ValueError("Empty content cannot be approved.")
    return content


def get_approved_content(drafts: dict[str, Any], approvals: dict[str, bool], key: str) -> Any:
    """Return content for export only after its current draft has been approved."""
    if not approvals.get(key, False):
        raise ValueError("Review and approve this content before exporting it.")
    if key not in drafts:
        raise ValueError("No saved draft is available for approval.")
    return drafts[key]
