"""Transparent heuristic quality scoring for human review of generated content."""

import re
from typing import Any


SCORE_LABEL = "AI-assisted content quality assessment - not campaign performance."


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(_flatten(item) for item in value)
    return str(value) if value is not None else ""


def _tokens(text: str) -> set[str]:
    return {
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", text)
        if token.casefold() not in {"the", "and", "for", "with", "that", "this", "from", "your"}
    }


def evaluate_content(
    content: Any,
    target_audience: str,
    business_challenges: str,
    brand_terms: list[str] | None = None,
    verified_facts: list[str] | None = None,
) -> dict[str, Any]:
    """Score six review dimensions from 1-5 using explainable text heuristics."""
    text = _flatten(content)
    words = _tokens(text)
    audience_terms = _tokens(target_audience)
    challenge_terms = _tokens(business_challenges)
    brand_terms = [term.strip() for term in (brand_terms or []) if term.strip()]
    verified_facts = [fact.strip() for fact in (verified_facts or []) if fact.strip()]

    relevance_overlap = len(words & (audience_terms | challenge_terms))
    relevance = min(5, 1 + relevance_overlap // 2) if audience_terms or challenge_terms else 2
    sentence_count = max(1, len(re.findall(r"[.!?]+", text)))
    average_words = len(text.split()) / sentence_count
    clarity = 5 if average_words <= 20 else 4 if average_words <= 28 else 3 if average_words <= 38 else 2
    if not text.strip():
        clarity = 1

    normalized = text.casefold()
    brand_matches = [term for term in brand_terms if term.casefold() in normalized]
    brand_consistency = 3 if not brand_terms else min(5, 1 + len(brand_matches) * 2)

    value_signals = {
        "business",
        "priority",
        "challenge",
        "evaluate",
        "decision",
        "workflow",
        "criteria",
        "align",
        "risk",
        "value",
        "goal",
        "outcome",
    }
    business_value = min(5, 1 + len(words & value_signals))

    cta_fields = ("call_to_action", "cta", "next_step", "call to action")
    cta_text = " ".join(
        str(value)
        for key, value in _walk_dict(content)
        if any(field in key.casefold() for field in cta_fields)
    )
    if cta_text:
        cta_strength = 5 if re.search(r"\b(book|schedule|request|register|reply|discuss|start|explore)\b", cta_text, re.I) else 4
        if len(cta_text.split()) > 22:
            cta_strength = max(2, cta_strength - 1)
    else:
        cta_strength = 2

    unsupported_markers = re.findall(
        r"\b(guarantee(?:d|s)?|proven|industry-leading|best-in-class|"
        r"number one|#1|increases? by \d+%|reduces? by \d+%)\b",
        text,
        flags=re.IGNORECASE,
    )
    grounded_fact_matches = sum(
        1 for fact in verified_facts if fact.casefold() in normalized
    )
    factual_grounding = 4 if verified_facts and grounded_fact_matches else 3
    if unsupported_markers:
        factual_grounding = 1
    elif not verified_facts:
        factual_grounding = 2 if any(term in normalized for term in ("assumption", "hypothetical", "validate")) else 3

    dimensions = [
        ("Relevance to target audience", relevance, "Overlap with supplied audience and challenge terms."),
        ("Clarity", clarity, "Heuristic based on average sentence length."),
        ("Brand consistency", brand_consistency, "Checks presence of optional user-provided brand terms."),
        ("Business value", business_value, "Looks for stated business-priority and evaluation language."),
        ("CTA strength", cta_strength, "Checks for a visible, actionable call to action."),
        (
            "Factual grounding",
            factual_grounding,
            "Flags selected unsupported-claim language; this is not a factuality verification.",
        ),
    ]
    scores = [
        {"dimension": name, "score": score, "scale": "1-5", "rationale": rationale}
        for name, score, rationale in dimensions
    ]
    return {
        "label": SCORE_LABEL,
        "overall_score": round(sum(item["score"] for item in scores) / len(scores), 1),
        "scores": scores,
        "flags": [
            "Possible unsupported claim language detected; verify or remove it."
            if unsupported_markers
            else "No selected high-risk claim phrase detected; this does not verify factual accuracy."
        ],
        "methodology": (
            "Transparent text heuristics for editorial review. Scores are directional, "
            "AI-assisted assessments and do not predict engagement, conversion, pipeline, or revenue."
        ),
    }


def _walk_dict(value: Any, parent_key: str = "") -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            items.extend(_walk_dict(nested, str(key)))
    elif isinstance(value, list):
        for nested in value:
            items.extend(_walk_dict(nested, parent_key))
    elif parent_key:
        items.append((parent_key, value))
    return items
