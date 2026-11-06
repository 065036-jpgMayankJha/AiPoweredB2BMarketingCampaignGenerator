"""LinkedIn, email, and sales enablement content generators."""

from typing import Any

from modules.llm_client import generate_json
from modules.prompt_engine import apply_sample_tone, build_marketing_prompt


def generate_linkedin_posts(
    industry: str,
    job_role: str,
    challenges: str,
    solution_name: str,
    campaign_goal: str,
    use_sample_mode: bool,
    tone: str = "professional",
) -> list[dict[str, Any]]:
    sample = [
        {
            "approach": "Thought leadership",
            "hook": "In enterprise AI, the most useful first question may be a business one.",
            "body": (
                f"For {industry} leaders such as a {job_role}, a grounded conversation starts "
                f"with the stated challenge: {challenges}. From there, teams can agree which "
                "business question and evaluation criteria merit further discovery."
            ),
            "call_to_action": "What business question is shaping your AI agenda?",
            "hashtags": ["B2BMarketing", "EnterpriseAI", "BFSI"],
            "assumptions": ["Hypothetical campaign copy; validate before publication."],
        },
        {
            "approach": "Educational",
            "hook": "A practical checklist for evaluating an enterprise AI opportunity.",
            "body": (
                f"For a {job_role} audience in {industry}, start with the challenge "
                f"'{challenges}'. Clarify affected stakeholders, define how success would be "
                "measured, and confirm governance and evidence requirements before evaluation."
            ),
            "call_to_action": "Save this checklist for your next discovery conversation.",
            "hashtags": ["AIReadiness", "BFSI", "DigitalStrategy"],
            "assumptions": ["Checklist is general guidance, not product-specific advice."],
        },
        {
            "approach": "Promotional",
            "hook": "Exploring AI priorities in financial services?",
            "body": (
                f"Consider a discovery conversation about your priorities and how {solution_name} "
                "may fit. Specific capabilities and suitability should be confirmed with approved "
                "product information and your organization's requirements."
            ),
            "call_to_action": campaign_goal,
            "hashtags": ["FinancialServices", "EnterpriseTechnology", "AI"],
            "assumptions": ["Promotional concept; obtain product and brand approval before use."],
        },
    ]
    task = (
        "Create exactly three LinkedIn posts in a JSON array, one each for Thought leadership, "
        "Educational, and Promotional. Every object must have approach, hook, body, call_to_action, "
        "hashtags (array), and assumptions (array). "
        f"Industry: {industry}. Target role: {job_role}. Stated challenges: {challenges}. "
        f"Illustrative solution: {solution_name}. Campaign goal: {campaign_goal}. "
        "Keep professional B2B tone. Make no unsupported product, customer, or performance claims. "
        "Mark approval and validation needs in assumptions."
    )
    prompt = build_marketing_prompt(
        "LinkedIn content",
        task,
        industry,
        job_role,
        challenges,
        tone,
        additional_context=f"Illustrative solution: {solution_name}. Campaign goal: {campaign_goal}.",
    )
    result = generate_json(prompt, sample, use_sample_mode)
    if not isinstance(result, list) or len(result) != 3:
        raise ValueError("LinkedIn generation must return exactly three posts.")
    return apply_sample_tone(result, tone) if use_sample_mode else result


