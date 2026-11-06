"""Tests for the simulated campaign performance dashboard."""

import unittest

import pandas as pd

from modules.campaign_dashboard import (
    SIMULATED_LABEL,
    calculate_campaign_kpis,
    campaign_insights,
    filter_campaign_data,
    generate_simulated_campaign_data,
    load_simulated_campaign_data,
    safe_divide,
)


class SimulatedCampaignDataTests(unittest.TestCase):
    def test_dataset_has_at_least_100_simulated_records_across_dimensions(self) -> None:
        frame = load_simulated_campaign_data()
        self.assertGreaterEqual(len(frame), 100)
        self.assertTrue(frame["is_simulated_demo_data"].all())
        self.assertGreaterEqual(frame["channel"].nunique(), 5)
        self.assertGreaterEqual(frame["industry"].nunique(), 4)
        self.assertGreaterEqual(frame["campaign_type"].nunique(), 4)
        self.assertGreaterEqual(frame["campaign_objective"].nunique(), 4)
        self.assertGreaterEqual(frame["date"].dt.to_period("M").nunique(), 12)
        self.assertTrue(frame["data_source_label"].str.contains("SIMULATED DEMONSTRATION DATA").all())

    def test_data_generation_is_deterministic(self) -> None:
        first = generate_simulated_campaign_data(100)
        second = generate_simulated_campaign_data(100)
        pd.testing.assert_frame_equal(first, second)

    def test_dataset_is_visibly_labeled_simulated(self) -> None:
        self.assertIn("SIMULATED DEMONSTRATION DATA", SIMULATED_LABEL)


class CampaignFilterTests(unittest.TestCase):
    def test_filters_apply_date_and_each_campaign_dimension(self) -> None:
        frame = load_simulated_campaign_data()
        target = frame.iloc[0]
        result = filter_campaign_data(
            frame,
            target["date"].date(),
            target["date"].date(),
            [target["industry"]],
            [target["channel"]],
            [target["campaign_type"]],
            [target["campaign_objective"]],
        )
        self.assertGreaterEqual(len(result), 1)
        self.assertTrue((result["industry"] == target["industry"]).all())
        self.assertTrue((result["channel"] == target["channel"]).all())
        self.assertTrue((result["campaign_type"] == target["campaign_type"]).all())
        self.assertTrue((result["campaign_objective"] == target["campaign_objective"]).all())

    def test_invalid_date_range_is_rejected(self) -> None:
        frame = load_simulated_campaign_data()
        with self.assertRaises(ValueError):
            filter_campaign_data(frame, "2026-01-01", "2025-01-01")

    def test_explicitly_empty_filter_selection_returns_no_records(self) -> None:
        frame = load_simulated_campaign_data()
        result = filter_campaign_data(
            frame,
            frame["date"].min().date(),
            frame["date"].max().date(),
            channels=[],
        )
        self.assertTrue(result.empty)


class CampaignKpiTests(unittest.TestCase):
    def test_safe_divide_handles_zero_and_missing_denominators(self) -> None:
        self.assertIsNone(safe_divide(10, 0))
        self.assertIsNone(safe_divide(10, None))
        self.assertEqual(safe_divide(1, 4), 0.25)

    def test_kpis_use_aggregate_ratios_and_only_calculate_roi_on_request(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "impressions": 1000,
                    "clicks": 100,
                    "engagements": 200,
                    "leads": 10,
                    "mqls": 5,
                    "sqls": 2,
                    "campaign_expenditure_usd": 500,
                    "acquisitions": 1,
                    "simulated_pipeline_influence_usd": 20000,
                },
                {
                    "impressions": 3000,
                    "clicks": 300,
                    "engagements": 300,
                    "leads": 30,
                    "mqls": 15,
                    "sqls": 6,
                    "campaign_expenditure_usd": 1500,
                    "acquisitions": None,
                    "simulated_pipeline_influence_usd": 30000,
                },
            ]
        )
        kpis = calculate_campaign_kpis(frame)
        self.assertEqual(kpis["total_impressions"], 4000)
        self.assertEqual(kpis["total_clicks"], 400)
        self.assertAlmostEqual(kpis["ctr"], 0.1)
        self.assertAlmostEqual(kpis["engagement_rate"], 0.125)
        self.assertAlmostEqual(kpis["lead_conversion_rate"], 0.1)
        self.assertEqual(kpis["cost_per_lead_usd"], 50)
        self.assertAlmostEqual(kpis["cost_per_acquisition_usd"], 500)
        self.assertEqual(kpis["pipeline_influence_usd"], 50000)
        self.assertIsNone(kpis["roi_percent"])
        roi = calculate_campaign_kpis(frame, simulated_revenue_assumption=3000)
        self.assertAlmostEqual(roi["roi_percent"], 50)

    def test_zero_denominators_return_none_and_roi_requires_positive_revenue(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "impressions": 0,
                    "clicks": 0,
                    "engagements": 0,
                    "leads": 0,
                    "mqls": 0,
                    "sqls": 0,
                    "campaign_expenditure_usd": 0,
                    "acquisitions": None,
                    "simulated_pipeline_influence_usd": 0,
                }
            ]
        )
        kpis = calculate_campaign_kpis(frame)
        self.assertIsNone(kpis["ctr"])
        self.assertIsNone(kpis["engagement_rate"])
        self.assertIsNone(kpis["lead_conversion_rate"])
        self.assertIsNone(kpis["cost_per_lead_usd"])
        self.assertIsNone(kpis["cost_per_acquisition_usd"])
        self.assertIsNone(kpis["roi_percent"])
        with self.assertRaises(ValueError):
            calculate_campaign_kpis(frame, simulated_revenue_assumption=0)

    def test_empty_frame_returns_safe_kpi_values(self) -> None:
        kpis = calculate_campaign_kpis(load_simulated_campaign_data().iloc[0:0])
        self.assertEqual(kpis["total_impressions"], 0)
        self.assertIsNone(kpis["ctr"])
        self.assertIsNone(kpis["roi_percent"])

    def test_campaign_insights_are_explicitly_directional(self) -> None:
        insights = campaign_insights(load_simulated_campaign_data())
        self.assertGreaterEqual(len(insights), 4)
        self.assertTrue(any("simulated" in item.lower() for item in insights))
        self.assertTrue(any("not causal" in item.lower() for item in insights))


if __name__ == "__main__":
    unittest.main()
