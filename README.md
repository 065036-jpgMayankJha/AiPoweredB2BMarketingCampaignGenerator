# AI-Powered B2B Marketing Campaign & Content Generator

A Streamlit portfolio project showing how an enterprise technology marketing team could plan and draft a targeted B2B campaign for BFSI audiences.

> **Important:** HCLTech AI Force is included only as an illustrative solution name. The personas, campaign copy, calendar, and CSV records are hypothetical. This project does not assert HCLTech product capabilities, customer results, certifications, or performance claims. Validate product facts, approvals, privacy requirements, and account details before any external use.

## Features

- Customer persona and value proposition generators
- Three LinkedIn approaches: thought leadership, educational, and promotional
- Personalized outreach sequence with two follow-ups
- Sales pitch, executive summary, FAQs, and objection-handling suggestions
- Thirty-day channel and content calendar
- Objective-based KPI recommendations with measurement guardrails
- Structured, industry-aware prompts with professional, consultative, and thought-leadership tones
- Account-based messaging for multiple user-supplied target accounts
- Channel, campaign objective, CTA, and awareness/consideration/conversion recommendations
- Transparent six-dimension editorial quality assessment (not campaign performance)
- Human edit/approval workflow; generated TXT/CSV exports are available only after approval
- Interactive B2B campaign performance dashboard with date and campaign filters
- Simulated campaign dataset with 144 records across 24 months, six channels, five industries, five campaign types, and four objectives
- Funnel, monthly, channel, industry, spend/leads, content engagement, and MQL-to-SQL visualizations
- Filtered campaign and KPI summary CSV reports; optional ROI based only on an explicit simulated revenue assumption
- Sample mode that works without an API key
- Configurable OpenAI-compatible chat-completions endpoint
- TXT and CSV downloads for generated content
- Hypothetical campaign data visualization using Plotly

## Project layout

```text
app.py
config.py
modules/
  __init__.py
  analytics.py
  campaign_planner.py
  prompt_engine.py
  account_based_marketing.py
  campaign_intelligence.py
  content_quality.py
  approval_workflow.py
  campaign_dashboard.py
  content_generator.py
  llm_client.py
  persona_generator.py
data/
  campaign_data.csv
  campaign_performance_simulated.csv
tests/
  test_advanced_marketing.py
reports/
  project_report.docx
  presentation.pptx
requirements.txt
.env.example
.gitignore
```

## Run locally

Python 3.10 or later is recommended.

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The app opens in sample mode by default. All workspaces produce deterministic sample content without sending data to an external service.

The **Campaign performance dashboard** uses `data/campaign_performance_simulated.csv`, a reproducible 144-record synthetic dataset spanning 24 months. Records include impressions, clicks, engagements, leads, MQLs, SQLs, campaign expenditure, partially observed simulated acquisitions, and explicitly simulated opportunity pipeline influence. All records are flagged as simulated demonstration data. Dashboard filters cover date, industry, channel, campaign type, and objective. CTR, engagement rate, lead conversion rate, CPL, and CPA use aggregate numerators and denominators; zero denominators are shown as unavailable. ROI remains hidden unless a positive user-entered simulated revenue assumption is provided, and is labeled as hypothetical. Filtered dataset and KPI summary CSV exports are available.

The advanced workspaces include Account-Based Marketing and Campaign Intelligence. Add accounts on separate lines using `Account name | industry | challenge`; industry and challenge are optional. The edit-and-approve workflow applies to generated content, including KPI recommendations and the campaign calendar. Only the currently approved draft can be downloaded.

Content quality scores use transparent text heuristics to support human editorial review. They are labeled AI-assisted assessments, do not verify factual accuracy, and do not predict campaign results. Scores should be reviewed alongside the draft and verified product evidence.

## Configure live generation

1. Copy `.env.example` to `.env`.
2. Set `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` for an OpenAI-compatible chat-completions API.
3. Keep `LLM_PROVIDER=openai_compatible`, then turn off sample mode in the sidebar.

`LLM_BASE_URL` is the API root (for example, `https://api.openai.com/v1`); the client appends `/chat/completions`. Never commit `.env` or paste confidential customer data into a third-party model. Provider usage, retention, and data processing terms should be reviewed before live use.

## KPI and data notes

The KPI engine recommends measures based on the selected objective and whether paid spend or CRM attribution can be measured. Definitions, baselines, targets, and attribution rules must be agreed with the organization; recommendations are not benchmarks. The sample CSV is fabricated and labeled as hypothetical, not actual campaign performance.

## Portfolio assets

- `reports/project_report.docx` summarizes the concept, architecture, safeguards, and evaluation approach.
- `reports/presentation.pptx` is a concise interview presentation for the project.

Both assets are illustrative portfolio materials and make no claims about HCLTech AI Force.

Run the focused automated tests with:

```bash
python -m unittest discover -s tests -v
```
