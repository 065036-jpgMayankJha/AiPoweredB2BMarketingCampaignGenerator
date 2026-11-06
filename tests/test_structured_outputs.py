"""Tests for structured generation, validation, and campaign exports."""

import csv
import io
import json
import unittest
from unittest.mock import Mock, patch

import requests

from config import Settings
from modules.approval_workflow import approve_content, get_approved_content
from modules.campaign_planner import generate_campaign_strategy
from modules.export_utils import export_campaign_csv, export_json, export_text
from modules.json_utils import JSONResponseError, parse_json_response
from modules.llm_client import LLMServiceError, generate_json
from modules.persona_generator import generate_icp, generate_persona, generate_value_proposition
from modules.analytics import recommend_kpis
from modules.structured_outputs import validate_structured_output
from modules.content_generator import generate_email_campaign, generate_linkedin_posts


PERSONA = {
    "persona_name": "Technology executive",
    "job_title": "Chief Information Officer",
    "industry": "BFSI",
    "company_size": "Enterprise",
    "responsibilities": ["Align stakeholders"],
    "business_goals": ["Clarify priorities"],
    "pain_points": ["Competing priorities"],
    "buying_motivations": ["Resolve a stated challenge"],
    "decision_making_criteria": ["Evidence and strategic fit"],
    "preferred_communication_channels": ["Professional email"],
}


def _completion(content: str) -> Mock:
    response = Mock()
    response.ok = True
    response.json.return_value = {
        "choices": [{"message": {"content": content}}],
    }
    return response


class JSONParsingTests(unittest.TestCase):
    def test_valid_json_and_markdown_code_fence(self) -> None:
        expected = {"message": "Ready"}
        self.assertEqual(parse_json_response(json.dumps(expected)), expected)
        self.assertEqual(
            parse_json_response(f"```json\n{json.dumps(expected)}\n```"),
            expected,
        )

    def test_malformed_empty_missing_and_null_responses_are_actionable(self) -> None:
        with self.assertRaisesRegex(JSONResponseError, "not valid JSON"):
            parse_json_response("{broken")
        with self.assertRaisesRegex(JSONResponseError, "empty response"):
            parse_json_response("  ")
        with self.assertRaisesRegex(JSONResponseError, "is missing"):
            parse_json_response("{}", "customer_persona")
        incomplete = {**PERSONA, "job_title": None}
        with self.assertRaisesRegex(JSONResponseError, "must not be null"):
            parse_json_response(json.dumps(incomplete), "customer_persona")

    def test_one_controlled_json_repair_is_attempted(self) -> None:
        settings = Settings(
            "openai_compatible",
            "test-key",
            "https://example.test/v1",
            "test-model",
            3,
        )
        with (
            patch("modules.llm_client.load_settings", return_value=settings),
            patch(
                "modules.llm_client.requests.post",
                side_effect=[
                    _completion("{}"),
                    _completion(json.dumps(PERSONA)),
                ],
            ) as request,
        ):
            result = generate_json("Make a persona.", {}, False, "customer_persona")
        self.assertEqual(result, PERSONA)
        self.assertEqual(request.call_count, 2)
        self.assertIn("JSON REPAIR REQUEST", request.call_args.kwargs["json"]["messages"][1]["content"])
        self.assertEqual(
            request.call_args.kwargs["headers"]["Authorization"],
            "Bearer test-key",
        )

    def test_api_failure_is_reported_without_retrying_as_json_repair(self) -> None:
        settings = Settings(
            "openai_compatible",
            "test-key",
            "https://example.test/v1",
            "test-model",
            3,
        )
        with (
            patch("modules.llm_client.load_settings", return_value=settings),
            patch(
                "modules.llm_client.requests.post",
                side_effect=requests.ConnectionError("provider unavailable"),
            ) as request,
        ):
            with self.assertRaisesRegex(LLMServiceError, "Could not reach"):
                generate_json("Make a persona.", {}, False, "customer_persona")
        self.assertEqual(request.call_count, 1)

    def test_empty_provider_completion_is_reported(self) -> None:
        settings = Settings(
            "openai_compatible",
            "test-key",
            "https://example.test/v1",
            "test-model",
            3,
        )
        with (
            patch("modules.llm_client.load_settings", return_value=settings),
            patch(
                "modules.llm_client.requests.post",
                return_value=_completion("  "),
            ) as request,
        ):
            with self.assertRaisesRegex(LLMServiceError, "empty completion"):
                generate_json("Make a persona.", {}, False, "customer_persona")
        self.assertEqual(request.call_count, 1)

    def test_demo_generation_needs_no_api_key_and_returns_structured_assets(self) -> None:
        with patch("modules.llm_client.load_settings", side_effect=AssertionError("API settings read")):
            persona = generate_persona(
                "BFSI", "Enterprise", "CIO", "Align stakeholders", "Exploring", True
            )
            icp = generate_icp(
                "BFSI", "Enterprise", "", "", "Exploring", "Align stakeholders", True
            )
            value = generate_value_proposition(
                "BFSI", "Enterprise", "CIO", "Align stakeholders", "Example solution",
                "Start a conversation", True,
            )
            posts = generate_linkedin_posts(
                "BFSI", "CIO", "Align stakeholders", "Example solution",
                "Start a conversation", True,
            )
            emails = generate_email_campaign(
                "BFSI", "CIO", "Align stakeholders", "Example solution",
                "Start a conversation", True,
            )
            strategy = generate_campaign_strategy(
                "BFSI", "Enterprise", "CIO", "Align stakeholders",
                "Start a conversation", ["LinkedIn"], True,
            )
        self.assertIn("preferred_communication_channels", persona)
        self.assertIn("qualification_criteria", icp)
        self.assertIn("supporting_evidence_or_assumptions", value)
        validate_structured_output(posts, "linkedin_posts")
        validate_structured_output(emails, "email_campaign")
        validate_structured_output(strategy, "campaign_strategy")

    def test_kpi_recommendations_have_non_fabricated_targets(self) -> None:
        kpis = recommend_kpis("Lead generation", ["Email"], False, False)
        validate_structured_output(kpis, "kpi_recommendations")
        self.assertTrue(
            all(item["target_value"].startswith("Set after a baseline") for item in kpis)
        )


class CampaignExportTests(unittest.TestCase):
    def test_editing_validation_and_approval_preserve_structured_content(self) -> None:
        edited = {**PERSONA, "business_goals": ["Prioritize a validated business need"]}
        validate_structured_output(edited, "customer_persona")
        approved = approve_content(export_json(edited))
        self.assertEqual(
            get_approved_content({"persona": approved}, {"persona": True}, "persona"),
            edited,
        )

    def test_json_text_and_csv_campaign_exports(self) -> None:
        campaign = {"persona": PERSONA, "posts": [{"post_body": "Example copy"}]}
        self.assertIn('"persona_name": "Technology executive"', export_json(campaign))
        self.assertIn("Business Goals", export_text(campaign))
        csv_export = export_campaign_csv(campaign)
        rows = list(csv.DictReader(io.StringIO(csv_export)))
        self.assertEqual(rows[0]["asset"], "persona")
        self.assertEqual(rows[1]["asset"], "posts")
        self.assertEqual(rows[1]["post_body"], "Example copy")


if __name__ == "__main__":
    unittest.main()
