"""KPI recommendations and sample campaign data loading."""

from pathlib import Path
from typing import Any

import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "campaign_data.csv"

_KPI_CATALOG = [
    {
        "kpi": "Impressions",
        "funnel_stage": "Awareness",
        "definition": "Number of times campaign content was served.",
        "formula": "Platform-reported impressions",
        "recommended_for": "Reach and awareness objectives",
        "measurement_cadence": "Weekly",
    },
    {
        "kpi": "Engagement rate",
        "funnel_stage": "Awareness",
        "definition": "Share of served content that received a defined interaction.",
        "formula": "Engagements / impressions",
        "recommended_for": "Content resonance and audience interaction",
        "measurement_cadence": "Weekly",
    },
    {
        "kpi": "Click-through rate (CTR)",
        "funnel_stage": "Consideration",
        "definition": "Share of impressions that resulted in a click.",
        "formula": "Clicks / impressions",
        "recommended_for": "Traffic-driving content and calls to action",
        "measurement_cadence": "Weekly",
    },
    {
        "kpi": "Conversion rate",
        "funnel_stage": "Conversion",
        "definition": "Share of eligible visits or clicks that completed a defined action.",
        "formula": "Conversions / eligible visits or clicks",
        "recommended_for": "Landing pages and form-based campaign actions",
        "measurement_cadence": "Weekly",
    },
    {
        "kpi": "Marketing-qualified leads (MQLs)",
        "funnel_stage": "Qualification",
        "definition": "Leads meeting the organization's documented marketing qualification rules.",
        "formula": "Count of leads meeting agreed MQL criteria",
        "recommended_for": "Lead generation with an agreed qualification definition",
        "measurement_cadence": "Weekly",
    },
    {
        "kpi": "Sales-qualified leads (SQLs)",
        "funnel_stage": "Qualification",
        "definition": "Leads accepted as sales-qualified under the shared sales definition.",
        "formula": "Count of leads meeting agreed SQL criteria",
        "recommended_for": "Sales handoff and qualification quality",
        "measurement_cadence": "Weekly or monthly",
    },
    {
        "kpi": "Cost per lead (CPL)",
        "funnel_stage": "Efficiency",
        "definition": "Campaign spend per defined lead; compare only like-for-like periods.",
        "formula": "Campaign spend / leads",
        "recommended_for": "Paid campaigns with attributable spend and lead tracking",
        "measurement_cadence": "Monthly",
    },
    {
        "kpi": "Pipeline influence",
        "funnel_stage": "Business impact",
        "definition": "Pipeline associated with campaign engagement under an agreed attribution model.",
        "formula": "Attributed pipeline using the approved attribution model",
        "recommended_for": "Programs with CRM integration and governance-approved attribution",
        "measurement_cadence": "Monthly or quarterly",
    },
]


def recommend_kpis(
    objective: str,
    channels: list[str],
    tracks_paid_spend: bool,
    has_crm_attribution: bool,
) -> list[dict[str, Any]]:
    """Recommend metrics based on stated objectives and measurement readiness."""
    objective_text = objective.casefold()
    selected = list(_KPI_CATALOG)

    if any(term in objective_text for term in ("awareness", "reach", "brand")):
        selected = selected[:3] + selected[3:6]
    elif any(term in objective_text for term in ("lead", "pipeline", "demand")):
        selected = selected[2:6] + selected[6:]

    channel_names = ", ".join(channels) if channels else "Not specified"
    recommendations = []
    for kpi in selected:
        if kpi["kpi"] == "Cost per lead (CPL)" and not tracks_paid_spend:
            continue
        if kpi["kpi"] == "Pipeline influence" and not has_crm_attribution:
            continue
        recommendations.append(
            {
                **kpi,
                "why_recommended": (
                    f"Supports the stated objective ({objective}) when measured consistently "
                    f"across the selected channel(s): {channel_names}."
                ),
                "kpi_name": kpi["kpi"],
                "description": kpi["definition"],
                "measurement_formula": kpi["formula"],
                "target_value": "Set after a baseline and measurement rules are agreed.",
                "measurement_frequency": kpi["measurement_cadence"],
                "business_relevance": kpi["recommended_for"],
                "guardrail": (
                    "Agree definitions, attribution, data sources, and baseline before setting targets."
                ),
                "assumptions": "Recommendation only; no target or benchmark is implied.",
            }
        )
    return recommendations


def load_sample_campaign_data() -> pd.DataFrame:
    """Load explicitly hypothetical, illustrative campaign records."""
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Sample campaign data was not found at {DATA_PATH}.")
    frame = pd.read_csv(DATA_PATH)
    if frame.empty:
        raise ValueError("Sample campaign data contains no records.")
    return frame
