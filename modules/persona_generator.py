"""Customer persona and positioning generators."""

from typing import Any

from modules.llm_client import generate_json
from modules.prompt_engine import apply_sample_tone, build_marketing_prompt


def generate_persona(
    industry: str,
    company_size: str,
    job_role: str,
    challenges: str,
    maturity: str,
    use_sample_mode: bool,
    tone: str = "professional",
) -> dict[str, Any]:
    sample = {
        "persona_name": f"{job_role} at a {company_size} {industry} organization",
        "role_and_influence": (
            "Illustrative business and technology stakeholder; buying authority must be "
            "validated for the specific account."
        ),
        "technology_adoption_maturity": maturity,
        "goals": [
            "Connect technology initiatives to measurable business priorities.",
            "Build a responsible, stakeholder-aligned path from evaluation to adoption.",
        ],
        "business_challenges": [item.strip() for item in challenges.splitlines() if item.strip()],
        "buying_triggers": [
            "A clearly prioritized business problem.",
            "A credible, reviewable proposal with evidence appropriate to the account.",
        ],
        "decision_criteria": [
            "Strategic fit and governance requirements.",
            "Evidence that can be validated with the organization.",
            "Implementation approach, stakeholder alignment, and commercial fit.",
        ],
        "messaging_guidance": [
            "Lead with the stakeholder's stated challenge rather than unverified product claims.",
            "Use discovery questions to qualify priorities and evaluation criteria.",
        ],
        "assumptions": [
            "This is a hypothetical persona created for portfolio demonstration.",
            "Role influence, buying triggers, and priorities require account-level research.",
        ],
    }
    task = (
        "Create one evidence-conscious, hypothetical enterprise buyer persona. "
        "Return a JSON object with keys persona_name, role_and_influence, goals (array), "
        "business_challenges (array), buying_triggers (array), decision_criteria (array), "
        "messaging_guidance (array), assumptions (array). "
        f"Industry: {industry}. Company size: {company_size}. Job role: {job_role}. "
        f"Stated business challenges: {challenges}. Technology adoption maturity: {maturity}. "
        "Separate user-provided facts from assumptions. Do not claim that research was performed."
    )
    prompt = build_marketing_prompt(
        "Customer persona",
        task,
        industry,
        job_role,
        challenges,
        tone,
        additional_context=(
            f"Company size: {company_size}. Technology adoption maturity: {maturity}."
        ),
    )
    result = generate_json(prompt, sample, use_sample_mode)
    return apply_sample_tone(result, tone) if use_sample_mode else result


def generate_value_proposition(
    industry: str,
    company_size: str,
    job_role: str,
    challenges: str,
    solution_name: str,
    campaign_goal: str,
    use_sample_mode: bool,
    tone: str = "professional",
) -> dict[str, Any]:
    sample = {
        "positioning_statement": (
            f"For {job_role} stakeholders in {industry}, {solution_name} is the illustrative "
            "solution in this campaign concept for exploring how AI may relate to stated "
            "business priorities. Specific fit and capabilities require validation."
        ),
        "value_propositions": [
            "Frame an exploratory discussion around the organization's stated priorities.",
            "Give stakeholders a structured starting point for evaluating potential relevance.",
        ],
        "differentiators": [
            "No product differentiator is asserted; validate approved product facts before use."
        ],
        "messaging_framework": {
            "audience": f"{job_role} in a {company_size} {industry} organization",
            "problem": challenges,
            "message": "Start with the business challenge; explore solution fit through discovery.",
            "proof_points_to_validate": [
                "Approved product capabilities and scope",
                "Customer evidence cleared for external use",
                "Security, compliance, and implementation details for the target account",
            ],
            "call_to_action": campaign_goal,
        },
        "assumptions": [
            "Hypothetical campaign messaging for portfolio demonstration.",
            "No product capability, customer result, or competitive advantage is claimed.",
        ],
    }
    task = (
        "Develop an evidence-conscious B2B messaging framework. Return a JSON object with keys "
        "positioning_statement (string), value_propositions (array), differentiators (array), "
        "messaging_framework (object with audience, problem, message, proof_points_to_validate "
        "array, call_to_action), assumptions (array). "
        f"Illustrative solution name: {solution_name}. Industry: {industry}. "
        f"Company size: {company_size}. Buyer role: {job_role}. Stated challenges: {challenges}. "
        f"Campaign goal: {campaign_goal}. "
        "Do not infer capabilities or differentiators from the solution name. Phrase unverified "
        "benefits as hypotheses and identify evidence that must be validated."
    )
    prompt = build_marketing_prompt(
        "Value proposition",
        task,
        industry,
        job_role,
        challenges,
        tone,
        additional_context=(
            f"Company size: {company_size}. Illustrative solution: {solution_name}. "
            f"Campaign goal: {campaign_goal}."
        ),
    )
    result = generate_json(prompt, sample, use_sample_mode)
    return apply_sample_tone(result, tone) if use_sample_mode else result
