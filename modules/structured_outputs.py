"""Required field definitions for structured marketing outputs."""

from typing import Any


FIELD_SCHEMAS: dict[str, dict[str, type[Any]]] = {
    "customer_persona": {
        "persona_name": str,
        "job_title": str,
        "industry": str,
        "company_size": str,
        "responsibilities": list,
        "business_goals": list,
        "pain_points": list,
        "buying_motivations": list,
        "decision_making_criteria": list,
        "preferred_communication_channels": list,
    },
    "ideal_customer_profile": {
        "target_industry": str,
        "company_size": str,
        "revenue_range": str,
        "geography": str,
        "technology_maturity": str,
        "business_challenges": list,
        "qualification_criteria": list,
    },
    "value_proposition": {
        "customer_problem": str,
        "proposed_solution": str,
        "core_value_proposition": str,
        "key_differentiators": list,
        "business_benefits": list,
        "supporting_evidence_or_assumptions": list,
    },
    "linkedin_post": {
        "content_objective": str,
        "target_audience": str,
        "post_headline": str,
        "post_body": str,
        "call_to_action": str,
        "suggested_hashtags": list,
        "content_format": str,
    },
    "email": {
        "campaign_objective": str,
        "target_persona": str,
        "email_subject": str,
        "preview_text": str,
        "email_body": str,
        "call_to_action": str,
        "follow_up_email_suggestions": list,
    },
    "campaign_strategy": {
        "campaign_name": str,
        "campaign_objective": str,
        "target_audience": str,
        "marketing_channels": list,
        "campaign_phases": list,
        "content_strategy": list,
        "timeline": list,
        "budget_allocation_assumptions": list,
        "expected_kpis": list,
    },
    "kpi": {
        "kpi_name": str,
        "description": str,
        "measurement_formula": str,
        "target_value": str,
        "measurement_frequency": str,
        "business_relevance": str,
    },
    "calendar_entry": {
        "day": int,
        "date": str,
        "content_type": str,
        "channel": str,
        "target_persona": str,
        "objective": str,
        "cta": str,
    },
}

LIST_OUTPUT_SCHEMAS = {
    "linkedin_posts": ("linkedin_post", 3),
    "email_campaign": ("email", 3),
    "kpi_recommendations": ("kpi", None),
    "campaign_calendar": ("calendar_entry", 30),
}

OUTPUT_KEY_SCHEMAS = {
    "persona_result": "customer_persona",
    "icp_result": "ideal_customer_profile",
    "value_result": "value_proposition",
    "linkedin_result": "linkedin_posts",
    "email_result": "email_campaign",
    "strategy_result": "campaign_strategy",
    "kpi_result": "kpi_recommendations",
    "calendar_result": "campaign_calendar",
}


class StructuredOutputError(ValueError):
    """Raised when an LLM response does not match its required output schema."""


def _validate_object(value: Any, schema_name: str, location: str) -> None:
    if not isinstance(value, dict):
        raise StructuredOutputError(f"{location} must be a JSON object.")

    fields = FIELD_SCHEMAS[schema_name]
    errors = []
    for field, expected_type in fields.items():
        field_location = f"{location}.{field}"
        if field not in value:
            errors.append(f"{field_location} is missing")
            continue
        field_value = value[field]
        if field_value is None:
            errors.append(f"{field_location} must not be null")
        elif not isinstance(field_value, expected_type) or (
            expected_type is int and isinstance(field_value, bool)
        ):
            errors.append(
                f"{field_location} must be {expected_type.__name__}, "
                f"not {type(field_value).__name__}"
            )
        elif isinstance(field_value, str) and not field_value.strip():
            errors.append(f"{field_location} must not be empty")
        elif isinstance(field_value, list) and not field_value:
            errors.append(f"{field_location} must contain at least one item")
        elif isinstance(field_value, list):
            allow_objects = schema_name == "campaign_strategy" and field in {
                "campaign_phases",
                "timeline",
                "expected_kpis",
            }
            for index, item in enumerate(field_value, start=1):
                item_location = f"{field_location}[{index}]"
                if item is None:
                    errors.append(f"{item_location} must not be null")
                elif allow_objects and not isinstance(item, (str, dict)):
                    errors.append(f"{item_location} must be a string or JSON object")
                elif not allow_objects and (
                    not isinstance(item, str) or not item.strip()
                ):
                    errors.append(f"{item_location} must be a non-empty string")

    if errors:
        raise StructuredOutputError("Invalid structured output: " + "; ".join(errors) + ".")


def validate_structured_output(value: Any, schema_name: str) -> Any:
    """Validate mandatory fields without filling in missing model-generated content."""
    if schema_name in FIELD_SCHEMAS:
        _validate_object(value, schema_name, schema_name)
        return value

    if schema_name not in LIST_OUTPUT_SCHEMAS:
        raise ValueError(f"Unknown structured output schema: {schema_name}.")

    item_schema, expected_length = LIST_OUTPUT_SCHEMAS[schema_name]
    if not isinstance(value, list):
        raise StructuredOutputError(f"{schema_name} must be a JSON array.")
    if expected_length is not None and len(value) != expected_length:
        raise StructuredOutputError(
            f"{schema_name} must contain exactly {expected_length} items; received {len(value)}."
        )
    if not value:
        raise StructuredOutputError(f"{schema_name} must contain at least one item.")
    for index, item in enumerate(value, start=1):
        _validate_object(item, item_schema, f"{schema_name}[{index}]")
    return value
