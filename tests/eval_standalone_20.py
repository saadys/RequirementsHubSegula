"""
Standalone 20-Case Benchmark Runner for the 5-Pillar LangGraph Engine
Directly evaluates all 20 cases using tests/standalone_evaluator_tk.py without requiring FastAPI or Docker.
"""

import json
import time
import os
import sys
sys.path.insert(0, os.path.abspath("."))

from tests.standalone_evaluator_tk import (
    pipeline_app,
    init_rag,
    PipelineState
)
from tests.run_20_cases import CASES

def run_benchmark():
    print("=" * 100)
    print("🚀 RUNNING 20-CASE BENCHMARK ON STANDALONE 5-PILLAR EVALUATION ENGINE")
    print("=" * 100)
    
    init_rag()
    
    results = []
    
    for i, item in enumerate(CASES, 1):
        case_id = item["case_id"]
        name = item["case_name"]
        form = item["form"]
        expected = item["expected"]
        
        print(f"\n[{i:2d}/20] Evaluating Case {case_id}: {name}...")
        start_t = time.time()
        
        state_input: PipelineState = {
            "form_data": form,
            "max_rag_score": 0.0,
            "best_matching_project": None,
            "facts": None,
            "score": 0,
            "sub_scores": {},
            "veto_triggered": False,
            "veto_reasons": [],
            "decision": "",
            "clarification_round": 0,
            "clarification_questions": [],
            "clarification_answers": [],
            "final_report": "",
        }
        
        try:
            res = pipeline_app.invoke(state_input)
            duration = time.time() - start_t
            
            facts = res.get("facts")
            decision = res.get("decision")
            score = res.get("score")
            rag_score = res.get("max_rag_score", 0.0)
            sub_scores = res.get("sub_scores", {})
            veto_reasons = res.get("veto_reasons", [])
            questions = res.get("clarification_questions", [])
            
            # Format output
            cat_ai = facts.ai_viability.category if facts else "N/A"
            cat_data = facts.data_readiness.category if facts else "N/A"
            cat_clarity = facts.problem_clarity.category if facts else "N/A"
            cat_integ = facts.integration_feasibility.category if facts else "N/A"
            cat_gov = facts.governance_and_safety.category if facts else "N/A"
            
            print(f"      Decision: {decision:18s} | Score: {score:3d}/100 | RAG: {rag_score*100:.1f}% | Time: {duration:.2f}s")
            print(f"      Pillars: AI={cat_ai}, Data={cat_data}, Clarity={cat_clarity}, Integ={cat_integ}, Gov={cat_gov}")
            if veto_reasons:
                print(f"      🚨 Vetoes: {veto_reasons}")
            if questions:
                print(f"      ❓ Questions Generated: {len(questions)}")
                
            results.append({
                "case_id": case_id,
                "case_name": name,
                "expected": expected,
                "decision": decision,
                "score": score,
                "rag_score": round(rag_score, 4),
                "sub_scores": sub_scores,
                "pillars": {
                    "ai_viability": cat_ai,
                    "data_readiness": cat_data,
                    "problem_clarity": cat_clarity,
                    "integration": cat_integ,
                    "governance": cat_gov,
                },
                "veto_reasons": veto_reasons,
                "questions_count": len(questions),
                "duration_s": round(duration, 2)
            })
            
        except Exception as e:
            print(f"      ❌ ERROR: {e}")
            results.append({
                "case_id": case_id,
                "case_name": name,
                "expected": expected,
                "error": str(e)
            })
            
    print("\n" + "=" * 100)
    print("📊 BENCHMARK SUMMARY TABLE")
    print("=" * 100)
    print(f"{'#':2s} | {'Case Name':30s} | {'Expected':20s} | {'Actual Decision':18s} | {'Score':5s} | {'RAG':6s} | {'Veto':4s}")
    print("-" * 100)
    
    for r in results:
        if "error" in r:
            print(f"{r['case_id']:2d} | {r['case_name']:30s} | {r['expected']:20s} | ERROR              | N/A   | N/A    | N/A")
        else:
            veto_str = "YES" if r["veto_reasons"] else "NO"
            print(f"{r['case_id']:2d} | {r['case_name'][:30]:30s} | {r['expected'][:20]:20s} | {r['decision'][:18]:18s} | {r['score']:3d}   | {r['rag_score']*100:4.1f}% | {veto_str:4s}")
            
    with open("tests/benchmark_standalone_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Full JSON results saved to tests/benchmark_standalone_results.json")

if __name__ == "__main__":
    run_benchmark()
