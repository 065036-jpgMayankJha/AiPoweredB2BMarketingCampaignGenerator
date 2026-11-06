"""Synthetic B2B campaign performance data, filtering, and safe KPI calculations."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "campaign_performance_simulated.csv"
SIMULATED_LABEL = "SIMULATED DEMONSTRATION DATA - NOT ACTUAL CAMPAIGN PERFORMANCE"

CHANNELS = ["LinkedIn", "Email", "Webinar", "Paid Search", "Website", "Events"]
INDUSTRIES = ["BFSI", "Banking", "Insurance", "Healthcare", "Manufacturing"]
CAMPAIGN_TYPES = [
    "Account-Based Marketing",
    "Demand Generation",
    "Thought Leadership",
    "Nurture",
    "Webinar",
]
OBJECTIVES = ["Awareness", "Engagement", "Lead Generation", "Pipeline Acceleration"]
CONTENT_TYPES = [
    "Thought Leadership",
    "Educational Article",
    "Webinar",
    "Case Study Concept",
    "Email Nurture",
]
REQUIRED_COLUMNS = {
    "campaign_id",
    "date",
    "campaign_name",
    "industry",
    "channel",
    "campaign_type",
    "campaign_objective",
    "content_type",
    "impressions",
    "clicks",
    "engagements",
    "leads",
    "mqls",
    "sqls",
    "campaign_expenditure_usd",
    "acquisitions",
    "simulated_opportunities_influenced",
    "simulated_pipeline_influence_usd",
    "is_simulated_demo_data",
    "data_source_label",
}


def safe_divide(numerator: float, denominator: float) -> float | None:
    """Return a ratio, or None when the denominator is zero or invalid."""
    if pd.isna(denominator) or denominator == 0:
        return None
    return numerator / denominator


def generate_simulated_campaign_data(record_count: int = 144) -> pd.DataFrame:
    """Generate reproducible synthetic records across months and marketing dimensions."""
    if record_count < 100:
        raise ValueError("The simulated campaign dataset must contain at least 100 records.")

    rng = random.Random(20261106)
    rows: list[dict[str, Any]] = []
    start = pd.Timestamp("2025-01-01")
    channel_factors = {
        "LinkedIn": 1.0,
        "Email": 0.82,
        "Webinar": 0.62,
        "Paid Search": 1.14,
        "Website": 0.74,
        "Events": 0.48,
    }
    objective_factors = {
        "Awareness": 1.35,
        "Engagement": 1.08,
        "Lead Generation": 0.96,
        "Pipeline Acceleration": 0.82,
    }

    for index in range(record_count):
        month_index = index % 24
        campaign_date = start + pd.DateOffset(
            months=month_index,
            days=(index // 24) * 4,
        )
        channel = CHANNELS[index % len(CHANNELS)]
        industry = INDUSTRIES[(index // 2 + index) % len(INDUSTRIES)]
        campaign_type = CAMPAIGN_TYPES[(index // 3 + index) % len(CAMPAIGN_TYPES)]
        objective = OBJECTIVES[(index // 5 + index) % len(OBJECTIVES)]
        content_type = CONTENT_TYPES[(index // 2 + index) % len(CONTENT_TYPES)]
        quality_factor = 0.72 + (index % 9) * 0.055

        impressions = int(
            rng.randint(4800, 28500)
            * channel_factors[channel]
            * objective_factors[objective]
        )
        ctr = min(0.095, max(0.008, rng.uniform(0.018, 0.058) * quality_factor))
        clicks = min(impressions, int(impressions * ctr))
        engagement_rate = min(0.18, max(0.01, rng.uniform(0.035, 0.105) * quality_factor))
        engagements = max(clicks, int(impressions * engagement_rate))
        conversion_rate = max(0.008, rng.uniform(0.045, 0.19) * quality_factor)
        leads = min(clicks, int(clicks * conversion_rate))
        mql_rate = rng.uniform(0.38, 0.78)
        mqls = min(leads, int(leads * mql_rate))
        sql_rate = rng.uniform(0.28, 0.68)
        sqls = min(mqls, int(mqls * sql_rate))
        expenditure = round(
            rng.uniform(650, 8600)
            * (1.25 if channel in {"Events", "Webinar"} else 1.0),
            2,
        )
        acquisition_observed = index % 5 != 0
        acquisitions: int | None = (
            min(sqls, int(sqls * rng.uniform(0.08, 0.4)))
            if acquisition_observed
            else None
        )
        opportunities = (
            min(sqls, int(sqls * rng.uniform(0.18, 0.65)))
            if sqls
            else 0
        )
        pipeline = round(
            sum(rng.uniform(18000, 115000) for _ in range(opportunities)),
            2,
        )

        rows.append(
            {
                "campaign_id": f"SIM-{campaign_date:%Y%m}-{index + 1:04d}",
                "date": campaign_date.date().isoformat(),
                "campaign_name": f"{campaign_type} - {industry} - {channel}",
                "industry": industry,
                "channel": channel,
                "campaign_type": campaign_type,
                "campaign_objective": objective,
                "content_type": content_type,
                "impressions": impressions,
                "clicks": clicks,
                "engagements": engagements,
                "leads": leads,
                "mqls": mqls,
                "sqls": sqls,
                "campaign_expenditure_usd": expenditure,
                "acquisitions": acquisitions,
                "simulated_opportunities_influenced": opportunities,
                "simulated_pipeline_influence_usd": pipeline,
                "is_simulated_demo_data": True,
                "data_source_label": SIMULATED_LABEL,
            }
        )

    return pd.DataFrame(rows)


def save_simulated_campaign_data(path: Path = DATA_PATH, record_count: int = 144) -> Path:
    """Write the reproducible demonstration dataset to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    generate_simulated_campaign_data(record_count).to_csv(path, index=False)
    return path


