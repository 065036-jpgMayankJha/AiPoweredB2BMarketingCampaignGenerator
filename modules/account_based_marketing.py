"""Account-based marketing message and outreach-strategy generation."""

from typing import Any

from modules.llm_client import generate_json
from modules.prompt_engine import apply_sample_tone, build_marketing_prompt


PERSONA_RECOMMENDATIONS = {
    "BFSI": [
        "Chief Information Officer",
        "Chief Technology Officer",
        "Chief Risk Officer",
        "Head of Operations",
        "Chief Data or Analytics Officer",
    ],
    "Banking": [
        "Chief Information Officer",
        "Chief Digital Officer",
        "Head of Banking Operations",
        "Chief Risk Officer",
    ],
    "Insurance": [
        "Chief Information Officer",
        "Chief Digital Officer",
        "Head of Claims or Operations",
        "Chief Risk Officer",
    ],
    "Capital markets": [
        "Chief Technology Officer",
        "Chief Information Officer",
        "Head of Operations",
        "Chief Risk Officer",
    ],
}


def parse_target_accounts(raw_accounts: str) -> list[dict[str, str]]:
    """Parse one account per line: account name | optional industry | optional challenge."""
    accounts: list[dict[str, str]] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(raw_accounts.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) > 3 or not parts[0]:
            raise ValueError(
                f"Account line {line_number} must be 'Account name | industry | challenge'."
            )
        key = parts[0].casefold()
        if key in seen:
            raise ValueError(f"Duplicate target account on line {line_number}: {parts[0]}.")
        seen.add(key)
        accounts.append(
            {
                "account": parts[0],
                "industry": parts[1] if len(parts) > 1 and parts[1] else "BFSI",
                "challenge": parts[2] if len(parts) > 2 else "",
            }
        )
    if not accounts:
        raise ValueError("Enter at least one target account, one account per line.")
    return accounts


def generate_account_strategies(
    raw_accounts: str,
    buyer_role: str,
    shared_challenges: str,
    solution_name: str,
    campaign_goal: str,
    tone: str = "professional",
    use_sample_mode: bool = True,
) -> list[dict[str, Any]]:
    """Create account-specific message hypotheses without implying account research."""
    accounts = parse_target_accounts(raw_accounts)
    results: list[dict[str, Any]] = []

    for account in accounts:
        industry = account["industry"]
        challenges = account["challenge"] or shared_challenges
        personas = PERSONA_RECOMMENDATIONS.get(
            industry, ["Chief Information Officer", "Chief Technology Officer", "Business sponsor"]
        )
        sample = {
            "account": account["account"],
            "industry": industry,
            "account_challenge": challenges or "Not provided; qualify in discovery.",
            "recommended_buyer_personas": personas,
            "account_message": (
                f"For {account['account']}, start a {tone} discovery conversation with "
                f"{buyer_role} stakeholders about the stated priority: "
                f"{challenges or 'the business priorities they identify'}. Treat {solution_name} "
                "as an illustrative topic only; confirm relevance and approved facts before use."
            ),
            "outreach_strategy": [
                f"Validate the account's stated priorities with a {personas[0]} stakeholder.",
                "Use a relevant, approved educational asset before proposing a meeting.",
                "Coordinate a respectful follow-up and stop if the recipient opts out.",
            ],
            "campaign_objective": campaign_goal,
            "call_to_action": "Would a short discovery conversation be useful?",
            "funnel_stage": "Consideration",
            "assumptions": [
                "Hypothetical account-specific message based only on user-entered context.",
                "No account research, product capability, or customer result is claimed.",
                "Validate buying roles, account facts, and approved product evidence before outreach.",
            ],
        }
        task = (
            "Create one account-based marketing recommendation. Return a JSON object with keys "
            "account, industry, account_challenge, recommended_buyer_personas (array), "
            "account_message, outreach_strategy (array), campaign_objective, call_to_action, "
            "funnel_stage, assumptions (array). "
            f"Target account name: {account['account']}. User-entered account industry: {industry}. "
            f"Illustrative solution name: {solution_name}. Campaign goal: {campaign_goal}. "
            "Recommend buyer roles as hypotheses, not confirmed account contacts. "
            "Personalize only using the account name, industry, and challenge supplied here."
        )
        prompt = build_marketing_prompt(
            "Account-based marketing",
            task,
            industry,
            buyer_role,
            challenges or "No account challenge supplied; discover before personalizing.",
            tone,
            additional_context=f"Target account: {account['account']}",
        )
        generated = generate_json(prompt, sample, use_sample_mode)
        if not isinstance(generated, dict):
            raise ValueError(f"Account strategy for {account['account']} must be a JSON object.")
        required_fields = {
            "account",
            "industry",
            "account_challenge",
            "recommended_buyer_personas",
            "account_message",
            "outreach_strategy",
            "campaign_objective",
            "call_to_action",
            "funnel_stage",
            "assumptions",
        }
        if not required_fields.issubset(generated):
            raise ValueError(
                f"Account strategy for {account['account']} is missing required fields."
            )
        if use_sample_mode:
            generated = apply_sample_tone(generated, tone)
        results.append(generated)
    return results
