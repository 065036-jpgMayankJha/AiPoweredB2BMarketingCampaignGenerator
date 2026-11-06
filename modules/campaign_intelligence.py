"""Deterministic channel, objective, CTA, and funnel recommendations."""

from typing import Any


CHANNEL_GUIDANCE = {
    "LinkedIn": "Test professional audience reach and expert-led discussion.",
    "Email": "Use only for permission-appropriate, relevant one-to-one or nurture outreach.",
    "Webinar": "Offer a deeper educational conversation for an interested audience.",
    "Website": "Provide a clear destination for considered evaluation and conversion actions.",
    "Sales enablement": "Equip account teams with consistent discovery questions and approved facts.",
}

OBJECTIVE_CTA = {
    "Awareness": ("Build awareness of the business question", "Explore the topic"),
    "Consideration": ("Help the audience evaluate the problem", "Review an educational resource"),
    "Conversion": ("Invite an appropriate next step", "Request a discovery conversation"),
}


def recommend_campaign_intelligence(
    industry: str,
    buyer_persona: str,
    business_challenges: str,
    campaign_goal: str,
    available_channels: list[str] | None = None,
) -> dict[str, Any]:
    """Recommend an explainable channel mix and map suggested activities to funnel stages."""
    channels = (
        ["LinkedIn", "Email", "Webinar", "Website", "Sales enablement"]
        if available_channels is None
        else available_channels
    )
    valid_channels = [channel for channel in channels if channel in CHANNEL_GUIDANCE]
    if not valid_channels:
        raise ValueError("Select at least one supported channel.")

    goal = campaign_goal.casefold()
    if any(term in goal for term in ("lead", "meeting", "conversion", "demo", "discovery")):
        priority_stage = "Conversion"
        preferred = ["Email", "Sales enablement", "Website"]
    elif any(term in goal for term in ("awareness", "reach", "brand", "introduce")):
        priority_stage = "Awareness"
        preferred = ["LinkedIn", "Website", "Webinar"]
    else:
        priority_stage = "Consideration"
        preferred = ["LinkedIn", "Webinar", "Email", "Website"]

    ranked_channels = sorted(
        valid_channels,
        key=lambda channel: (channel not in preferred, preferred.index(channel) if channel in preferred else 99),
    )
    selected = ranked_channels[: min(3, len(ranked_channels))]
    activities: list[dict[str, str]] = []
    activity_templates = [
        ("Awareness", "Thought leadership post", "Introduce the business question"),
        ("Consideration", "Educational resource or webinar", "Help assess evaluation criteria"),
        ("Conversion", "Permission-appropriate outreach", "Offer a relevant discovery next step"),
    ]
    for stage, activity, objective in activity_templates:
        stage_objective, cta = OBJECTIVE_CTA[stage]
        channel = next(
            (candidate for candidate in selected if candidate in _channels_for_stage(stage)),
            selected[0],
        )
        activities.append(
            {
                "funnel_stage": stage,
                "activity": activity,
                "recommended_channel": channel,
                "objective": stage_objective,
                "cta": cta,
                "target_persona": buyer_persona,
                "rationale": activity + " can be tested against the stated campaign goal.",
                "assumptions": "Hypothesis only; validate channel access, audience consent, and fit.",
            }
        )

    return {
        "recommended_channels": [
            {
                "channel": channel,
                "reason": CHANNEL_GUIDANCE[channel],
                "priority": index + 1,
                "assumptions": "Strategic recommendation, not an outcome prediction.",
            }
            for index, channel in enumerate(selected)
        ],
        "suggested_campaign_objective": campaign_goal or OBJECTIVE_CTA[priority_stage][0],
        "priority_funnel_stage": priority_stage,
        "activities": activities,
        "industry_context": industry,
        "buyer_persona": buyer_persona,
        "business_challenges": business_challenges,
        "assumptions": [
            "Recommendations are planning hypotheses, not verified account or channel research.",
            "Confirm objectives, privacy/consent, and measurement definitions before activation.",
        ],
    }


def _channels_for_stage(stage: str) -> tuple[str, ...]:
    if stage == "Awareness":
        return "LinkedIn", "Website", "Webinar"
    if stage == "Consideration":
        return "Webinar", "LinkedIn", "Website", "Email"
    return "Email", "Sales enablement", "Website"
