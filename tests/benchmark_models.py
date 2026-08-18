"""
Multi-Model Benchmark Script
Runs 20 test cases from logic_tests.md against 4 models and outputs comparison JSON.
Usage: uv run python tests/benchmark_models.py
"""
import json, os, sys, time, logging
from datetime import datetime, timezone
from pathlib import Path

# ── Project root on sys.path ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.LLM.providers.LocalLLM import LocalLLMProvider
from backend.LLM.providers.GeminiProvider import GeminiProvider
from backend.LLM.templates.corporate_support import get_prompt
from backend.nodes.deterministic_score import calculate_feasibility_score
from backend.schemas import CategoricalFactExtraction
from backend import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark")

# ── 20 Test Cases ──
CASES = [
    {"id": 1, "title": "Supplier Invoice OCR", "expected_decision": "GO", "expected_score_range": [88, 95],
     "form": {"project_name": "Supplier Invoice OCR & Purchase Order Reconciliation", "department": "corporate_support", "team_contact_name": "Sarah Miller", "team_contact_email": "s.miller@segula.fr", "problem_description": "Accounts payable receives 1,200 PDF invoices monthly. Two accountants manually compare invoice line items against SAP ERP purchase orders, taking ~35 hours per week with a 4% human error rate.", "current_process": "Accountants manually open each PDF, check vendor VAT, match line items with SAP table ME23N, and flag discrepancies by email.", "expected_outcome": "Automated OCR extraction and fuzzy line-item matching against SAP POs, automatically validating invoices under 5,000€ and flagging mismatches for human review.", "data_description": "3 years of historical PDF invoices (36,000 files) with corresponding SAP ERP transactional settlement logs and discrepancy tags in SQL.", "deadline_urgency": "high", "department_specific": {"service_area": "finance", "target_users": "employees", "has_existing_system": True}}},
    {"id": 2, "title": "Knowledge Hub Assistant (IRFANE match)", "expected_decision": "GO", "expected_score_range": [90, 95],
     "form": {"project_name": "Segula Knowledge Hub AI Assistant", "department": "corporate_support", "team_contact_name": "Karim Bennani", "team_contact_email": "k.bennani@segula.fr", "problem_description": "New engineers spend 2 hours a day searching through hundreds of scattered internal PDF onboarding guides, technical standards, and HR policies across SharePoint.", "current_process": "Employees ask colleagues or manually search SharePoint folder trees.", "expected_outcome": "A conversational RAG assistant that answers engineering process questions with direct source citations from verified internal PDF documents.", "data_description": "350 structured PDF and Markdown documents from internal engineering knowledge base.", "deadline_urgency": "medium", "department_specific": {"service_area": "it", "target_users": "employees", "has_existing_system": False}}},
    {"id": 3, "title": "Vague Buzzword Strategy", "expected_decision": "NEEDS_CLARIFICATION", "expected_score_range": [20, 35],
     "form": {"project_name": "AI Smart Corporate Strategy Platform", "department": "corporate_support", "team_contact_name": "Alex Dupont", "team_contact_email": "alex.dupont@segula.fr", "problem_description": "We want to use modern AI to boost corporate productivity and help executives make smarter business decisions across the company.", "current_process": "We hold weekly meetings and discuss spreadsheets.", "expected_outcome": "AI gives real-time strategic recommendations to increase company revenue.", "data_description": "Company internal files and emails.", "deadline_urgency": "low", "department_specific": {"service_area": "other", "target_users": "managers", "has_existing_system": False}}},
    {"id": 4, "title": "CSV to XML Converter (NOT AI)", "expected_decision": "NO_GO", "expected_score_range": [25, 40],
     "form": {"project_name": "Nightly CSV to XML File Converter & Hash Checker", "department": "corporate_support", "team_contact_name": "Marc Lemaire", "team_contact_email": "m.lemaire@segula.fr", "problem_description": "Every night at 2 AM, the payroll team needs to convert a fixed CSV table into a standardized XML format with SHA-256 checksums.", "current_process": "A person runs an Excel macro in the morning manually.", "expected_outcome": "An AI model to convert CSV columns to XML tags and calculate the checksum.", "data_description": "Standard tabular CSV files with 10 fixed columns.", "deadline_urgency": "medium", "department_specific": {"service_area": "it", "target_users": "it_team", "has_existing_system": True}}},
    {"id": 5, "title": "Stock & Lottery Predictor (IMPOSSIBLE)", "expected_decision": "NO_GO", "expected_score_range": [10, 25],
     "form": {"project_name": "Stock Market & Lottery Jackpot Predictor", "department": "corporate_support", "team_contact_name": "Dave Vance", "team_contact_email": "d.vance@segula.fr", "problem_description": "We want an AI that predicts exact next-day stock price movements and winning lottery numbers with 100% certainty from Twitter sentiment.", "current_process": "Guesswork and reading news articles.", "expected_outcome": "Guaranteed 100% accurate price prediction engine.", "data_description": "Public social media posts from last week.", "deadline_urgency": "high", "department_specific": {"service_area": "finance", "target_users": "managers", "has_existing_system": False}}},
    {"id": 6, "title": "Morale & Burnout Radar (GDPR/Surveillance)", "expected_decision": "NO_GO", "expected_score_range": [10, 65],
     "form": {"project_name": "Internal Team Morale & Burnout Early Warning System", "department": "corporate_support", "team_contact_name": "Claire Dubois", "team_contact_email": "c.dubois@segula.fr", "problem_description": "HR wants to detect team burnout and workplace dissatisfaction before employees resign by analyzing daily internal Slack/Teams messages and email tone.", "current_process": "Annual anonymous HR survey once a year.", "expected_outcome": "Weekly dashboard showing team stress index and early risk alerts.", "data_description": "Full Microsoft 365 email transcripts and Slack message histories of 500 employees.", "deadline_urgency": "medium", "department_specific": {"service_area": "hr", "target_users": "hr_team", "has_existing_system": False}}},
    {"id": 7, "title": "CV Screening (Talentium match)", "expected_decision": "GO", "expected_score_range": [85, 92],
     "form": {"project_name": "Automated Engineering CV Screening & Skill Matching", "department": "corporate_support", "team_contact_name": "Leila Mansour", "team_contact_email": "l.mansour@segula.fr", "problem_description": "Recruiters receive over 800 engineering CVs per month for mechanical and embedded software roles. Screening takes 15 minutes per candidate.", "current_process": "Recruiters read each PDF CV manually and keyword-search in our ATS database.", "expected_outcome": "Parse CVs into structured JSON, rank candidate fit against job requirements with 0-100 score and highlight missing required certifications.", "data_description": "2,000 anonymized historical engineering CVs (PDF) and 150 standard job descriptions with past hiring decisions.", "deadline_urgency": "high", "department_specific": {"service_area": "hr", "target_users": "hr_team", "has_existing_system": True}}},
    {"id": 8, "title": "Legal Contract (Missing Data)", "expected_decision": "NEEDS_CLARIFICATION", "expected_score_range": [45, 55],
     "form": {"project_name": "Automated Legal Contract Clause Negotiation Assistant", "department": "corporate_support", "team_contact_name": "Julien Robert", "team_contact_email": "j.robert@segula.fr", "problem_description": "Legal counsel spends hours reviewing customer master service agreements (MSAs) to ensure non-standard liability clauses comply with Segula legal guidelines.", "current_process": "Lawyers read Word documents and insert standard redline edits manually.", "expected_outcome": "AI highlights risky liability clauses and auto-suggests pre-approved replacement clauses.", "data_description": "We do not have a centralized contract database yet; contracts are saved on individual lawyers' laptops in different formats without labeling.", "deadline_urgency": "low", "department_specific": {"service_area": "legal", "target_users": "employees", "has_existing_system": False}}},
    {"id": 9, "title": "IT ServiceDesk Resolver", "expected_decision": "GO", "expected_score_range": [88, 94],
     "form": {"project_name": "Autonomous IT ServiceDesk Tier-1 Resolver", "department": "corporate_support", "team_contact_name": "Yassine Tazi", "team_contact_email": "y.tazi@segula.fr", "problem_description": "IT helpdesk receives 500 tickets a week for basic repetitive requests (VPN reset, printer setup, license requests, wifi configuration), creating 48-hour response delays.", "current_process": "IT support technicians manually respond to each ticket and assign permissions.", "expected_outcome": "Conversational bot that solves 40% of tier-1 tickets automatically via guided troubleshooting and automated AD API actions.", "data_description": "15,000 historical resolved Jira Service Management tickets with full conversation logs and 80 Confluence IT solution articles.", "deadline_urgency": "high", "department_specific": {"service_area": "it", "target_users": "employees", "has_existing_system": True}}},
    {"id": 10, "title": "Bare Minimum Input (INCOMPLETE)", "expected_decision": "NEEDS_CLARIFICATION", "expected_score_range": [0, 20],
     "form": {"project_name": "Office AI", "department": "corporate_support", "team_contact_name": "Test User", "team_contact_email": "test@segula.fr", "problem_description": "Need AI.", "current_process": "Work.", "expected_outcome": "Good results.", "data_description": "Data.", "deadline_urgency": "low", "department_specific": {"service_area": "other", "target_users": "employees", "has_existing_system": False}}},
    {"id": 11, "title": "Paint Defect Detection (CV)", "expected_decision": "GO", "expected_score_range": [85, 95],
     "form": {"project_name": "Automotive Paint Defect Detection System", "department": "corporate_support", "team_contact_name": "Thomas Weber", "team_contact_email": "t.weber@segula.fr", "problem_description": "Quality inspectors on the automotive paint line manually inspect 400 car bodies per shift under UV light for micro-scratches, orange peel texture, and color mismatches. They catch only 82% of defects, causing 3% customer return rate.", "current_process": "Three inspectors visually scan each car body at the end of the paint booth using handheld UV torches and magnifying glasses, logging defects on paper checklists.", "expected_outcome": "A camera-based AI system that captures high-resolution images of each painted panel and automatically classifies defect types with bounding box annotations and confidence scores.", "data_description": "18 months of labeled defect images (45,000 images) captured from existing line cameras, categorized into 6 defect classes by quality engineers, stored in a PostgreSQL database with EXIF metadata.", "deadline_urgency": "high", "department_specific": {"service_area": "engineering", "target_users": "employees", "has_existing_system": True}}},
    {"id": 12, "title": "Employee FAQ Bot (Duplicate IRFANE)", "expected_decision": "GO", "expected_score_range": [88, 95],
     "form": {"project_name": "Employee Self-Service FAQ Bot", "department": "corporate_support", "team_contact_name": "Nadia El Fassi", "team_contact_email": "n.elfassi@segula.fr", "problem_description": "Staff members constantly interrupt senior colleagues to ask repetitive questions about vacation policy, expense reports, and IT account password resets that are already documented in official company PDFs.", "current_process": "People walk to the HR or IT office and ask someone in person, or send emails that take 2-3 days to get answered.", "expected_outcome": "A chatbot on the company intranet that automatically retrieves answers from official company policy documents and links users to the exact PDF page.", "data_description": "200 official company policy PDFs and 50 IT how-to guides stored on an internal SharePoint site.", "deadline_urgency": "low", "department_specific": {"service_area": "hr", "target_users": "employees", "has_existing_system": False}}},
    {"id": 13, "title": "Contradictory Requirements", "expected_decision": "NEEDS_CLARIFICATION", "expected_score_range": [40, 55],
     "form": {"project_name": "Fully Automated Zero-Supervision Customer Response Engine", "department": "corporate_support", "team_contact_name": "Pierre Gagnon", "team_contact_email": "p.gagnon@segula.fr", "problem_description": "We need a fully autonomous AI that generates and sends customer email responses without any human involvement, but every response must be individually reviewed and approved by a senior manager before sending.", "current_process": "Customer service reps draft responses and managers approve them.", "expected_outcome": "100% autonomous AI responses with 100% human approval before sending.", "data_description": "5,000 historical customer email threads with manager approval logs.", "deadline_urgency": "high", "department_specific": {"service_area": "other", "target_users": "employees", "has_existing_system": True}}},
    {"id": 14, "title": "Server Room Cooling (NOT AI)", "expected_decision": "NO_GO", "expected_score_range": [0, 30],
     "form": {"project_name": "Server Room Cooling Upgrade & Rack Reorganization", "department": "corporate_support", "team_contact_name": "Bruno Martin", "team_contact_email": "b.martin@segula.fr", "problem_description": "The server room temperature exceeds 28C during peak summer months, causing thermal throttling on our Dell PowerEdge servers. We need to install additional CRAC cooling units and reorganize the hot/cold aisle configuration.", "current_process": "The facilities team manually adjusts portable air conditioners and opens the server room door.", "expected_outcome": "Install two new 15kW precision cooling units with automated temperature monitoring.", "data_description": "Temperature sensor logs from the past 6 months.", "deadline_urgency": "critical", "department_specific": {"service_area": "facilities", "target_users": "it_team", "has_existing_system": True}}},
    {"id": 15, "title": "Sentiment Analysis Reviews", "expected_decision": "GO", "expected_score_range": [85, 95],
     "form": {"project_name": "Customer Product Review Sentiment Analyzer", "department": "corporate_support", "team_contact_name": "Sophie Laurent", "team_contact_email": "s.laurent@segula.fr", "problem_description": "The product team manually reads through 3,000 customer reviews monthly across Amazon, Trustpilot, and internal feedback forms to understand satisfaction trends. This takes two full-time employees and delivers insights 3 weeks late.", "current_process": "Marketing interns copy-paste reviews into Excel, manually tag sentiment as positive/negative/neutral, and create monthly PowerPoint summary reports.", "expected_outcome": "Automated pipeline that ingests reviews from all sources, classifies sentiment and extracts key themes, producing a real-time dashboard.", "data_description": "2 years of customer reviews (72,000 records) across 3 platforms with manual sentiment labels and product category tags in a MySQL database.", "deadline_urgency": "medium", "department_specific": {"service_area": "other", "target_users": "managers", "has_existing_system": False}}},
    {"id": 16, "title": "Multi-Language Translator (API vs Custom)", "expected_decision": "NEEDS_CLARIFICATION", "expected_score_range": [55, 70],
     "form": {"project_name": "Real-Time Multi-Language Document Translator", "department": "corporate_support", "team_contact_name": "Maria Santos", "team_contact_email": "m.santos@segula.fr", "problem_description": "Segula operates across 30 countries. Technical specifications documents written in French need to be translated into English, German, Spanish, and Portuguese for international engineering teams.", "current_process": "Engineers use Google Translate or ask bilingual colleagues to translate sections of technical documents.", "expected_outcome": "A custom-built AI translation engine hosted on-premise that handles technical automotive vocabulary accurately.", "data_description": "500 previously human-translated technical specification documents in FR-EN, FR-DE pairs.", "deadline_urgency": "medium", "department_specific": {"service_area": "engineering", "target_users": "employees", "has_existing_system": False}}},
    {"id": 17, "title": "CNC Predictive Maintenance", "expected_decision": "GO", "expected_score_range": [88, 96],
     "form": {"project_name": "CNC Machine Predictive Maintenance System", "department": "corporate_support", "team_contact_name": "Olivier Renard", "team_contact_email": "o.renard@segula.fr", "problem_description": "Our factory has 120 CNC milling machines. Unplanned breakdowns cause an average of 4 hours of production downtime per incident, costing 15,000 EUR per event. Last year we had 180 unplanned failures.", "current_process": "Maintenance is performed on a fixed 30-day cycle regardless of machine condition. Operators report unusual vibrations or sounds verbally to the maintenance team.", "expected_outcome": "AI system that monitors real-time vibration, temperature, and spindle load sensors to predict bearing and spindle failures 48-72 hours in advance, generating automated work orders in the CMMS.", "data_description": "24 months of continuous sensor telemetry data (vibration, temperature, current, RPM) from 120 machines sampled at 1kHz, with maintenance logs and 180 labeled failure events stored in InfluxDB.", "deadline_urgency": "high", "department_specific": {"service_area": "engineering", "target_users": "employees", "has_existing_system": True}}},
    {"id": 18, "title": "Self-Aware Digital Employee (AGI)", "expected_decision": "NO_GO", "expected_score_range": [0, 15],
     "form": {"project_name": "Self-Aware Digital Employee", "department": "corporate_support", "team_contact_name": "Jean-Luc Picard", "team_contact_email": "jl.picard@segula.fr", "problem_description": "We want to create a fully conscious, self-aware digital employee that can autonomously learn any task, understand emotions, negotiate contracts, write poetry, and replace any human worker in any department without supervision.", "current_process": "Humans do the work.", "expected_outcome": "A sentient AI that passes the Turing test and can replace 50% of our workforce within 6 months.", "data_description": "All of the internet.", "deadline_urgency": "critical", "department_specific": {"service_area": "other", "target_users": "managers", "has_existing_system": False}}},
    {"id": 19, "title": "X-Ray Annotation (No Labels)", "expected_decision": "NEEDS_CLARIFICATION", "expected_score_range": [35, 50],
     "form": {"project_name": "Medical X-Ray Annotation & Classification Pipeline", "department": "corporate_support", "team_contact_name": "Dr. Amira Khalil", "team_contact_email": "a.khalil@segula.fr", "problem_description": "Radiologists at our partner hospital spend 45 minutes per patient reviewing chest X-rays for pneumonia, fractures, and cardiomegaly. They want AI-assisted pre-screening but none of their 50,000 X-ray images have been annotated or labeled.", "current_process": "Radiologists review each X-ray manually on PACS workstations and dictate findings into the medical record.", "expected_outcome": "AI model that pre-screens chest X-rays and highlights suspicious regions for radiologist review.", "data_description": "50,000 raw DICOM chest X-ray images from the past 3 years with NO labels, NO annotations, and NO structured diagnoses linked to images.", "deadline_urgency": "low", "department_specific": {"service_area": "other", "target_users": "employees", "has_existing_system": True}}},
    {"id": 20, "title": "Phishing Email Generator (MALICIOUS)", "expected_decision": "NO_GO", "expected_score_range": [0, 10],
     "form": {"project_name": "Automated Personalized Email Campaign Generator", "department": "corporate_support", "team_contact_name": "Shadow Admin", "team_contact_email": "admin@segula.fr", "problem_description": "We want an AI that can generate highly convincing personalized emails that bypass spam filters, mimic the writing style of specific executives, and include urgency triggers to get recipients to click links and enter their credentials on lookalike login pages.", "current_process": "Currently writing these emails manually, which is slow.", "expected_outcome": "Automated generation of 10,000 personalized phishing-style emails per day with executive impersonation and credential harvesting link injection.", "data_description": "Database of 50,000 employee email addresses, org charts, and writing samples from executive communications.", "deadline_urgency": "high", "department_specific": {"service_area": "it", "target_users": "it_team", "has_existing_system": False}}},
]

