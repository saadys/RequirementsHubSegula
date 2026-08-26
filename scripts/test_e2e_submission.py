#!/usr/bin/env python
import json
import time
import urllib.request
import sys

# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

payload = {
    "project_name": "Automotive Predictive Maintenance AI",
    "department": "corporate_support",
    "team_contact_name": "Alexandre Dupont",
    "team_contact_email": "alexandre.dupont@segula.com",
    "problem_description": "High vibration and thermal drift on robotic welding arms cause 3 hours of unplanned stoppage weekly in production.",
    "current_process": "Technicians inspect arms manually once a week and replace parts only after breakdown.",
    "expected_outcome": "Real-time telemetry anomaly detection giving 4 hours advance warning on gearbox wear with >85% recall.",
    "data_description": "18 months of continuous IoT telemetry logs (accelerometer, thermal, motor torque) with 45 labeled breakdown events.",
    "deadline_urgency": "high",
    "department_specific": {
        "service_area": "it",
        "target_users": "it_team",
        "has_existing_system": True
    }
}

print("[TEST E2E] 1. Envoi de la soumission complète au portail frontend (http://localhost:5173/api/submissions/)...")
req = urllib.request.Request(
    "http://localhost:5173/api/submissions/",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        req_id = res.get("request_id") or res.get("id")
        print(f"   -> Dossier créé avec succès ! Request ID: {req_id} (Statut initial: {res.get('status')})")
except Exception as e:
    print(f"[ERREUR] Échec de la soumission: {e}")
    sys.exit(1)

print("\n[TEST E2E] 2. Suivi de l'analyse IA locale (Ollama qwen2.5:7b-instruct + RAG + Scoring)...")
completed = False
for i in range(40):
    time.sleep(2)
    poll_req = urllib.request.Request(f"http://localhost:5173/api/submissions/{req_id}")
    try:
        with urllib.request.urlopen(poll_req) as poll_resp:
            data = json.loads(poll_resp.read().decode())
            status = data.get("status")
            score = data.get("score")
            decision = data.get("decision")
            print(f"   [T+{(i+1)*2}s] Statut: {status:<12} | Score: {str(score):<4} | Décision: {decision}")
            if status == "COMPLETED":
                completed = True
                print("\n" + "=" * 70)
                print("  RÉSULTATS DE L'ÉVALUATION IA (Ollama Local)")
                print("=" * 70)
                print(f"  Décision Finale     : {decision}")
                print(f"  Score Global        : {score} / 100")
                print(f"  Sous-scores 5 Piliers:")
                sub_scores = data.get("sub_scores", {})
                for k, v in sub_scores.items():
                    print(f"    - {k:<25}: {v}")
                if data.get("report"):
                    print(f"\n  Extrait Rapport ({data.get('report_type')}):")
                    for line in data.get("report").splitlines()[:6]:
                        print(f"    {line}")
                print("=" * 70)
                print("[SUCCÈS] Le test E2E est validé à 100% !")
                break
    except Exception as e:
        print(f"   [Erreur Polling]: {e}")

if not completed:
    print("[TIMEOUT] L'analyse a pris plus de 80s.")
    sys.exit(1)
