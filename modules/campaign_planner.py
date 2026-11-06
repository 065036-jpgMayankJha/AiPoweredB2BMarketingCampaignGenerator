"""Thirty-day, multi-channel campaign calendar generation."""

from datetime import date, timedelta
from typing import Any

from modules.llm_client import generate_json
from modules.prompt_engine import apply_sample_tone, build_marketing_prompt


def generate_campaign_calendar(
    start_date: date,
    industry: str,
    job_role: str,
    challenges: str,
    campaign_goal: str,
    use_sample_mode: bool,
    tone: str = "professional",
) -> list[dict[str, Any]]:
    channels = ["LinkedIn", "Email", "Website", "Webinar", "Sales enablement"]
    content_types = [
        "Thought leadership post",
        "Educational email",
        "Explainer article",
        "Webinar invitation",
        "Sales discovery guide",
    ]
    sample = []
    for day_index in range(30):
        day_date = start_date + timedelta(days=day_index)
        sample.append(
            {
                "day": day_index + 1,
                "date": day_date.isoformat(),
                "content_type": content_types[day_index % len(content_types)],
                "channel": channels[day_index % len(channels)],
                "target_persona": f"{job_role} in {industry}",
                "objective": campaign_goal,
                "cta": (
                    "Explore the topic"
                    if day_index % 3 == 0
                    else "Review the resource"
                    if day_index % 3 == 1
                    else "Start a discovery conversation"
                ),
                "assumptions": "Hypothetical planning idea; validate audience, timing, and approvals.",
            }
        )
    task = (
        "Build a 30-day B2B campaign calendar. Return a JSON array with exactly 30 objects, "
        "one for each consecutive date starting on the given start_date. Each object must contain "
        "day (integer 1-30), date (YYYY-MM-DD), content_type, channel, target_persona, objective, "
        "cta, assumptions. Use varied but realistic content/channel formats and a coherent "
        "awareness-to-consideration-to-action progression. "
        f"Start date: {start_date.isoformat()}. Industry: {industry}. Buyer: {job_role}. "
        f"Challenges: {challenges}. Campaign goal: {campaign_goal}. "
        "Keep activities hypothetical and do not imply product capabilities or results."
    )
    prompt = build_marketing_prompt(
        "Campaign planner",
        task,
        industry,
        job_role,
        challenges,
        tone,
        additional_context=f"Campaign start date: {start_date.isoformat()}. Goal: {campaign_goal}.",
    )
    result = generate_json(prompt, sample, use_sample_mode, "campaign_calendar")
    if not isinstance(result, list) or len(result) != 30:
        raise ValueError("The campaign calendar must contain exactly 30 daily entries.")
    required_keys = {"day", "date", "content_type", "channel", "target_persona", "objective", "cta"}
    for index, entry in enumerate(result, start=1):
        if not isinstance(entry, dict) or not required_keys.issubset(entry):
            raise ValueError(f"Calendar entry {index} is missing one or more required fields.")
    return apply_sample_tone(result, tone) if use_sample_mode else result


def generate_campaign_strategy(
    industry: str,
    company_size: str,
    job_role: str,
    challenges: str,
    campaign_goal: str,
    channels: list[str],
    use_sample_mode: bool,
    tone: str = "professional",
) -> dict[str, Any]:
    """Create an evidence-conscious campaign strategy with explicit planning assumptions."""
    selected_channels = channels or ["LinkedIn", "Email", "Website"]
    sample = {
        "campaign_name": f"Hypothetical {industry} discovery campaign",
        "campaign_objective": campaign_goal,
        "target_audience": f"{job_role} at {company_size} {industry} organizations",
        "marketing_channels": selected_channels,
        "campaign_phases": [
            {
                "phase": "Awareness",
                "objective": "Introduce the business question and relevant context.",
                "activities": ["Thought leadership post", "Educational website content"],
            },
            {
                "phase": "Consideration",
                "objective": "Help interested stakeholders assess their requirements.",
                "activities": ["Evaluation checklist", "Educational webinar or email"],
            },
            {
                "phase": "Discovery",
                "objective": "Invite an appropriate, permission-aware next step.",
                "activities": ["Discovery conversation using approved information"],
            },
        ],
        "content_strategy": [
            "Address the stated business challenge without making unverified product claims.",
            "Use educational content to help stakeholders define evaluation criteria.",
            "Adapt channel execution to confirmed audience access and consent.",
        ],
        "timeline": [
            {"period": "Weeks 1-2", "focus": "Awareness and audience validation"},
            {"period": "Weeks 3-4", "focus": "Education and consideration"},
            {"period": "Weeks 5-6", "focus": "Discovery and measurement review"},
        ],
        "budget_allocation_assumptions": [
            "No budget amount or allocation is supplied; determine it after channel costs and scope are validated.",
            "Any future allocation should be treated as a planning assumption, not a forecast.",
        ],
        "expected_kpis": [
            "Awareness: qualified reach or impressions; establish a baseline before setting a target.",
            "Consideration: engaged visits or content interactions; define engagement consistently.",
            "Discovery: qualified conversations; agree qualification rules with sales.",
        ],
        "business_challenges": challenges,
        "assumptions": [
            "Hypothetical campaign recommendation; no performance outcome is forecast.",
            "Validate audience, channel availability, budget, timing, and approved product evidence.",
        ],
    }
    task = (
        "Create a hypothetical B2B campaign strategy as one JSON object. Include campaign_name, "
        "campaign_objective, target_audience, marketing_channels (array), campaign_phases (array), "
        "content_strategy (array), timeline (array), budget_allocation_assumptions (array), "
        "expected_kpis (array), and assumptions (array). Use only provided context; do not invent "
        "a budget, baseline, target, product claim, or campaign result. State unknowns as items "
        "to validate. "
        f"Industry: {industry}. Company size: {company_size}. Buyer: {job_role}. "
        f"Business challenges: {challenges}. Campaign objective: {campaign_goal}. "
        f"Available channels: {', '.join(selected_channels)}."
    )
    prompt = build_marketing_prompt(
        "Campaign strategy",
        task,
        industry,
        job_role,
        challenges,
        tone,
        additional_context=f"Company size: {company_size}; channels: {', '.join(selected_channels)}.",
    )
    result = generate_json(prompt, sample, use_sample_mode, "campaign_strategy")
    return apply_sample_tone(result, tone) if use_sample_mode else result
