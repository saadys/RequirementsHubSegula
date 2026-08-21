"""
End-to-End Local LLM Validation Script

Tests Ollama (qwen2.5:7b-instruct) integration:
1. Health check & direct structured output generation (FactExtraction)
2. Full LangGraph submission pipeline execution with USE_LOCAL_LLM=True
"""

import os
import sys
import time

# Enforce USE_LOCAL_LLM before importing config or services
os.environ["USE_LOCAL_LLM"] = "true"
os.environ["LOCAL_MODEL"] = "ollama/qwen3:8b"

from backend import config
config.USE_LOCAL_LLM = True
config.LOCAL_MODEL = "ollama/qwen3:8b"

from backend.LLM.providers.LocalLLM import LocalLLMProvider
from backend.LLM.LLMProviderFactory import LLMProviderFactory
from backend.schemas import FactExtraction
from backend.graph.builder import get_compiled_graph


async def run_e2e_local_llm_test():
    print("=" * 70)
    print("  REQUIREMENTS HUB SEGULA - END-TO-END LOCAL LLM (OLLAMA) TEST")
    print("=" * 70)
    print(f"Model: {config.LOCAL_MODEL}")
    print(f"Ollama URL: {config.OLLAMA_BASE_URL}")
    print(f"USE_LOCAL_LLM: {config.USE_LOCAL_LLM}")
    print("-" * 70)

    # -------------------------------------------------------------------------
    # STEP 1: Direct Provider Health Check & Structured Output
    # -------------------------------------------------------------------------
    print("\n[STEP 1] Testing LocalLLMProvider Health Check & Direct Structured Output...")
    provider = LocalLLMProvider(model_name=config.LOCAL_MODEL, temperature=0.0)

    t0 = time.time()
    is_healthy = provider.health_check()
    t_health = round((time.time() - t0) * 1000, 2)
    print(f"  -> Health check: {'SUCCESS' if is_healthy else 'FAILED'} ({t_health} ms)")

    if not is_healthy:
        print("[ERROR] CRITICAL: Local LLM service unreachable on http://localhost:11434")
        sys.exit(1)

    prompt = (
        "Un atelier de fabrication aeronautique souhaite utiliser l'IA et la vision par ordinateur "
        "pour detecter automatiquement les defauts de soudure sur des pieces d'avion en alliage titane. "
        "Ils ont accumule 50 000 images haute resolution annotees par leurs experts qualite sur 3 ans."
    )

    print("  -> Invoking generate_structured_output(FactExtraction)...")
    t0 = time.time()
    fact_result: FactExtraction = await provider.generate_structured_output(
        prompt=prompt,
        response_schema=FactExtraction
    )
    t_struct = round(time.time() - t0, 2)

    print(f"  -> Direct Extraction Completed in {t_struct}s")
    print(f"    - Clear Problem Statement: {fact_result.has_clear_problem_statement}")
    print(f"    - Problem AI Solvable: {fact_result.problem_is_ai_solvable}")
    print(f"    - Problem Category: {fact_result.problem_category}")
    print(f"    - Data Availability: {fact_result.data_availability}")
    print(f"    - AI Technique: {fact_result.ai_technique_identified}")
    print(f"    - Summary: {fact_result.summary}")

    # -------------------------------------------------------------------------
    # STEP 2: Full LangGraph End-to-End Pipeline
    # -------------------------------------------------------------------------
    print("\n[STEP 2] Executing Full LangGraph Pipeline with Qwen2.5:7b-instruct...")
    
    graph = get_compiled_graph()

    submission_state = {
        "form_data": {
            "project_name": "Inspection Qualite Soudure Titan-Vision",
            "department": "manufacturing",
            "team_contact_name": "Marc Dubois",
            "team_contact_email": "marc.dubois@segula.fr",
            "problem_description": (
                "Les controles visuels de soudures titane sont aujourd'hui realises a 100% manuellement par des inspecteurs certifies. "
                "Cela cree un goulot d'etranglement avec 45 minutes d'inspection par piece. "
                "Nous voulons un systeme IA de detection automatique des micro-fissures et meats de porosite pour reduire le temps a 5 minutes."
            ),
            "current_process": "Inspection manuelle au microscope et retro-eclairage par 2 inspecteurs mecatronique.",
            "expected_outcome": "Pre-detection automatique des zones suspectes sur images 4K avec un taux de rappel > 98%.",
            "data_description": "Base de donnees de 50 000 images 4K annotees avec masques de segmentation des defauts (porosite, fissure, manque de penetration).",
            "deadline_urgency": "high",
            "department_specific": {
                "production_site": "Usine Saint-Nazaire",
                "quality_standard": "ISO 9001 / EN 9100",
                "realtime_constraint": True
            }
        },
        "uploaded_files": [],
        "department": "manufacturing",
        "clarification_round": 0,
        "clarification_answers": []
    }

    t0 = time.time()
    result_state = await graph.ainvoke(submission_state)
    t_pipeline = round(time.time() - t0, 2)

    print("\n" + "=" * 70)
    print("  E2E PIPELINE EXECUTION RESULTS")
    print("=" * 70)
    print(f"Total Execution Time: {t_pipeline} seconds")
    print(f"Score: {result_state.get('score', 'N/A')} / 100")
    print(f"Decision: {result_state.get('decision', 'N/A')}")
    print(f"Report Type: {result_state.get('report_type', 'N/A')}")
    print(f"Is Fast Track: {result_state.get('is_exact_match', False)}")
    
    if result_state.get("score_breakdown"):
        print("\n--- Score Breakdown ---")
        for k, v in result_state.get("score_breakdown").items():
            print(f"  - {k}: {v}")

    report_content = result_state.get("report", "")
    print(f"\nReport Generated Length: {len(report_content)} characters")
    
    # Save generated report to file
    report_file = os.path.join(os.path.dirname(__file__), "generated_local_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Full report saved to: {report_file}")

    print("-" * 70)
    print("Extrait du Cahier des Charges Genere (1000 premiers caracteres) :")
    print("-" * 70)
    safe_preview = report_content[:1000].encode("ascii", "replace").decode("ascii")
    print(safe_preview + ("..." if len(report_content) > 1000 else ""))
    print("-" * 70)

    print("\n[SUCCESS] END-TO-END LOCAL LLM TEST COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_e2e_local_llm_test())
