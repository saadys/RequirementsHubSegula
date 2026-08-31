"""
Segula AI Requirement Hub - Architecture Diagram Generator
Uses the Python 'diagrams' library to generate high-resolution architecture diagrams.

Run with:
    uv run python architecture_diagrams/generate_diagrams.py
"""

import os
from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
from diagrams.onprem.client import Users
from diagrams.onprem.database import PostgreSQL

# Change to the current directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# ==============================================================================
# Diagram 1: End-to-End Enterprise Architecture
# ==============================================================================
graph_attr = {
    "fontsize": "28",
    "fontname": "Helvetica, Arial, sans-serif",
    "bgcolor": "#0e1117",
    "fontcolor": "#ffffff",
    "pad": "0.8",
    "splines": "spline",
    "nodesep": "0.8",
    "ranksep": "1.2"
}

node_attr = {
    "fontname": "Helvetica, Arial, sans-serif",
    "fontsize": "13",
    "fontcolor": "#ffffff",
    "color": "#30363d",
    "style": "filled",
    "fillcolor": "#161b22"
}

edge_attr = {
    "fontname": "Helvetica, Arial, sans-serif",
    "fontsize": "11",
    "fontcolor": "#8b949e",
    "color": "#58a6ff"
}

print("🎨 Generating Diagram 1: End-to-End Enterprise Architecture...")

with Diagram(
    "Segula AI Requirement Hub - End-to-End Sovereign Enterprise Architecture",
    filename="segula_ai_hub_architecture",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr
):
    users = Users("Segula Engineers\n& Department Leads\n(Web Browser)")

    # 1. CI/CD Cluster
    with Cluster("Automated CI/CD Platform (GitHub Actions)", graph_attr={"bgcolor": "#161b22", "fontcolor": "#a371f7", "fontsize": "16"}):
        ci_cd = Custom("GitHub Actions\nCI/CD Automation", "assets/github_actions.png")

    # 2. Google Cloud Run Cluster
    with Cluster("Production Runtime Platform (Google Cloud Run)\nUnified Serverless Scale-to-Zero Container", graph_attr={"bgcolor": "#161b22", "fontcolor": "#58a6ff", "fontsize": "16"}):
        ui = Custom("React 18 SPA\nFrontend Portal", "assets/react.png")
        fastapi = Custom("FastAPI Application Core\nReal-Time SSE Streaming Gateway", "assets/fastapi.png")
        
        with Cluster("LangGraph AI State Machine Engine", graph_attr={"bgcolor": "#0d1117", "fontcolor": "#d29922", "fontsize": "14"}):
            langgraph = Custom("LangGraph Engine\nCheckpointer Pool", "assets/langgraph.png")
            validation_node = Custom("1. Input & Schema\nValidation Gate", "assets/segula.png")
            rag_node = PostgreSQL("2. Vector RAG\nSearch Node")
            fact_node = Custom("3. 5-Pillar Extraction\nDeepSeek Reasoner", "assets/deepseek.png")
            scoring_node = Custom("4. Scoring Engine\nDeterministic Rubrics", "assets/segula.png")
            report_node = Custom("5. Dossier Builder\nStrategic AI Advice", "assets/segula.png")

            langgraph - validation_node - rag_node - fact_node - scoring_node - report_node

        ui >> Edge(color="#58a6ff", label="POST /api/submissions/stream\n(SSE Events)") >> fastapi
        fastapi >> Edge(color="#58a6ff", label="Trigger Workflow") >> langgraph

    # 3. Supabase Database Cluster
    with Cluster("Managed Database Tier (Supabase PostgreSQL 17 + pgvector)", graph_attr={"bgcolor": "#161b22", "fontcolor": "#3fb950", "fontsize": "16"}):
        supabase_db = Custom("Supabase PgBouncer Pooler\n(Port 5432 / Session Mode)", "assets/supabase.png")
        pgvector_store = PostgreSQL("Historic Projects Index\npgvector Cosine (1024-dim)")
        submissions_table = PostgreSQL("Submissions, Facts,\nScoring & Dossiers")
        
        supabase_db - pgvector_store
        supabase_db - submissions_table

    # 4. Lightning AI Sovereign GPU Cluster
    with Cluster("Sovereign AI GPU Platform (Lightning AI Studio)\nNVIDIA Tesla T4 GPU (16GB VRAM)", graph_attr={"bgcolor": "#161b22", "fontcolor": "#f0883e", "fontsize": "16"}):
        proxy = Custom("FastAPI Secure Gateway\nBearer Token Auth (Port 8000)", "assets/lightning.png")
        
        vllm = Custom("vLLM Inception Engine\nDeepSeek-R1 14B AWQ\n(Port 8001 | Marlin FP16)", "assets/deepseek.png")
        ollama = Custom("Ollama Embed Engine\nQwen3-Embedding 0.6B\n(Port 11434 | 4x Parallel)", "assets/ollama.png")

        proxy >> Edge(color="#f0883e", label="/v1/chat/completions") >> vllm
        proxy >> Edge(color="#f0883e", label="/api/embed") >> ollama

    # Global System Connections
    users >> Edge(color="#58a6ff", label="HTTPS Web Traffic") >> ui
    ci_cd >> Edge(color="#a371f7", label="Builds & Deploys Container") >> fastapi
    
    rag_node >> Edge(color="#3fb950", label="Cosine Similarity (<=>)") >> supabase_db
    report_node >> Edge(color="#3fb950", label="Persist Results & State") >> supabase_db
    
    rag_node >> Edge(color="#f0883e", style="dashed", label="Embed Query (/api/embed)") >> proxy
    fact_node >> Edge(color="#f0883e", style="bold", label="Stream Reasoning Tokens (/v1/...)") >> proxy
    report_node >> Edge(color="#f0883e", label="Generate Strategic Advice") >> proxy