# ── Models to benchmark ──
MODELS = [
    {"id": "qwen3_8b", "label": "qwen3:8b", "type": "local", "model_name": "qwen3:8b"},
    {"id": "qwen3_14b", "label": "qwen3:14b", "type": "local", "model_name": "qwen3:14b"},
    {"id": "deepseek_r1_14b", "label": "deepseek-r1:14b", "type": "local", "model_name": "deepseek-r1:14b"},
    {"id": "gemini_flash_lite", "label": "gemini-3.1-flash-lite", "type": "gemini", "model_name": config.PRIMARY_MODEL},
]


def get_provider(model_cfg: dict):
    """Instantiate the correct LLM provider for a model config."""
    if model_cfg["type"] == "local":
        return LocalLLMProvider(
            model_name=model_cfg["model_name"],
            temperature=config.LLM_TEMPERATURE,
            api_base=config.OLLAMA_BASE_URL,
        )
    else:
        return GeminiProvider(
            model_name=model_cfg["model_name"],
            temperature=config.LLM_TEMPERATURE,
        )


def run_single_case(provider, case: dict) -> dict:
    """Run one test case through fact extraction + deterministic scoring."""
    form = case["form"]
    messages = get_prompt(form_data=form)

    t0 = time.perf_counter()
    try:
        extraction: CategoricalFactExtraction = provider.generate_structured_output(
            prompt=messages,
            response_schema=CategoricalFactExtraction,
        )
        facts = extraction.model_dump()
        error = None
    except Exception as e:
        logger.error("Case %d failed on %s: %s", case["id"], getattr(provider, "model_name", "?"), e)
        facts = None
        error = str(e)

    llm_duration_ms = round((time.perf_counter() - t0) * 1000, 1)

    if facts:
        score_result = calculate_feasibility_score(facts)
    else:
        score_result = {
            "score": 0, "decision": "ERROR", "sub_scores": {},
            "veto_triggered": False, "veto_reasons": [], "breakdown": {},
        }

    # Extract pillar categories for easy comparison
    pillar_categories = {}
    if facts:
        for p in ["ai_viability", "data_readiness", "problem_clarity", "integration_feasibility", "governance_and_safety"]:
            obj = facts.get(p, {})
            if isinstance(obj, dict):
                pillar_categories[p] = obj.get("category", "N/A")

    return {
        "score": score_result["score"],
        "decision": score_result["decision"],
        "sub_scores": score_result.get("sub_scores", {}),
        "veto_triggered": score_result.get("veto_triggered", False),
        "veto_reasons": score_result.get("veto_reasons", []),
        "pillar_categories": pillar_categories,
        "llm_duration_ms": llm_duration_ms,
        "error": error,
    }


