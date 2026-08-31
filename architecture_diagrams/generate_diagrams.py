"""
Segula AI Requirement Hub - Architecture Diagram Generator
Uses the Python 'diagrams' library to generate high-resolution architecture diagrams
with a clean, professional white background suitable for executive presentations.

Run with:
    uv run python architecture_diagrams/generate_diagrams.py
"""

import os
from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
from diagrams.onprem.client import Users
from diagrams.onprem.database import PostgreSQL

# Change to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# ==============================================================================
# Global Styling Theme (Enterprise Light / White Background)
# ==============================================================================
graph_attr_global = {
    "fontsize": "26",
    "fontname": "Arial, Helvetica, sans-serif",
    "bgcolor": "#ffffff",
    "fontcolor": "#0f172a",
    "pad": "0.8",
    "splines": "curved",
    "nodesep": "1.0",
    "ranksep": "1.8",
    "compound": "true",
    "concentrate": "false"
}

node_attr_global = {
    "fontname": "Arial, Helvetica, sans-serif",
    "fontsize": "12",
    "fontcolor": "#0f172a",
    "color": "#cbd5e1",
    "style": "filled",
    "fillcolor": "#f8fafc",
    "shape": "box"
}

edge_attr_global = {
    "fontname": "Arial, Helvetica, sans-serif",
    "fontsize": "10",
    "fontcolor": "#334155",
    "color": "#2563eb",
    "penwidth": "1.6"
}

# ==============================================================================
# Diagram 1: End-to-End Enterprise Sovereign Architecture
# ==============================================================================
print("🎨 Generating Diagram 1: End-to-End Enterprise Architecture (White Background)...")

with Diagram(
    "Segula AI Requirement Hub - End-to-End Sovereign Enterprise Architecture",
    filename="segula_ai_hub_architecture",
    show=False,
    direction="LR",
    graph_attr=graph_attr_global,
    node_attr=node_attr_global,
    edge_attr=edge_attr_global
):
    users = Users("Segula Engineers\n& Department Leads\n(Web Portal)")

    # 1. CI/CD Cluster
    with Cluster("Automated CI/CD Platform (GitHub Actions)", graph_attr={"bgcolor": "#f1f5f9", "fontcolor": "#6b21a8", "fontsize": "14", "pencolor": "#c084fc", "penwidth": "1.5"}):
        ci_cd = Custom("GitHub Actions\nCI/CD Runner", "assets/github_actions.png")

    # 2. Google Cloud Run Cluster
    with Cluster("Production Runtime Tier (Google Cloud Run Serverless)", graph_attr={"bgcolor": "#f8fafc", "fontcolor": "#1e40af", "fontsize": "15", "pencolor": "#93c5fd", "penwidth": "1.5"}):
        ui = Custom("React 18 SPA\nVite Frontend", "assets/react.png")
        fastapi = Custom("FastAPI Core\nSSE Streaming Gateway", "assets/fastapi.png")
        
        with Cluster("LangGraph AI State Machine Pipeline", graph_attr={"bgcolor": "#ffffff", "fontcolor": "#b45309", "fontsize": "13", "pencolor": "#fcd34d", "penwidth": "1.5"}):
            validation_node = Custom("1. Ingestion &\nSchema Rules", "assets/segula.png")
            rag_node = PostgreSQL("2. Vector RAG\nSearch Node")
            fact_node = Custom("3. 5-Pillars Fact\nDeepSeek Reasoner", "assets/deepseek.png")
            scoring_node = Custom("4. Scoring Engine\nRubrics & Veto", "assets/segula.png")
            report_node = Custom("5. Dossier Builder\nStrategic AI Advice", "assets/segula.png")

            validation_node >> Edge(color="#64748b", style="solid") >> rag_node >> Edge(color="#64748b", style="solid") >> fact_node >> Edge(color="#64748b", style="solid") >> scoring_node >> Edge(color="#64748b", style="solid") >> report_node

        ui >> Edge(color="#2563eb", label="POST /api/submissions/stream\n(SSE Real-Time)") >> fastapi
        fastapi >> Edge(color="#2563eb", label="Trigger LangGraph") >> validation_node

    # 3. Supabase Database Cluster
    with Cluster("Managed Database Tier (Supabase PostgreSQL 17 + pgvector)", graph_attr={"bgcolor": "#f8fafc", "fontcolor": "#15803d", "fontsize": "15", "pencolor": "#86efac", "penwidth": "1.5"}):
        supabase_db = Custom("Supabase PgBouncer Pooler\n(Port 5432 / Session Mode)", "assets/supabase.png")
        pgvector_store = PostgreSQL("Historic Projects Index\npgvector Cosine (1024-dim)")
        submissions_table = PostgreSQL("Submissions, Facts,\nScoring & Dossiers")
        
        supabase_db >> Edge(color="#16a34a") >> pgvector_store
        supabase_db >> Edge(color="#16a34a") >> submissions_table

    # 4. Lightning AI Sovereign GPU Cluster
    with Cluster("Sovereign AI GPU Platform (Lightning AI Studio - Tesla T4 16GB)", graph_attr={"bgcolor": "#f8fafc", "fontcolor": "#c2410c", "fontsize": "15", "pencolor": "#fdba74", "penwidth": "1.5"}):
        proxy = Custom("FastAPI Secure Gateway\nBearer Token Auth (Port 8000)", "assets/lightning.png")
        
        vllm = Custom("vLLM Inception Engine\nDeepSeek-R1 14B AWQ\n(Port 8001 | Marlin FP16)", "assets/deepseek.png")
        ollama = Custom("Ollama Embed Engine\nQwen3-Embedding 0.6B\n(Port 11434 | 4x Parallel)", "assets/ollama.png")

        proxy >> Edge(color="#ea580c", label="/v1/chat/completions") >> vllm
        proxy >> Edge(color="#ea580c", label="/api/embed") >> ollama

    # Global System Connections
    users >> Edge(color="#2563eb", label="HTTPS / Web Traffic") >> ui
    ci_cd >> Edge(color="#7c3aed", label="Builds & Deploys Container") >> fastapi
    
    rag_node >> Edge(color="#16a34a", label="Cosine Similarity (<=>)") >> supabase_db
    report_node >> Edge(color="#16a34a", label="Persist Results & State") >> supabase_db
    
    rag_node >> Edge(color="#ea580c", style="dashed", label="Embed Query (/api/embed)") >> proxy
    fact_node >> Edge(color="#ea580c", style="bold", label="Stream Reasoning Tokens (/v1/...)") >> proxy
    report_node >> Edge(color="#ea580c", label="Generate Strategic Advice") >> proxy

