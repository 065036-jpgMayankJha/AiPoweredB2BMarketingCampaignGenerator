"""Reusable Streamlit renderers for structured marketing assets."""

from typing import Any

import pandas as pd
import streamlit as st


def _display(value: Any) -> str:
    if value is None or value == "":
        return "Not provided — edit or regenerate to add this information."
    return str(value)


def _render_list(title: str, items: Any) -> None:
    st.markdown(f"**{title}**")
    if isinstance(items, list):
        if items:
            for item in items:
                st.markdown(f"- {_display(item)}")
        else:
            st.caption("No items provided.")
    else:
        st.write(_display(items))


def _render_persona(value: dict[str, Any]) -> None:
    st.subheader(_display(value.get("persona_name")))
    profile = st.columns(3)
    profile[0].metric("Job title", _display(value.get("job_title")))
    profile[1].metric("Industry", _display(value.get("industry")))
    profile[2].metric("Company size", _display(value.get("company_size")))
    tabs = st.tabs(["Profile", "Goals & pain points", "Buying process"])
    with tabs[0]:
        _render_list("Responsibilities", value.get("responsibilities"))
        _render_list(
            "Preferred communication channels",
            value.get("preferred_communication_channels"),
        )
    with tabs[1]:
        columns = st.columns(2)
        with columns[0]:
            _render_list("Business goals", value.get("business_goals"))
        with columns[1]:
            _render_list("Pain points", value.get("pain_points"))
        _render_list("Buying motivations", value.get("buying_motivations"))
    with tabs[2]:
        _render_list("Decision-making criteria", value.get("decision_making_criteria"))
    _render_list("Assumptions to validate", value.get("assumptions"))


def _render_icp(value: dict[str, Any]) -> None:
    columns = st.columns(3)
    for column, label, key in zip(
        columns,
        ("Target industry", "Company size", "Revenue range"),
        ("target_industry", "company_size", "revenue_range"),
    ):
        column.metric(label, _display(value.get(key)))
    st.markdown(
        f"**Geography:** {_display(value.get('geography'))}  \n"
        f"**Technology maturity:** {_display(value.get('technology_maturity'))}"
    )
    left, right = st.columns(2)
    with left:
        _render_list("Business challenges", value.get("business_challenges"))
    with right:
        _render_list("Qualification criteria", value.get("qualification_criteria"))
    _render_list("Assumptions to validate", value.get("assumptions"))


def _render_value_proposition(value: dict[str, Any]) -> None:
    st.markdown("#### Core value proposition")
    st.info(_display(value.get("core_value_proposition")))
    columns = st.columns(2)
    with columns[0]:
        st.markdown("**Customer problem**")
        st.write(_display(value.get("customer_problem")))
    with columns[1]:
        st.markdown("**Proposed solution**")
        st.write(_display(value.get("proposed_solution")))
    left, right = st.columns(2)
    with left:
        _render_list("Key differentiators", value.get("key_differentiators"))
    with right:
        _render_list("Business benefits", value.get("business_benefits"))
    _render_list(
        "Supporting evidence or assumptions",
        value.get("supporting_evidence_or_assumptions"),
    )
    _render_list("Assumptions to validate", value.get("assumptions"))


def _render_linkedin_posts(value: list[Any]) -> None:
    tabs = st.tabs(
        [
            str(post.get("content_format", f"Post {index}"))
            if isinstance(post, dict)
            else f"Post {index}"
            for index, post in enumerate(value, start=1)
        ]
    )
    for tab, post in zip(tabs, value):
        with tab:
            if not isinstance(post, dict):
                st.write(_display(post))
                continue
            st.caption(
                f"{_display(post.get('content_objective'))} · "
                f"{_display(post.get('target_audience'))}"
            )
            st.markdown(f"### {_display(post.get('post_headline'))}")
            body = _display(post.get("post_body"))
            st.markdown(body)
            st.code(body, language=None)
            st.markdown(f"**Call to action:** {_display(post.get('call_to_action'))}")
            _render_list("Suggested hashtags", post.get("suggested_hashtags"))
            _render_list("Assumptions", post.get("assumptions"))


def _render_emails(value: list[Any]) -> None:
    tabs = st.tabs(
        [
            str(email.get("email_subject", f"Email {index}"))
            if isinstance(email, dict)
            else f"Email {index}"
            for index, email in enumerate(value, start=1)
        ]
    )
    for tab, email in zip(tabs, value):
        with tab:
            if not isinstance(email, dict):
                st.write(_display(email))
                continue
            st.caption(
                f"{_display(email.get('campaign_objective'))} · "
                f"{_display(email.get('target_persona'))}"
            )
            st.markdown(f"**Subject:** {_display(email.get('email_subject'))}")
            st.markdown(f"**Preview:** {_display(email.get('preview_text'))}")
            body = _display(email.get("email_body"))
            st.text(body)
            st.code(body, language=None)
            st.markdown(f"**Call to action:** {_display(email.get('call_to_action'))}")
            _render_list(
                "Follow-up suggestions",
                email.get("follow_up_email_suggestions"),
            )
            _render_list("Assumptions", email.get("assumptions"))


