"""Focused tests for enterprise marketing features and approval safeguards."""

import unittest

from modules.account_based_marketing import (
    generate_account_strategies,
    parse_target_accounts,
)
from modules.approval_workflow import (
    approve_content,
    get_approved_content,
    parse_edited_content,
    serialize_content,
)
from modules.campaign_intelligence import recommend_campaign_intelligence
from modules.content_generator import generate_linkedin_posts
from modules.content_quality import SCORE_LABEL, evaluate_content
from modules.prompt_engine import apply_sample_tone, build_marketing_prompt


class PromptEngineTests(unittest.TestCase):
    def test_prompt_contains_industry_persona_challenge_and_tone(self) -> None:
        prompt = build_marketing_prompt(
            "Email",
            "Draft an email.",
            "BFSI",
            "CIO",
            "AI governance",
            "consultative",
        )
        self.assertIn("governance", prompt.lower())
        self.assertIn("CIO", prompt)
        self.assertIn("AI governance", prompt)
        self.assertIn("collaborative", prompt)
        self.assertIn("Do not invent product capabilities", prompt)

    def test_sample_tones_change_demo_content(self) -> None:
        sample = [{"hook": "A useful thought.", "call_to_action": "Explore the topic"}]
        consultative = apply_sample_tone(sample, "consultative")
        thought_leadership = apply_sample_tone(sample, "thought leadership")
        self.assertTrue(consultative[0]["call_to_action"].endswith("?"))
        self.assertTrue(thought_leadership[0]["hook"].startswith("A perspective:"))


class AccountBasedMarketingTests(unittest.TestCase):
    def test_parse_multiple_accounts_and_optional_context(self) -> None:
        accounts = parse_target_accounts(
            "Northstar | Banking | Review AI priorities\nCedar Mutual | Insurance"
        )
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0]["challenge"], "Review AI priorities")
        self.assertEqual(accounts[1]["industry"], "Insurance")

    def test_reject_duplicate_and_empty_accounts(self) -> None:
        with self.assertRaises(ValueError):
            parse_target_accounts("Northstar\nnorthstar")
        with self.assertRaises(ValueError):
            parse_target_accounts(" \n # example")

    def test_sample_strategy_is_account_specific(self) -> None:
        results = generate_account_strategies(
            "Northstar | Banking | Modernizing discovery\nCedar | Insurance | Evaluating workflows",
            "CIO",
            "Shared challenge",
            "Illustrative solution",
            "Start a discovery conversation",
            "professional",
        )
        self.assertEqual(len(results), 2)
        self.assertIn("Northstar", results[0]["account_message"])
        self.assertEqual(results[1]["industry"], "Insurance")
        self.assertIn("assumptions", results[0])


class CampaignIntelligenceTests(unittest.TestCase):
    def test_activities_cover_all_funnel_stages_and_channels_rank(self) -> None:
        result = recommend_campaign_intelligence(
            "BFSI",
            "CIO",
            "Prioritize AI",
            "Start a discovery conversation",
        )
        self.assertEqual(result["priority_funnel_stage"], "Conversion")
        self.assertEqual(
            {activity["funnel_stage"] for activity in result["activities"]},
            {"Awareness", "Consideration", "Conversion"},
        )
        self.assertEqual(result["recommended_channels"][0]["channel"], "Email")

    def test_empty_channel_selection_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            recommend_campaign_intelligence("BFSI", "CIO", "Need", "Awareness", [])


class ContentQualityTests(unittest.TestCase):
    def test_quality_scores_are_labeled_and_cover_required_dimensions(self) -> None:
        result = evaluate_content(
            {
                "body": "CIO teams can assess AI priorities and business value.",
                "call_to_action": "Request a discovery conversation",
            },
            "Enterprise CIO",
            "AI priorities",
            ["Enterprise AI"],
        )
        self.assertEqual(result["label"], SCORE_LABEL)
        self.assertEqual(len(result["scores"]), 6)
        self.assertTrue(all(1 <= score["score"] <= 5 for score in result["scores"]))
        self.assertIn("not predict", result["methodology"])

    def test_possible_unverified_claims_are_flagged(self) -> None:
        result = evaluate_content(
            "Our proven platform guarantees a 40% improvement.",
            "CIO",
            "Efficiency",
        )
        factual_score = next(
            item["score"] for item in result["scores"] if item["dimension"] == "Factual grounding"
        )
        self.assertEqual(factual_score, 1)


class ApprovalWorkflowTests(unittest.TestCase):
    def test_edited_content_must_be_valid_and_approved_before_export(self) -> None:
        draft = {"message": "Draft"}
        approvals = {"campaign": False}
        drafts = {"campaign": draft}
        with self.assertRaises(ValueError):
            get_approved_content(drafts, approvals, "campaign")
        edited = approve_content(serialize_content({"message": "Reviewed"}))
        drafts["campaign"] = edited
        approvals["campaign"] = True
        self.assertEqual(
            get_approved_content(drafts, approvals, "campaign"),
            {"message": "Reviewed"},
        )

    def test_invalid_json_has_actionable_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid JSON"):
            parse_edited_content("{invalid")


class ExistingGeneratorToneTests(unittest.TestCase):
    def test_linkedin_sample_obeys_selected_tone(self) -> None:
        posts = generate_linkedin_posts(
            "BFSI",
            "CIO",
            "Prioritize AI",
            "Illustrative solution",
            "Start a discovery conversation",
            True,
            "thought leadership",
        )
        self.assertEqual(len(posts), 3)
        self.assertTrue(posts[0]["hook"].startswith("A perspective:"))
        self.assertEqual(posts[0]["content_tone"], "thought leadership")


if __name__ == "__main__":
    unittest.main()