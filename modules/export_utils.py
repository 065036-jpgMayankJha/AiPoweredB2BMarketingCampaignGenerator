"""Serialization helpers for individual and complete campaign exports."""

import json
from typing import Any

import pandas as pd


def export_json(value: Any) -> str:
    """Serialize structured campaign data as UTF-8-friendly JSON."""
    return json.dumps(value, indent=2, ensure_ascii=False)


def _text_lines(value: Any, title: str = "") -> list[str]:
    lines: list[str] = []
    if title:
        lines.append(title)
    if isinstance(value, dict):
        for key, nested in value.items():
            label = key.replace("_", " ").strip().title()
            if isinstance(nested, (dict, list)):
                lines.extend(_text_lines(nested, label))
            else:
                lines.append(f"{label}: {nested if nested is not None else 'Not provided'}")
    elif isinstance(value, list):
        for index, nested in enumerate(value, start=1):
            if isinstance(nested, (dict, list)):
                lines.extend(_text_lines(nested, f"Item {index}"))
            else:
                lines.append(f"- {nested if nested is not None else 'Not provided'}")
    else:
        lines.append(str(value) if value is not None else "Not provided")
    return lines


def export_text(value: Any, title: str = "Marketing campaign output") -> str:
    """Render structured output as a readable, plain-text report."""
    return "\n".join(_text_lines(value, title))


def export_campaign_csv(campaign: dict[str, Any]) -> str:
    """Flatten campaign assets into a CSV with an asset identifier per record."""
    rows = []
    for asset_name, asset in campaign.items():
        records = asset if isinstance(asset, list) else [asset]
        for index, record in enumerate(records, start=1):
            if isinstance(record, dict):
                row = {"asset": asset_name, "item": index}
                normalized = pd.json_normalize(record, sep=".").to_dict(orient="records")[0]
                for field, content in normalized.items():
                    row[str(field)] = content
                rows.append(row)
            else:
                rows.append({"asset": asset_name, "item": index, "content": record})
    return pd.DataFrame(rows).to_csv(index=False)
