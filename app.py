"""Streamlit interface for the AI-powered B2B campaign and content generator."""

import json
from datetime import date
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from config import load_settings
from modules.account_based_marketing import generate_account_strategies
from modules.analytics import load_sample_campaign_data, recommend_kpis
from modules.approval_workflow import (
    approve_content,
    get_approved_content,
    parse_edited_content,
    serialize_content,
)
from modules.campaign_planner import generate_campaign_calendar
from modules.campaign_intelligence import recommend_campaign_intelligence
from modules.campaign_dashboard import (
    SIMULATED_LABEL,
    calculate_campaign_kpis,
    campaign_insights,
    filter_campaign_data,
    load_simulated_campaign_data,
)
from modules.content_generator import (
    generate_email_campaign,
    generate_linkedin_posts,
    generate_sales_enablement,
)
from modules.content_quality import SCORE_LABEL, evaluate_content
from modules.llm_client import LLMError
from modules.persona_generator import generate_persona, generate_value_proposition


st.set_page_config(
    page_title="AI B2B Campaign Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #f5f7fb; }
    [data-testid="stSidebar"] { background: #10243a; }
    [data-testid="stSidebar"] * { color: #f4f7fb; }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #0b1e33;
        color: #f4f7fb;
        border-color: #2d5877;
    }
    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] textarea::placeholder {
        color: #a9c6d9;
        opacity: 1;
    }
    .hero {
        padding: 1.5rem 1.8rem; border-radius: 16px; color: white;
        background: linear-gradient(115deg, #10243a 0%, #145b86 65%, #00a3ad 100%);
        margin-bottom: 1.2rem;
    }
    .hero p { margin-bottom: .15rem; color: #e3f3fa; }
    .note {
        padding: .8rem 1rem; border-left: 4px solid #e6a23c;
        background: #fff8e9; border-radius: 5px; margin: .7rem 0 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PAGES = [
    "Campaign performance dashboard",
    "Customer persona",
    "Value proposition",
    "LinkedIn content",
    "Email campaign",
    "Sales enablement",
    "Campaign planner",
    "KPI recommendations",
    "Account-based marketing",
    "Campaign intelligence",
]


def add_downloads(value: Any, key: str) -> None:
    """Offer reusable TXT and CSV exports for generated structured content."""
    text = json.dumps(value, indent=2, ensure_ascii=False)
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        export_frame = pd.json_normalize(value, sep=".")
    elif isinstance(value, dict):
        export_frame = pd.json_normalize(value, sep=".")
    else:
        export_frame = pd.DataFrame({"content": [text]})
    left, right = st.columns(2)
    left.download_button(
        "Download TXT",
        data=text,
        file_name=f"{key}.txt",
        mime="text/plain",
        key=f"{key}_txt",
    )
    right.download_button(
        "Download CSV",
        data=export_frame.to_csv(index=False),
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"{key}_csv",
    )


def render_output(key: str, title: str) -> None:
    """Render editable content, quality guidance, and approval-gated downloads."""
    generated = st.session_state.get(key)
    if generated is None:
        return
    drafts = st.session_state.setdefault("marketing_drafts", {})
    approvals = st.session_state.setdefault("marketing_approvals", {})
    if key not in drafts:
        drafts[key] = generated
        approvals[key] = False

    value = drafts[key]
    st.divider()
    st.subheader(title)
    assessment = evaluate_content(
        value,
        target_audience=st.session_state.get("review_audience", "Enterprise buyer"),
        business_challenges=st.session_state.get("review_challenges", ""),
        brand_terms=st.session_state.get("review_brand_terms", []),
    )
    st.caption(SCORE_LABEL)
    st.metric("Editorial quality score", f"{assessment['overall_score']} / 5")
    score_columns = st.columns(3)
    for index, score in enumerate(assessment["scores"]):
        with score_columns[index % len(score_columns)]:
            st.caption(f"{score['dimension']}: **{score['score']}/5**")
    for flag in assessment["flags"]:
        st.caption(flag)
    with st.expander("Quality scoring methodology", expanded=False):
        st.write(assessment["methodology"])
        st.json(assessment["scores"])

    editor_key = f"marketing_editor_{key}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = serialize_content(value)
    with st.form(f"review_form_{key}"):
        edited_text = st.text_area(
            "Review and edit generated JSON",
            key=editor_key,
            height=300,
            help="Edit the content directly. Valid JSON is required to save or approve.",
        )
        save_clicked, approve_clicked = st.columns(2)
        with save_clicked:
            save_draft = st.form_submit_button("Save edits", use_container_width=True)
        with approve_clicked:
            approve_draft = st.form_submit_button(
                "Approve content", type="primary", use_container_width=True
            )

    if save_draft or approve_draft:
        approvals[key] = False
        try:
            updated = (
                approve_content(edited_text)
                if approve_draft
                else parse_edited_content(edited_text)
            )
            drafts[key] = updated
            approvals[key] = bool(approve_draft)
            if approve_draft:
                st.success("Content approved for export.")
            else:
                st.info("Edits saved. Review and approve before exporting.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    if approvals.get(key, False):
        st.success("Approved draft — ready to export.")
        try:
            approved = get_approved_content(drafts, approvals, key)
            add_downloads(approved, key)
        except ValueError as exc:
            st.error(str(exc))
    else:
        st.warning("Draft only. TXT and CSV downloads become available after human approval.")
    with st.expander("Current draft preview", expanded=False):
        st.json(drafts[key], expanded=True)


def set_result(key: str, generator: Any, title: str) -> None:
    """Run one generator with user-visible progress and actionable errors."""
    try:
        with st.spinner(f"Creating {title.lower()}..."):
            generated = generator()
            st.session_state[key] = generated
            st.session_state.setdefault("marketing_drafts", {})[key] = generated
            st.session_state.setdefault("marketing_approvals", {})[key] = False
            st.session_state.pop(f"marketing_editor_{key}", None)
    except (LLMError, ValueError) as exc:
        st.error(str(exc))


def _format_rate(value: float | None) -> str:
    return f"{value:.2%}" if value is not None else "N/A"


def _format_currency(value: float | None) -> str:
    return f"${value:,.2f}" if value is not None else "N/A"


def render_campaign_performance_dashboard() -> None:
    """Render the interactive, explicitly simulated campaign performance dashboard."""
    st.header("B2B Marketing Campaign Performance Dashboard")
    st.error(
        f"**{SIMULATED_LABEL}.** Figures, opportunities, and pipeline are fabricated "
        "for dashboard demonstration only; they are not actual campaign or customer results."
    )
    try:
        data = load_simulated_campaign_data()
    except (FileNotFoundError, ValueError, pd.errors.ParserError) as exc:
        st.error(f"Could not load the simulated campaign dataset: {exc}")
        return

    minimum_date = data["date"].min().date()
    maximum_date = data["date"].max().date()
    st.subheader("Interactive filters")
    date_range = st.date_input(
        "Date range",
        value=(minimum_date, maximum_date),
        min_value=minimum_date,
        max_value=maximum_date,
        key="performance_date_range",
    )
    if not isinstance(date_range, tuple) or len(date_range) != 2:
        st.info("Select both a start date and an end date to view campaign performance.")
        return

    filters = st.columns(4)
    with filters[0]:
        industries = st.multiselect(
            "Industry",
            sorted(data["industry"].dropna().unique()),
            default=sorted(data["industry"].dropna().unique()),
            key="performance_industries",
        )
    with filters[1]:
        channels = st.multiselect(
            "Marketing channel",
            sorted(data["channel"].dropna().unique()),
            default=sorted(data["channel"].dropna().unique()),
            key="performance_channels",
        )
    with filters[2]:
        campaign_types = st.multiselect(
            "Campaign type",
            sorted(data["campaign_type"].dropna().unique()),
            default=sorted(data["campaign_type"].dropna().unique()),
            key="performance_campaign_types",
        )
    with filters[3]:
        objectives = st.multiselect(
            "Campaign objective",
            sorted(data["campaign_objective"].dropna().unique()),
            default=sorted(data["campaign_objective"].dropna().unique()),
            key="performance_objectives",
        )

    if not industries or not channels or not campaign_types or not objectives:
        st.info("Select at least one value for industry, channel, campaign type, and objective.")
        return

    filtered = filter_campaign_data(
        data,
        date_range[0],
        date_range[1],
        industries,
        channels,
        campaign_types,
        objectives,
    )
    st.caption(
        f"{len(filtered):,} of {len(data):,} simulated records selected. "
        "All figures below remain demonstration data."
    )
    if filtered.empty:
        st.warning("No simulated records match these filters. Expand the filters to continue.")
        return

    st.subheader("Performance summary")
    roi_enabled = st.checkbox(
        "Show campaign ROI using an explicit simulated attributed-revenue assumption",
        value=False,
        help=(
            "ROI is hidden unless you explicitly enable it and provide a positive simulated "
            "revenue assumption. Formula: (assumed revenue - filtered campaign expenditure) "
            "/ filtered campaign expenditure."
        ),
    )
    revenue_assumption = None
    if roi_enabled:
        revenue_assumption = st.number_input(
            "Simulated attributed revenue assumption (USD)",
            min_value=0.0,
            value=0.0,
            step=10000.0,
            help="A user-provided hypothetical input for demonstration, not observed revenue.",
        )
        if revenue_assumption <= 0:
            st.warning("Enter a positive simulated revenue assumption to calculate ROI.")
            revenue_assumption = None

    kpis = calculate_campaign_kpis(filtered, revenue_assumption)
    kpi_cards = [
        ("Total impressions", f"{kpis['total_impressions']:,}"),
        ("Total clicks", f"{kpis['total_clicks']:,}"),
        ("Click-through rate (CTR)", _format_rate(kpis["ctr"])),
        ("Engagement rate", _format_rate(kpis["engagement_rate"])),
        ("Leads generated", f"{kpis['leads_generated']:,}"),
        ("Marketing qualified leads (MQLs)", f"{kpis['mqls']:,}"),
        ("Sales qualified leads (SQLs)", f"{kpis['sqls']:,}"),
        ("Lead conversion rate (leads / clicks)", _format_rate(kpis["lead_conversion_rate"])),
        ("Campaign expenditure", _format_currency(kpis["campaign_expenditure_usd"])),
        ("Cost per lead (CPL)", _format_currency(kpis["cost_per_lead_usd"])),
        (
            f"Cost per acquisition (CPA; {kpis['acquisitions_observed']} records with data)",
            _format_currency(kpis["cost_per_acquisition_usd"]),
        ),
        ("Simulated pipeline influence", _format_currency(kpis["pipeline_influence_usd"])),
    ]
    for row_start in range(0, len(kpi_cards), 4):
        card_columns = st.columns(4)
        for column, (label, value) in zip(card_columns, kpi_cards[row_start : row_start + 4]):
            column.metric(label, value)
    if roi_enabled and revenue_assumption is not None:
        if kpis["roi_percent"] is None:
            st.info("ROI is unavailable because filtered campaign expenditure is zero.")
        else:
            st.metric("Simulated ROI (based on user-entered revenue assumption)", f"{kpis['roi_percent']:.1f}%")
            st.caption(
                f"Assumed revenue: {_format_currency(revenue_assumption)}. Formula: "
                "(assumed revenue - campaign expenditure) / campaign expenditure. "
                "This is a hypothetical scenario, not measured campaign ROI."
            )

    st.subheader("Campaign performance visualizations")
    by_channel = (
        filtered.groupby("channel", as_index=False)
        .agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            leads=("leads", "sum"),
            mqls=("mqls", "sum"),
            sqls=("sqls", "sum"),
            expenditure=("campaign_expenditure_usd", "sum"),
            engagements=("engagements", "sum"),
        )
    )
    by_channel["ctr"] = by_channel.apply(
        lambda row: row["clicks"] / row["impressions"] if row["impressions"] else 0,
        axis=1,
    )
    by_channel["engagement_rate"] = by_channel.apply(
        lambda row: row["engagements"] / row["impressions"] if row["impressions"] else 0,
        axis=1,
    )
    channel_chart = px.bar(
        by_channel.sort_values("leads", ascending=False),
        x="channel",
        y="leads",
        color="channel",
        hover_data=["impressions", "clicks", "ctr", "engagement_rate", "expenditure"],
        title="Campaign performance by channel — leads with reach and response context",
        labels={"leads": "Leads", "channel": "Marketing channel"},
    )
    st.plotly_chart(channel_chart, use_container_width=True)

    funnel = pd.DataFrame(
        {
            "stage": ["Impressions", "Clicks", "Leads", "MQLs", "SQLs"],
            "volume": [
                kpis["total_impressions"],
                kpis["total_clicks"],
                kpis["leads_generated"],
                kpis["mqls"],
                kpis["sqls"],
            ],
        }
    )
    st.plotly_chart(
        px.funnel(funnel, x="volume", y="stage", title="Lead funnel visualization"),
        use_container_width=True,
    )

    monthly = filtered.assign(month=filtered["date"].dt.to_period("M").astype(str))
    monthly = monthly.groupby("month", as_index=False).agg(
        impressions=("impressions", "sum"),
        leads=("leads", "sum"),
        clicks=("clicks", "sum"),
    )
    monthly["ctr"] = monthly.apply(
        lambda row: row["clicks"] / row["impressions"] if row["impressions"] else 0,
        axis=1,
    )
    monthly_chart = make_subplots(specs=[[{"secondary_y": True}]])
    monthly_chart.add_trace(
        go.Scatter(x=monthly["month"], y=monthly["impressions"], name="Impressions", mode="lines+markers"),
        secondary_y=False,
    )
    monthly_chart.add_trace(
        go.Scatter(x=monthly["month"], y=monthly["leads"], name="Leads", mode="lines+markers"),
        secondary_y=False,
    )
    monthly_chart.add_trace(
        go.Scatter(x=monthly["month"], y=monthly["ctr"], name="CTR", mode="lines+markers"),
        secondary_y=True,
    )
    monthly_chart.update_layout(title="Monthly campaign performance", xaxis_title="Month")
    monthly_chart.update_yaxes(title_text="Impressions / leads", secondary_y=False)
    monthly_chart.update_yaxes(title_text="CTR", tickformat=".1%", secondary_y=True)
    st.plotly_chart(monthly_chart, use_container_width=True)

    by_industry = filtered.groupby("industry", as_index=False)["leads"].sum()
    st.plotly_chart(
        px.bar(
            by_industry.sort_values("leads"),
            x="leads",
            y="industry",
            orientation="h",
            color="industry",
            title="Industry-wise lead generation",
            labels={"leads": "Leads", "industry": "Industry"},
        ),
        use_container_width=True,
    )

    spend_chart = px.scatter(
        filtered,
        x="campaign_expenditure_usd",
        y="leads",
        color="channel",
        size="mqls",
        hover_data=["campaign_name", "industry", "campaign_type", "campaign_objective"],
        title="Campaign expenditure versus leads generated",
        labels={"campaign_expenditure_usd": "Campaign expenditure (USD)", "leads": "Leads"},
    )
    st.plotly_chart(spend_chart, use_container_width=True)

    by_content = (
        filtered.groupby("content_type", as_index=False)
        .agg(engagements=("engagements", "sum"), impressions=("impressions", "sum"))
    )
    by_content["engagement_rate"] = by_content.apply(
        lambda row: row["engagements"] / row["impressions"] if row["impressions"] else 0,
        axis=1,
    )
    st.plotly_chart(
        px.bar(
            by_content.sort_values("engagement_rate", ascending=False),
            x="content_type",
            y="engagement_rate",
            color="content_type",
            title="Content engagement comparison (weighted engagement rate)",
            labels={"engagement_rate": "Engagement rate", "content_type": "Content type"},
        ).update_yaxes(tickformat=".1%"),
        use_container_width=True,
    )

    mql_sql = by_channel.copy()
    mql_sql["mql_to_sql_rate"] = mql_sql.apply(
        lambda row: row["sqls"] / row["mqls"] if row["mqls"] else 0,
        axis=1,
    )
    st.plotly_chart(
        px.bar(
            mql_sql.sort_values("mql_to_sql_rate", ascending=False),
            x="channel",
            y="mql_to_sql_rate",
            color="channel",
            hover_data=["mqls", "sqls"],
            title="MQL-to-SQL conversion analysis by channel",
            labels={"mql_to_sql_rate": "SQLs / MQLs", "channel": "Marketing channel"},
        ).update_yaxes(tickformat=".1%"),
        use_container_width=True,
    )

    st.subheader("Business insights")
    st.caption("Directional comparisons from the filtered simulated dataset; not causal conclusions.")
    for insight in campaign_insights(filtered):
        st.write(f"- {insight}")

    with st.expander("Metric definitions and assumptions"):
        st.markdown(
            """
            - **CTR** = total clicks / total impressions.
            - **Engagement rate** = total engagements / total impressions.
            - **Lead conversion rate** = total leads / total clicks.
            - **CPL** = campaign expenditure / total leads.
            - **CPA** = expenditure on records with observed acquisition data / observed simulated
              acquisitions. Records without acquisition data are excluded from both numerator and
              denominator; acquisition coverage is shown.
            - **Pipeline influence** = sum of explicitly simulated opportunity influence amounts;
              this is not sourced from a CRM or actual opportunities.
            - **ROI** is not shown by default. When enabled with positive, user-entered simulated
              attributed revenue, ROI = (assumed revenue - campaign expenditure) / expenditure.
            - Ratios with zero denominators are shown as N/A or zero on charts, never as infinity.
            """
        )

    report_columns = st.columns(2)
    report_columns[0].download_button(
        "Download filtered campaign report (CSV)",
        data=filtered.to_csv(index=False),
        file_name="simulated_campaign_performance_filtered.csv",
        mime="text/csv",
        key="performance_filtered_csv",
    )
    kpi_report = pd.DataFrame(
        [{"metric": key, "value": value, "data_label": SIMULATED_LABEL} for key, value in kpis.items()]
    )
    report_columns[1].download_button(
        "Download filtered KPI summary (CSV)",
        data=kpi_report.to_csv(index=False),
        file_name="simulated_campaign_kpi_summary.csv",
        mime="text/csv",
        key="performance_kpi_csv",
    )


def main() -> None:
    settings = load_settings()
    with st.sidebar:
        st.title("AI Campaign Studio")
        page = st.radio("Workspace", PAGES, label_visibility="collapsed")
        st.divider()
        st.subheader("Campaign context")
        industry = st.selectbox("Industry", ["BFSI", "Banking", "Insurance", "Capital markets", "Other"])
        company_size = st.selectbox(
            "Company size",
            ["Enterprise (10,000+ employees)", "Large (1,000-9,999)", "Mid-market (200-999)"],
        )
        job_role = st.text_input("Target job role", "Chief Information Officer")
        challenges = st.text_area(
            "Business challenges",
            "Prioritizing AI opportunities; aligning business and technology stakeholders",
            height=90,
        )
        maturity = st.selectbox(
            "Technology adoption maturity",
            ["Exploring", "Developing", "Established", "Advanced"],
        )
        solution_name = st.text_input("Illustrative solution", "Enterprise AI solution")
        campaign_goal = st.text_input("Campaign goal", "Start a discovery conversation")
        tone = st.selectbox(
            "Content tone",
            ["professional", "consultative", "thought leadership"],
            help="Tone is applied to live prompts and deterministic sample content.",
        )
        sample_mode = st.toggle("Use sample mode (no API key)", value=True)
        if sample_mode:
            st.caption("Deterministic sample outputs are enabled; no external API call is made.")
        elif settings.api_key:
            st.caption(f"Live provider: {settings.provider} · model: {settings.model}")
        else:
            st.warning("Add LLM_API_KEY to .env for live generation, or enable sample mode.")

    st.session_state["review_audience"] = job_role
    st.session_state["review_challenges"] = challenges
    st.session_state["review_brand_terms"] = [solution_name] if solution_name else []

    st.markdown(
        "<div class='hero'><h1>AI-Powered B2B Marketing Campaign &amp; Content Generator</h1>"
        "<p>Enterprise campaign concepts for technology marketing teams · BFSI illustrative use case</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='note'><strong>Portfolio demonstration:</strong> The solution name is "
        "illustrative. Campaigns, personas, and data are hypothetical. No product capabilities, "
        "customer outcomes, or performance claims are asserted. Validate "
        "all facts and approvals before external use.</div>",
        unsafe_allow_html=True,
    )

    if page == "Campaign performance dashboard":
        render_campaign_performance_dashboard()

    elif page == "Customer persona":
        st.header("Customer Persona Generator")
        st.write("Develop a working enterprise buyer hypothesis for account research and validation.")
        if st.button("Generate customer persona", type="primary"):
            set_result(
                "persona_result",
                lambda: generate_persona(
                    industry, company_size, job_role, challenges, maturity, sample_mode, tone
                ),
                "customer persona",
            )
        render_output("persona_result", "Illustrative buyer persona")

    elif page == "Value proposition":
        st.header("Value Proposition Generator")
        st.write("Build a customer-specific positioning hypothesis and evidence-aware message framework.")
        if st.button("Generate value proposition", type="primary"):
            set_result(
                "value_result",
                lambda: generate_value_proposition(
                    industry,
                    company_size,
                    job_role,
                    challenges,
                    solution_name,
                    campaign_goal,
                    sample_mode,
                    tone,
                ),
                "value proposition",
            )
        render_output("value_result", "Positioning and messaging framework")

    elif page == "LinkedIn content":
        st.header("LinkedIn Content Generator")
        st.write("Generate thought leadership, educational, and promotional post concepts.")
        if st.button("Generate three LinkedIn posts", type="primary"):
            set_result(
                "linkedin_result",
                lambda: generate_linkedin_posts(
                    industry, job_role, challenges, solution_name, campaign_goal, sample_mode, tone
                ),
                "LinkedIn posts",
            )
        render_output("linkedin_result", "LinkedIn post concepts")

    elif page == "Email campaign":
        st.header("Email Campaign Generator")
        st.write("Create a personalized initial email and two respectful follow-ups.")
        if st.button("Generate email sequence", type="primary"):
            set_result(
                "email_result",
                lambda: generate_email_campaign(
                    industry, job_role, challenges, solution_name, campaign_goal, sample_mode, tone
                ),
                "email sequence",
            )
        render_output("email_result", "Email sequence")

    elif page == "Sales enablement":
        st.header("Sales Enablement Generator")
        st.write("Prepare an evidence-conscious executive brief, pitch, FAQs, and objection guidance.")
        if st.button("Generate sales enablement pack", type="primary"):
            set_result(
                "sales_result",
                lambda: generate_sales_enablement(
                    industry, job_role, challenges, solution_name, campaign_goal, sample_mode, tone
                ),
                "sales enablement pack",
            )
        render_output("sales_result", "Sales enablement pack")

    elif page == "Campaign planner":
        st.header("30-Day Campaign Planner")
        start_date = st.date_input("Campaign start date", value=date.today())
        if st.button("Generate 30-day calendar", type="primary"):
            set_result(
                "calendar_result",
                lambda: generate_campaign_calendar(
                    start_date, industry, job_role, challenges, campaign_goal, sample_mode, tone
                ),
                "30-day calendar",
            )
        calendar = st.session_state.get("calendar_result")
        if calendar:
            st.caption("All entries are planning concepts; confirm dates, channels, and approvals.")
            st.dataframe(pd.DataFrame(calendar), use_container_width=True, hide_index=True)
            render_output("calendar_result", "Review the campaign calendar")

    elif page == "KPI recommendations":
        st.header("Marketing KPI Recommendation Engine")
        st.write("Select measurement readiness to get a practical, objective-aligned KPI shortlist.")
        with st.form("kpi_form"):
            objective = st.selectbox(
                "Primary objective",
                ["Awareness and reach", "Engagement", "Lead generation", "Pipeline influence"],
            )
            channels = st.multiselect(
                "Channels in scope",
                ["LinkedIn", "Email", "Website", "Webinar", "Paid media", "Sales outreach"],
                default=["LinkedIn", "Email", "Website"],
            )
            tracks_paid_spend = st.checkbox("Paid spend is attributable")
            has_crm_attribution = st.checkbox("CRM attribution is defined and available")
            submitted = st.form_submit_button("Recommend KPIs", type="primary")
        if submitted:
            st.session_state["kpi_result"] = recommend_kpis(
                objective, channels, tracks_paid_spend, has_crm_attribution
            )
        if "kpi_result" in st.session_state:
            result = st.session_state["kpi_result"]
            st.subheader("Recommended metrics")
            st.dataframe(pd.DataFrame(result), use_container_width=True, hide_index=True)
            render_output("kpi_result", "Review KPI recommendations")

        st.divider()
        st.subheader("Illustrative campaign data")
        st.caption(
            "The records below are fabricated examples for demonstrating analysis only; "
            "they are not actual company or customer results."
        )
        try:
            sample_data = load_sample_campaign_data()
            st.dataframe(sample_data, use_container_width=True, hide_index=True)
            chart_data = sample_data.groupby("channel", as_index=False)["impressions"].sum()
            chart = px.bar(
                chart_data,
                x="channel",
                y="impressions",
                title="Hypothetical impressions by channel",
                color_discrete_sequence=["#087e8b"],
            )
            st.plotly_chart(chart, use_container_width=True)
            st.download_button(
                "Download sample campaign data (CSV)",
                data=sample_data.to_csv(index=False),
                file_name="hypothetical_campaign_data.csv",
                mime="text/csv",
                key="sample_data_csv",
            )
        except (FileNotFoundError, ValueError, pd.errors.ParserError) as exc:
            st.error(f"Could not load the illustrative campaign data: {exc}")

    elif page == "Account-based marketing":
        st.header("Account-Based Marketing")
        st.write(
            "Create separate messaging hypotheses for each target account using only the "
            "context you provide. The prefilled account names and priorities are hypothetical demo inputs."
        )
        with st.form("abm_form"):
            accounts_text = st.text_area(
                "Target accounts",
                "Northstar Bank | Banking | Evaluating AI priorities across business teams\n"
                "Cedar Mutual | Insurance | Aligning operations and technology stakeholders",
                height=120,
                help="One account per line: Account name | industry | account-specific challenge. "
                "Omit fields when not known; do not enter confidential data.",
            )
            submitted = st.form_submit_button("Generate account strategies", type="primary")
        if submitted:
            set_result(
                "abm_result",
                lambda: generate_account_strategies(
                    accounts_text,
                    job_role,
                    challenges,
                    solution_name,
                    campaign_goal,
                    tone,
                    sample_mode,
                ),
                "account strategies",
            )
        render_output("abm_result", "Account-specific messaging hypotheses")

    else:
        st.header("Campaign Intelligence")
        st.write(
            "Build a channel recommendation and map sample activities to awareness, "
            "consideration, and conversion."
        )
        with st.form("campaign_intelligence_form"):
            available_channels = st.multiselect(
                "Available channels",
                ["LinkedIn", "Email", "Webinar", "Website", "Sales enablement"],
                default=["LinkedIn", "Email", "Webinar", "Website", "Sales enablement"],
            )
            submitted = st.form_submit_button("Recommend campaign mix", type="primary")
        if submitted:
            set_result(
                "campaign_intelligence_result",
                lambda: recommend_campaign_intelligence(
                    industry,
                    job_role,
                    challenges,
                    campaign_goal,
                    available_channels,
                ),
                "campaign recommendations",
            )
        render_output(
            "campaign_intelligence_result",
            "Recommended channel mix and funnel activities",
        )

    st.caption(
        "Before activation: validate product facts, target-account details, legal/privacy "
        "requirements, brand voice, and measurement definitions."
    )


if __name__ == "__main__":
    main()