print("✅ Diagram 1 generated: architecture_diagrams/segula_ai_hub_architecture.png")


# ==============================================================================
# Diagram 2: LangGraph 5-Pillar Decision & Scoring Flow
# ==============================================================================
print("🎨 Generating Diagram 2: LangGraph 5-Pillar Pipeline Flow (White Background)...")

with Diagram(
    "Segula AI Requirement Hub - 5-Pillar LangGraph Decision & Assessment Flow",
    filename="segula_ai_pipeline_flow",
    show=False,
    direction="TB",
    graph_attr={"fontsize": "24", "bgcolor": "#ffffff", "fontcolor": "#0f172a", "pad": "0.8", "ranksep": "1.4", "splines": "curved"},
    node_attr=node_attr_global,
    edge_attr=edge_attr_global
):
    start = Users("Form Submission\n(8 Required Fields + Attachments)")

    with Cluster("1. Ingestion & Schema Gate", graph_attr={"bgcolor": "#f8fafc", "fontcolor": "#1e40af", "pencolor": "#93c5fd", "penwidth": "1.5"}):
        step1 = Custom("Field Ingestion\n& Department Schema Rules", "assets/segula.png")

    with Cluster("2. Semantic Knowledge Base Search", graph_attr={"bgcolor": "#f8fafc", "fontcolor": "#15803d", "pencolor": "#86efac", "penwidth": "1.5"}):
        step2_embed = Custom("Qwen3-Embedding:0.6b\n(1024-dim Vector Generation)", "assets/ollama.png")
        step2_pgvector = PostgreSQL("pgvector Cosine Search (<=>)\nHistoric Segula Projects Index")
        step2_embed >> Edge(color="#16a34a") >> step2_pgvector

    with Cluster("3. 5-Pillar Fact Extraction & Deep Reasoning", graph_attr={"bgcolor": "#f8fafc", "fontcolor": "#c2410c", "pencolor": "#fdba74", "penwidth": "1.5"}):
        step3_reasoning = Custom("DeepSeek-R1 14B AWQ\nStreaming `<think>` Reasoning", "assets/deepseek.png")
        step3_pillars = Custom("5-Pillar Classification\nViability | Data | Clarity | Integration | Governance", "assets/segula.png")
        step3_reasoning >> Edge(color="#ea580c") >> step3_pillars

    with Cluster("4. Deterministic Scoring & Veto Engine", graph_attr={"bgcolor": "#f8fafc", "fontcolor": "#b45309", "pencolor": "#fcd34d", "penwidth": "1.5"}):
        step4_rubrics = Custom("Weighted Scoring Algorithm\n(0 - 100 Scale)", "assets/segula.png")
        step4_veto = Custom("VETO Kill-Switches\n(IMPOSSIBLE | NOT_AI | CRITICAL_RISK | NO_DATA)", "assets/segula.png")
        step4_rubrics >> Edge(color="#d97706") >> step4_veto

    with Cluster("5. Feasibility Dossier & Governance Output", graph_attr={"bgcolor": "#f8fafc", "fontcolor": "#15803d", "pencolor": "#86efac", "penwidth": "1.5"}):
        decision = Custom("Decision Gate\nFAST_TRACK (>=85%) | GO (>=70%) | CLARIFY (>=50%) | NO_GO (<50%)", "assets/segula.png")
        report = Custom("Feasibility Report Dossier\nTarget Architecture, Tech Stack & Action Plan", "assets/segula.png")
        decision >> Edge(color="#16a34a") >> report

    start >> Edge(color="#2563eb") >> step1 >> Edge(color="#2563eb") >> step2_embed
    step2_pgvector >> Edge(color="#2563eb") >> step3_reasoning
    step3_pillars >> Edge(color="#2563eb") >> step4_rubrics
    step4_veto >> Edge(color="#2563eb") >> decision

print("✅ Diagram 2 generated: architecture_diagrams/segula_ai_pipeline_flow.png")
print("🎉 All white-background diagrams generated successfully!")