def _render_strategy(value: dict[str, Any]) -> None:
    st.subheader(_display(value.get("campaign_name")))
    st.info(_display(value.get("campaign_objective")))
    st.caption(f"Target audience: {_display(value.get('target_audience'))}")
    st.markdown("#### Channel mix")
    channels = value.get("marketing_channels", [])
    for column, channel in zip(st.columns(max(1, min(len(channels), 4))), channels):
        column.metric("Recommended channel", _display(channel))

    phases = value.get("campaign_phases", [])
    if phases:
        st.markdown("#### Campaign phases")
        phase_columns = st.columns(min(len(phases), 3))
        for index, phase in enumerate(phases):
            with phase_columns[index % len(phase_columns)]:
                if isinstance(phase, dict):
                    st.markdown(f"**{_display(phase.get('phase'))}**")
                    st.write(_display(phase.get("objective")))
                    _render_list("Activities", phase.get("activities", []))
                else:
                    st.write(_display(phase))
    timeline = value.get("timeline", [])
    if timeline:
        st.markdown("#### Timeline")
        if all(isinstance(item, dict) for item in timeline):
            st.dataframe(pd.json_normalize(timeline), use_container_width=True, hide_index=True)
        else:
            _render_list("Timeline", timeline)
    _render_list("Content strategy", value.get("content_strategy"))
    _render_list("Budget allocation assumptions", value.get("budget_allocation_assumptions"))
    _render_list("Expected KPIs — hypothetical recommendations", value.get("expected_kpis"))
    _render_list("Assumptions to validate", value.get("assumptions"))


def render_structured_output(asset_type: str, value: Any) -> None:
    """Choose a human-readable preview without exposing raw JSON by default."""
    if asset_type == "customer_persona" and isinstance(value, dict):
        _render_persona(value)
    elif asset_type == "ideal_customer_profile" and isinstance(value, dict):
        _render_icp(value)
    elif asset_type == "value_proposition" and isinstance(value, dict):
        _render_value_proposition(value)
    elif asset_type == "linkedin_posts" and isinstance(value, list):
        _render_linkedin_posts(value)
    elif asset_type == "email_campaign" and isinstance(value, list):
        _render_emails(value)
    elif asset_type == "campaign_strategy" and isinstance(value, dict):
        _render_strategy(value)
    elif asset_type == "kpi_recommendations" and isinstance(value, list):
        columns = [
            "kpi_name",
            "description",
            "measurement_formula",
            "target_value",
            "measurement_frequency",
            "business_relevance",
        ]
        frame = pd.DataFrame(value)
        st.dataframe(
            frame[[column for column in columns if column in frame.columns]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Targets are not benchmarks; establish a baseline before setting numeric goals.")
    elif asset_type == "campaign_calendar" and isinstance(value, list):
        st.dataframe(pd.DataFrame(value), use_container_width=True, hide_index=True)
    elif isinstance(value, list):
        for index, item in enumerate(value, start=1):
            with st.expander(f"Item {index}", expanded=True):
                _render_generic(item)
    else:
        _render_generic(value)


def _render_generic(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            label = key.replace("_", " ").title()
            if isinstance(nested, (list, dict)):
                with st.expander(label, expanded=True):
                    _render_generic(nested)
            else:
                st.markdown(f"**{label}**")
                st.write(_display(nested))
    elif isinstance(value, list):
        for item in value:
            _render_generic(item)
    else:
        st.write(_display(value))


def _edit_value(value: Any, path: str) -> Any:
    if isinstance(value, dict):
        return {
            key: _edit_value(nested, f"{path}_{key}")
            for key, nested in value.items()
        }
    if isinstance(value, list):
        if all(isinstance(item, str) for item in value):
            text = st.text_area(
                path.rsplit("_", 1)[-1].replace("_", " ").title(),
                value="\n".join(value),
                key=f"edit_{path}",
                height=100,
            )
            return [line.strip() for line in text.splitlines() if line.strip()]
        return [
            _edit_value(item, f"{path}_{index}")
            for index, item in enumerate(value, start=1)
        ]
    label = path.rsplit("_", 1)[-1].replace("_", " ").title()
    if isinstance(value, int) and not isinstance(value, bool):
        return st.number_input(label, value=value, step=1, key=f"edit_{path}")
    text = "" if value is None else str(value)
    if len(text) > 100 or "\n" in text:
        return st.text_area(label, value=text, key=f"edit_{path}", height=130)
    return st.text_input(label, value=text, key=f"edit_{path}")


def render_edit_form(value: Any, key: str) -> tuple[bool, Any, bool]:
    """Render a form that edits structured fields and can save or approve the result."""
    with st.expander("Edit generated content", expanded=False):
        with st.form(f"edit_form_{key}"):
            edited = _edit_value(value, key)
            save_column, approve_column = st.columns(2)
            with save_column:
                save = st.form_submit_button("Save edits", use_container_width=True)
            with approve_column:
                approve = st.form_submit_button(
                    "Save and approve", type="primary", use_container_width=True
                )
    return save or approve, edited, approve