print("✅ Diagram 1 generated: architecture_diagrams/segula_ai_hub_architecture.png")


# ==============================================================================
# Diagram 2: LangGraph 5-Pillar Decision & Scoring Flow
# ==============================================================================
print("🎨 Generating Diagram 2: LangGraph 5-Pillar Pipeline Flow...")

with Diagram(
    "Segula AI Requirement Hub - 5-Pillar LangGraph Decision & Assessment Flow",
    filename="segula_ai_pipeline_flow",
    show=False,
    direction="TB",
    graph_attr={"fontsize": "24", "bgcolor": "#0e1117", "fontcolor": "#ffffff", "pad": "0.6"},
    node_attr=node_attr,
    edge_attr=edge_attr
):
    start = Users("Form Submission\n(8 Required Fields + Attachments)")

    with Cluster("1. Ingestion & Schema Gate", graph_attr={"bgcolor": "#161b22", "fontcolor": "#58a6ff"}):
        step1 = Custom("Field Ingestion\n& Department Schema Rules", "assets/segula.png")

    with Cluster("2. Semantic Knowledge Base Search", graph_attr={"bgcolor": "#161b22", "fontcolor": "#3fb950"}):
        step2_embed = Custom("Qwen3-Embedding:0.6b\n(1024-dim Vector Generation)", "assets/ollama.png")
        step2_pgvector = PostgreSQL("pgvector Cosine Search (<=>)\nHistoric Segula Projects Index")
        step2_embed >> step2_pgvector

    with Cluster("3. 5-Pillar Fact Extraction & Deep Reasoning", graph_attr={"bgcolor": "#161b22", "fontcolor": "#f0883e"}):
        step3_reasoning = Custom("DeepSeek-R1 14B AWQ\nStreaming `<think>` Reasoning", "assets/deepseek.png")
        step3_pillars = Custom("5-Pillar Classification\nViability | Data | Clarity | Integration | Governance", "assets/segula.png")
        step3_reasoning >> step3_pillars

    with Cluster("4. Deterministic Scoring & Veto Engine", graph_attr={"bgcolor": "#161b22", "fontcolor": "#d29922"}):
        step4_rubrics = Custom("Weighted Scoring Algorithm\n(0 - 100 Scale)", "assets/segula.png")
        step4_veto = Custom("VETO Kill-Switches\n(IMPOSSIBLE | NOT_AI | CRITICAL_RISK | NO_DATA)", "assets/segula.png")
        step4_rubrics - step4_veto

    with Cluster("5. Feasibility Dossier & Governance Output", graph_attr={"bgcolor": "#161b22", "fontcolor": "#3fb950"}):
        decision = Custom("Decision Gate\nFAST_TRACK (>=85%) | GO (>=70%) | CLARIFY (>=50%) | NO_GO (<50%)", "assets/segula.png")
        report = Custom("Feasibility Report Dossier\nTarget Architecture, Tech Stack & Action Plan", "assets/segula.png")
        decision >> report

    start >> step1 >> step2_embed
    step2_pgvector >> step3_reasoning
    step3_pillars >> step4_rubrics
    step4_veto >> decision

print("✅ Diagram 2 generated: architecture_diagrams/segula_ai_pipeline_flow.png")
print("🎉 All diagrams generated successfully!")
