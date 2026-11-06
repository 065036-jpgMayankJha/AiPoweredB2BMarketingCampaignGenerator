"""Streamlit interaction tests for generated marketing content."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class MarketingContentUITests(unittest.TestCase):
    def test_edit_approval_downloads_and_raw_json_default_visibility(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path), default_timeout=45).run()
        app.radio[0].set_value("Customer persona").run()
        next(
            button
            for button in app.button
            if button.label == "Generate customer persona"
        ).click().run()

        self.assertEqual(list(app.exception), [])
        raw_json = next(
            item for item in app.expander if item.label == "Advanced: View Raw JSON"
        )
        self.assertFalse(raw_json.proto.expanded)
        self.assertNotIn(
            "Download JSON",
            [item.proto.label for item in app.get("download_button")],
        )

        name_field = next(item for item in app.text_input if item.label == "Name")
        name_field.set_value("Edited persona hypothesis")
        next(
            button for button in app.button if button.label == "Save and approve"
        ).click().run()

        self.assertEqual(list(app.exception), [])
        self.assertEqual(
            app.session_state["marketing_drafts"]["persona_result"]["persona_name"],
            "Edited persona hypothesis",
        )
        download_labels = [item.proto.label for item in app.get("download_button")]
        self.assertIn("Download JSON", download_labels)
        self.assertIn("Download TXT", download_labels)
        self.assertIn("Download CSV", download_labels)
        self.assertIn("Download campaign JSON", download_labels)


if __name__ == "__main__":
    unittest.main()
