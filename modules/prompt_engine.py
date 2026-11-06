"""Reusable, evidence-conscious prompt construction for marketing generators."""

from copy import deepcopy
from typing import Any


INDUSTRY_CONTEXT = {
    "BFSI": (
        "Use an enterprise financial-services lens. Treat governance, risk, privacy, "
        "security, regulatory review, and stakeholder alignment as discovery topics to "
        "validate for the specific organization, not as verified account facts."
    ),
    "Banking": (
        "Use a banking audience lens. Frame operational, customer, risk, and technology "
        "priorities as questions to validate with the account; do not imply a known initiative."
    ),
    "Insurance": (
        "Use an insurance audience lens. Frame distribution, service, operations, risk, and "
        "technology priorities as discovery hypotheses that require account validation."
    ),
    "Capital markets": (
        "Use a capital-markets audience lens. Frame workflow, data, risk, and technology "
        "considerations as topics to validate; do not infer account practices."
    ),
}

TONE_GUIDANCE = {
    "professional": (
        "Use precise, concise enterprise language. Keep the message factual, respectful, "
        "and specific to the stated audience."
    ),
    "consultative": (
        "Use a collaborative, discovery-led voice. Acknowledge the stated challenge, ask "
        "relevant questions, avoid pressure, and offer a practical next step."
    ),
    "thought leadership": (
        "Use an insightful, perspective-led voice grounded in the supplied context. Offer "
        "a useful point of view without implying research, trend data, or proof not supplied."
    ),
}


def build_marketing_prompt(
    module: str,
    task: str,
    industry: str,
    buyer_persona: str,
    business_challenges: str,
    tone: str = "professional",
    additional_context: str = "",
) -> str:
    """Build a structured prompt with explicit audience, evidence, and output constraints."""
    normalized_tone = tone.strip().lower()
    if normalized_tone not in TONE_GUIDANCE:
        raise ValueError(f"Unsupported tone '{tone}'. Choose professional, consultative, or thought leadership.")

    industry_context = INDUSTRY_CONTEXT.get(
        industry,
        "Use only the supplied industry and account context. Do not assume industry facts.",
    )
    sections = [
        f"MARKETING MODULE\n{module}",
        f"INDUSTRY CONTEXT\n{industry_context}",
        f"BUYER PERSONA\n{buyer_persona}",
        f"STATED BUSINESS CHALLENGES\n{business_challenges}",
        f"CONTENT TONE: {normalized_tone}\n{TONE_GUIDANCE[normalized_tone]}",
        f"TASK AND REQUIRED OUTPUT\n{task}",
        (
            "EVIDENCE AND CLAIMS GUARDRAILS\n"
            "Use only facts explicitly provided in this prompt. Do not invent product "
            "capabilities, customer results, certifications, benchmarks, market statistics, "
            "account research, or performance guarantees. Clearly label campaign ideas and "
            "inferences as hypotheses or assumptions. Where evidence is missing, identify what "
            "must be validated rather than asserting it."
        ),
    ]
    if additional_context.strip():
        sections.insert(5, f"ADDITIONAL USER-PROVIDED CONTEXT\n{additional_context.strip()}")
    return "\n\n".join(sections)


def apply_sample_tone(content: Any, tone: str) -> Any:
    """Make deterministic demo content visibly respond to the selected tone."""
    normalized_tone = tone.strip().lower()
    if normalized_tone not in TONE_GUIDANCE:
        raise ValueError(f"Unsupported tone '{tone}'. Choose professional, consultative, or thought leadership.")
    result = deepcopy(content)

    def adapt(value: Any) -> Any:
        if isinstance(value, list):
            return [adapt(item) for item in value]
        if not isinstance(value, dict):
            return value

        updated = {key: adapt(item) for key, item in value.items()}
        updated["content_tone"] = normalized_tone
        if normalized_tone == "consultative":
            cta = updated.get("call_to_action")
            if isinstance(cta, str) and cta.strip() and not cta.strip().endswith("?"):
                updated["call_to_action"] = f"Would it be useful to {cta[0].lower() + cta[1:]}?"
        elif normalized_tone == "thought leadership":
            hook = updated.get("hook")
            if isinstance(hook, str) and hook.strip() and not hook.startswith("A perspective:"):
                updated["hook"] = f"A perspective: {hook}"
        return updated

    if isinstance(result, list):
        return [adapt(item) for item in result]
    if isinstance(result, dict):
        return adapt(result)
    return result