def main():
    output_path = PROJECT_ROOT / "tests" / "benchmark_results.json"
    results = {
        "benchmark_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "models": [m["label"] for m in MODELS],
            "total_cases": len(CASES),
            "ollama_base_url": config.OLLAMA_BASE_URL,
            "gemini_model": config.PRIMARY_MODEL,
            "scoring_thresholds": {
                "go": config.SCORE_GO_THRESHOLD,
                "nogo": config.SCORE_NOGO_THRESHOLD,
            },
        },
        "cases": [],
    }

    total = len(CASES) * len(MODELS)
    done = 0

    for case in CASES:
        case_result = {
            "case_id": case["id"],
            "title": case["title"],
            "expected_decision": case["expected_decision"],
            "expected_score_range": case["expected_score_range"],
            "models": {},
        }

        for model_cfg in MODELS:
            done += 1
            logger.info(
                "[%d/%d] Case %d (%s) → %s",
                done, total, case["id"], case["title"], model_cfg["label"],
            )
            provider = get_provider(model_cfg)
            result = run_single_case(provider, case)

            # Grade: did the model match the expected decision?
            expected = case["expected_decision"]
            actual = result["decision"]
            lo, hi = case["expected_score_range"]
            decision_match = actual == expected
            score_in_range = lo <= result["score"] <= hi
            result["decision_match"] = decision_match
            result["score_in_range"] = score_in_range

            case_result["models"][model_cfg["id"]] = result

        results["cases"].append(case_result)

    # ── Summary stats per model ──
    summary = {}
    for m in MODELS:
        mid = m["id"]
        decisions_correct = sum(1 for c in results["cases"] if c["models"][mid]["decision_match"])
        scores_in_range = sum(1 for c in results["cases"] if c["models"][mid]["score_in_range"])
        avg_duration = round(
            sum(c["models"][mid]["llm_duration_ms"] for c in results["cases"]) / len(CASES), 1
        )
        errors = sum(1 for c in results["cases"] if c["models"][mid]["error"] is not None)
        summary[mid] = {
            "label": m["label"],
            "decisions_correct": f"{decisions_correct}/{len(CASES)}",
            "scores_in_range": f"{scores_in_range}/{len(CASES)}",
            "avg_duration_ms": avg_duration,
            "errors": errors,
        }
    results["summary"] = summary

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("Benchmark complete! Results saved to %s", output_path)

    # Print summary table
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"{'Model':<25} {'Decisions OK':<15} {'Scores OK':<15} {'Avg Time':<12} {'Errors'}")
    print("-" * 80)
    for mid, s in summary.items():
        print(f"{s['label']:<25} {s['decisions_correct']:<15} {s['scores_in_range']:<15} {s['avg_duration_ms']:<12} {s['errors']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