def load_simulated_campaign_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and validate the explicitly marked simulated campaign dataset."""
    if not path.is_file():
        raise FileNotFoundError(f"Simulated campaign performance data not found: {path}")
    frame = pd.read_csv(path, parse_dates=["date"])
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            "Simulated campaign dataset is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
    if len(frame) < 100:
        raise ValueError("Simulated campaign dataset must have at least 100 records.")
    if not frame["is_simulated_demo_data"].astype(str).str.casefold().isin(
        {"true", "1"}
    ).all():
        raise ValueError("Campaign dashboard data must be explicitly marked simulated.")
    if frame.empty:
        raise ValueError("Simulated campaign performance data contains no records.")
    return frame


def filter_campaign_data(
    frame: pd.DataFrame,
    start_date: Any,
    end_date: Any,
    industries: list[str] | None = None,
    channels: list[str] | None = None,
    campaign_types: list[str] | None = None,
    objectives: list[str] | None = None,
) -> pd.DataFrame:
    """Apply inclusive date and categorical filters without mutating input data."""
    filtered = frame.copy()
    dates = pd.to_datetime(filtered["date"])
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if start > end:
        raise ValueError("Start date must be on or before end date.")
    filtered = filtered.loc[dates.between(start, end)].copy()

    for column, selected in (
        ("industry", industries),
        ("channel", channels),
        ("campaign_type", campaign_types),
        ("campaign_objective", objectives),
    ):
        if selected is not None:
            filtered = filtered.loc[filtered[column].isin(selected)].copy()
    return filtered


def calculate_campaign_kpis(
    frame: pd.DataFrame,
    simulated_revenue_assumption: float | None = None,
) -> dict[str, float | int | None]:
    """Aggregate marketing metrics with safe denominators and an optional ROI assumption."""
    if frame.empty:
        return {
            "total_impressions": 0,
            "total_clicks": 0,
            "ctr": None,
            "engagement_rate": None,
            "leads_generated": 0,
            "mqls": 0,
            "sqls": 0,
            "lead_conversion_rate": None,
            "campaign_expenditure_usd": 0.0,
            "cost_per_lead_usd": None,
            "cost_per_acquisition_usd": None,
            "pipeline_influence_usd": 0.0,
            "roi_percent": None,
            "acquisitions_observed": 0,
            "simulated_revenue_assumption_usd": None,
        }

    impressions = int(frame["impressions"].sum())
    clicks = int(frame["clicks"].sum())
    engagements = int(frame["engagements"].sum())
    leads = int(frame["leads"].sum())
    mqls = int(frame["mqls"].sum())
    sqls = int(frame["sqls"].sum())
    expenditure = float(frame["campaign_expenditure_usd"].sum())
    acquisition_values = pd.to_numeric(frame["acquisitions"], errors="coerce")
    acquisitions_observed = int(acquisition_values.notna().sum())
    acquisitions = float(acquisition_values.sum(min_count=1)) if acquisitions_observed else None
    acquisition_spend = (
        float(frame.loc[acquisition_values.notna(), "campaign_expenditure_usd"].sum())
        if acquisitions_observed
        else None
    )
    pipeline = float(frame["simulated_pipeline_influence_usd"].sum())
    roi_percent = None

    if simulated_revenue_assumption is not None:
        if simulated_revenue_assumption <= 0:
            raise ValueError("Simulated revenue assumption must be greater than zero.")
        if expenditure > 0:
            roi_percent = (
                simulated_revenue_assumption - expenditure
            ) / expenditure * 100

    return {
        "total_impressions": impressions,
        "total_clicks": clicks,
        "ctr": safe_divide(clicks, impressions),
        "engagement_rate": safe_divide(engagements, impressions),
        "leads_generated": leads,
        "mqls": mqls,
        "sqls": sqls,
        "lead_conversion_rate": safe_divide(leads, clicks),
        "campaign_expenditure_usd": expenditure,
        "cost_per_lead_usd": safe_divide(expenditure, leads),
        "cost_per_acquisition_usd": (
            safe_divide(acquisition_spend, acquisitions) # type: ignore
            if acquisitions is not None
            else None
        ),
        "pipeline_influence_usd": pipeline,
        "roi_percent": roi_percent,
        "acquisitions_observed": acquisitions_observed,
        "simulated_revenue_assumption_usd": simulated_revenue_assumption,
    }


def campaign_insights(frame: pd.DataFrame) -> list[str]:
    """Explain relative simulated results using aggregated rates and volume."""
    if frame.empty:
        return ["No simulated records match the selected filters."]

    by_channel = _aggregate_group(frame, "channel")
    by_channel = by_channel.loc[by_channel["leads"] > 0]
    if by_channel.empty:
        return ["No leads are present in this filtered simulated dataset."]

    lead_leader = by_channel.sort_values("leads", ascending=False).iloc[0]
    efficient = by_channel.sort_values("cost_per_lead_usd").iloc[0]
    best_ctr = by_channel.sort_values("ctr", ascending=False).iloc[0]
    by_type = _aggregate_group(frame, "campaign_type")
    best_type = by_type.sort_values("leads", ascending=False).iloc[0]
    by_campaign = _aggregate_group(frame, "campaign_name")
    by_campaign = by_campaign.loc[by_campaign["leads"] > 0]
    best_campaign = by_campaign.sort_values("leads", ascending=False).iloc[0]
    return [
        (
            f"{lead_leader['channel']} generated the most leads "
            f"({int(lead_leader['leads']):,}) in the selected simulated records; its CTR was "
            f"{lead_leader['ctr']:.1%}, so volume and response can be reviewed together."
        ),
        (
            f"{efficient['channel']} had the lowest simulated CPL "
            f"(${efficient['cost_per_lead_usd']:,.0f}); compare its lead volume and audience mix "
            "before reallocating spend."
        ),
        (
            f"{best_ctr['channel']} recorded the highest simulated CTR ({best_ctr['ctr']:.1%}); "
            "this indicates relative click response in this demo, not causal effectiveness."
        ),
        (
            f"{best_type['campaign_type']} contributed the most simulated leads "
            f"({int(best_type['leads']):,}) among campaign types in the current selection."
        ),
        (
            f"The simulated campaign cohort '{best_campaign['campaign_name']}' generated the "
            f"most leads ({int(best_campaign['leads']):,}); compare its spend and audience "
            "mix before treating it as a repeatable pattern."
        ),
    ]


def _aggregate_group(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    grouped = (
        frame.groupby(column, dropna=False)
        .agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            engagements=("engagements", "sum"),
            leads=("leads", "sum"),
            mqls=("mqls", "sum"),
            sqls=("sqls", "sum"),
            expenditure=("campaign_expenditure_usd", "sum"),
        )
        .reset_index()
    )
    grouped["ctr"] = grouped.apply(
        lambda row: safe_divide(row["clicks"], row["impressions"]), axis=1
    )
    grouped["engagement_rate"] = grouped.apply(
        lambda row: safe_divide(row["engagements"], row["impressions"]), axis=1
    )
    grouped["cost_per_lead_usd"] = grouped.apply(
        lambda row: safe_divide(row["expenditure"], row["leads"]), axis=1
    )
    grouped["mql_to_sql_rate"] = grouped.apply(
        lambda row: safe_divide(row["sqls"], row["mqls"]), axis=1
    )
    return grouped