def generate_email_campaign(
    industry: str,
    job_role: str,
    challenges: str,
    solution_name: str,
    campaign_goal: str,
    use_sample_mode: bool,
    tone: str = "professional",
) -> list[dict[str, Any]]:
    sample = [
        {
            "step": "Initial outreach",
            "timing": "Day 1",
            "subject_line": "A question about your AI priorities",
            "value_proposition": (
                "Compare your stated priorities with a structured discovery discussion; no "
                "capability or outcome is assumed."
            ),
            "email_body": (
                f"Hello {{First name}},\n\nI am reaching out because teams in {industry} may be "
                "reviewing how AI relates to their business priorities. You noted that "
                f"{challenges}. Would a short conversation about your evaluation criteria be "
                "useful? We can also determine whether learning more about {solution_name} is "
                "relevant to your context.\n\nBest,\n{{Sender name}}"
            ),
            "call_to_action": campaign_goal,
            "assumptions": ["Personalize with verified account context before sending."],
        },
        {
            "step": "Follow-up",
            "timing": "Day 5",
            "subject_line": "Re: A question about your AI priorities",
            "value_proposition": "Offer a concise, relevant next step based on the recipient's reply.",
            "email_body": (
                "Hello {First name},\n\nFollowing up in case this is timely. If AI evaluation "
                "is on your agenda, I would be glad to understand the business challenge and "
                "what evidence your team would need to assess potential fit. If another colleague "
                "owns this topic, please feel free to point me in the right direction.\n\nBest,\n"
                "{Sender name}"
            ),
            "call_to_action": "Reply with a suitable time or the right contact.",
            "assumptions": ["Send only where consent, policy, and contact rules permit."],
        },
        {
            "step": "Final follow-up",
            "timing": "Day 12",
            "subject_line": "Should I close the loop?",
            "value_proposition": "Make it easy to defer or redirect the conversation.",
            "email_body": (
                "Hello {First name},\n\nI will close the loop for now. If reviewing AI priorities "
                "becomes relevant, I would welcome a conversation focused on your requirements "
                "and evaluation criteria. No response is needed if the timing is not right.\n\n"
                "Best,\n{Sender name}"
            ),
            "call_to_action": "Let me know if a later conversation would be useful.",
            "assumptions": ["Stop outreach when requested and follow applicable policies."],
        },
    ]
    task = (
        "Create a compliant, personalized B2B outreach sequence with exactly three emails: "
        "initial outreach, follow-up, and final follow-up. Return a JSON array; every object must "
        "contain step, timing, subject_line, value_proposition, email_body, call_to_action, "
        "assumptions. Use placeholders such as {First name} and {Sender name}. "
        f"Industry: {industry}. Buyer role: {job_role}. Stated challenges: {challenges}. "
        f"Illustrative solution: {solution_name}. Campaign goal: {campaign_goal}. "
        "Do not claim product capabilities or guaranteed outcomes. Avoid fabricated personalization. "
        "Include respectful opt-out and policy reminders in assumptions."
    )
    prompt = build_marketing_prompt(
        "Email campaign",
        task,
        industry,
        job_role,
        challenges,
        tone,
        additional_context=f"Illustrative solution: {solution_name}. Campaign goal: {campaign_goal}.",
    )
    result = generate_json(prompt, sample, use_sample_mode)
    if not isinstance(result, list) or len(result) != 3:
        raise ValueError("Email generation must return an initial email and two follow-ups.")
    return apply_sample_tone(result, tone) if use_sample_mode else result


def generate_sales_enablement(
    industry: str,
    job_role: str,
    challenges: str,
    solution_name: str,
    campaign_goal: str,
    use_sample_mode: bool,
    tone: str = "professional",
) -> dict[str, Any]:
    sample = {
        "executive_summary": (
            f"Illustrative discussion brief for {job_role} stakeholders in {industry}: begin "
            f"with the stated challenge ({challenges}), establish evaluation criteria, and determine "
            f"whether a conversation about {solution_name} is relevant. This is not a product claim."
        ),
        "sales_pitch": (
            f"Rather than assume fit, start with your stated challenge ({challenges}) and "
            "understand your priorities and how you evaluate "
            f"AI opportunities. If useful, we can explore whether {solution_name} merits a closer "
            "look using approved product information and your requirements."
        ),
        "faqs": [
            {
                "question": "What capabilities are included?",
                "answer": (
                    "Confirm the current, approved product documentation with the product team; "
                    "this portfolio example does not assert capabilities."
                ),
            },
            {
                "question": "What outcomes can we expect?",
                "answer": (
                    "Do not promise an outcome. Define success measures with the customer and "
                    "validate any evidence cleared for external use."
                ),
            },
            {
                "question": "How should we evaluate fit?",
                "answer": (
                    "Align on the business problem, stakeholders, governance, evidence needs, "
                    "and decision criteria before discussing a next step."
                ),
            },
        ],
        "objection_handling": [
            {
                "objection": "We already have an AI strategy.",
                "response": (
                    "Acknowledge the work already done and ask where evaluation or execution "
                    "support remains a priority."
                ),
                "suggested_follow_up": "Which priorities are most important to validate this quarter?",
            },
            {
                "objection": "We need proof before considering a discussion.",
                "response": (
                    "Agree that evidence matters. Offer only approved, relevant materials and "
                    "be clear about what has not yet been validated."
                ),
                "suggested_follow_up": "What evidence and review criteria would your team require?",
            },
        ],
        "assumptions": [
            "Hypothetical sales enablement content, not approved product collateral.",
            "Validate all solution, security, compliance, and customer references before use.",
        ],
    }
    task = (
        "Create an evidence-led enterprise sales enablement pack. Return JSON with keys "
        "executive_summary, sales_pitch, faqs (array of question/answer objects), "
        "objection_handling (array of objection/response/suggested_follow_up objects), "
        "assumptions (array). "
        f"Industry: {industry}. Buyer role: {job_role}. Stated challenges: {challenges}. "
        f"Illustrative solution: {solution_name}. Campaign goal: {campaign_goal}. "
        "Avoid unsupported claims, customer evidence, guarantees, or invented features. "
        "For unknown product questions, explicitly direct the seller to approved sources."
    )
    prompt = build_marketing_prompt(
        "Sales enablement",
        task,
        industry,
        job_role,
        challenges,
        tone,
        additional_context=f"Illustrative solution: {solution_name}. Campaign goal: {campaign_goal}.",
    )
    result = generate_json(prompt, sample, use_sample_mode)
    return apply_sample_tone(result, tone) if use_sample_mode else result
