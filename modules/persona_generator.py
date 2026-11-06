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
        "persona_name": f"{job_role} - {industry} - {company_size}",
        "job_title": job_role,
        "industry": industry,
        "company_size": company_size,
        "responsibilities": [
            "Coordinate business and technology stakeholders.",
            "Assess priorities and evaluation criteria.",
        ],
        "business_goals": [
            "Connect technology initiatives to measurable business priorities.",
            "Build a responsible, stakeholder-aligned path from evaluation to adoption.",
        ],
        "pain_points": [item.strip() for item in challenges.splitlines() if item.strip()]
        or ["Specific pain points were not provided; validate in discovery."],
        "buying_motivations": [
            "A clearly prioritized business problem.",
            "A credible, reviewable proposal with evidence appropriate to the account.",
        ],
        "decision_making_criteria": [
            "Strategic fit and governance requirements.",
            "Evidence that can be validated with the organization.",
            "Implementation approach, stakeholder alignment, and commercial fit.",
        ],
        "preferred_communication_channels": [
            "Professional email, where permitted and relevant.",
            "Educational LinkedIn content.",
            "Discovery conversations when invited.",
        ],
        "assumptions": ["Illustrative hypothesis; validate role priorities and preferences with research."],
        "technology_adoption_maturity": maturity,
    }
    task = (
        "Create one evidence-conscious, hypothetical enterprise buyer persona. Return a JSON "
        "object with persona_name, job_title, industry, company_size, responsibilities (array), "
        "business_goals (array), pain_points (array), buying_motivations (array), "
        "decision_making_criteria (array), preferred_communication_channels (array), and "
        "assumptions (array). "
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
    result = generate_json(prompt, sample, use_sample_mode, "customer_persona")
    return apply_sample_tone(result, tone) if use_sample_mode else result


def generate_icp(
    industry: str,
    company_size: str,
    revenue_range: str,
    geography: str,
    maturity: str,
    challenges: str,
    use_sample_mode: bool,
    tone: str = "professional",
) -> dict[str, Any]:
    """Generate an ideal customer profile using supplied context and explicit assumptions."""
    sample = {
        "target_industry": industry,
        "company_size": company_size,
        "revenue_range": revenue_range or "Not provided; qualify during discovery.",
        "geography": geography or "Not provided; qualify during discovery.",
        "technology_maturity": maturity,
        "business_challenges": [item.strip() for item in challenges.splitlines() if item.strip()]
        or ["Specific challenges were not provided; validate during discovery."],
        "qualification_criteria": [
            "A relevant business challenge is confirmed by the organization.",
            "Stakeholders and decision process are identified through discovery.",
            "Technology, governance, budget, and timing requirements are validated.",
        ],
        "assumptions": ["Hypothetical profile; company fit and qualification criteria require validation."],
    }
    task = (
        "Create a hypothetical ideal customer profile. Return a JSON object with target_industry, "
        "company_size, revenue_range, geography, technology_maturity, business_challenges (array), "
        "qualification_criteria (array), and assumptions (array). Use only supplied facts. "
        "Where revenue or geography is not supplied, state that it was not provided and should "
        "be qualified; do not infer company data. "
        f"Industry: {industry}. Company size: {company_size}. Revenue range: {revenue_range or 'not provided'}. "
        f"Geography: {geography or 'not provided'}. Technology maturity: {maturity}. "
        f"Business challenges: {challenges}."
    )
    prompt = build_marketing_prompt(
        "Ideal customer profile",
        task,
        industry,
        "Organization-level buying group",
        challenges,
        tone,
        additional_context=(
            f"Company size: {company_size}. Revenue range: {revenue_range or 'not provided'}. "
            f"Geography: {geography or 'not provided'}."
        ),
    )
    result = generate_json(prompt, sample, use_sample_mode, "ideal_customer_profile")
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
        "customer_problem": challenges or "Specific customer problem was not provided; validate during discovery.",
        "proposed_solution": (
            f"Explore whether {solution_name} is relevant to the stated priorities through "
            "discovery and approved product information."
        ),
        "core_value_proposition": (
            "Provide a structured starting point for evaluating the stated business challenge "
            "without assuming product fit or outcomes."
        ),
        "key_differentiators": [
            "No differentiator is asserted; compare only against approved, verifiable product facts."
        ],
        "business_benefits": [
            "Help stakeholders clarify evaluation criteria and evidence requirements.",
            "Support a more focused discussion of stated business priorities.",
        ],
        "supporting_evidence_or_assumptions": [
            "Hypothesis only; validate fit with the organization.",
            "Confirm approved capabilities, customer evidence, and implementation details before use.",
        ],
        "assumptions": [
            "Hypothetical campaign messaging.",
            "No product capability, customer result, or competitive advantage is claimed.",
        ],
        "target_audience": f"{job_role} in a {company_size} {industry} organization",
        "campaign_goal": campaign_goal,
    }
    task = (
        "Develop an evidence-conscious B2B value proposition. Return a JSON object with "
        "customer_problem, proposed_solution, core_value_proposition, key_differentiators "
        "(array), business_benefits (array), supporting_evidence_or_assumptions (array), and "
        "assumptions (array). "
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
    result = generate_json(prompt, sample, use_sample_mode, "value_proposition")
    return apply_sample_tone(result, tone) if use_sample_mode else result
