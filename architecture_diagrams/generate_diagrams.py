"""
Segula AI Requirement Hub - Enterprise Architecture Diagram Generator
Uses native Python 'graphviz' with HTML record cards for crisp, publication-quality diagrams.

Run with:
    uv run python architecture_diagrams/generate_diagrams.py
"""

import os
import graphviz

# Change to the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# ==============================================================================
# Diagram 1: End-to-End Enterprise Sovereign Architecture
# ==============================================================================
print("🎨 Generating Diagram 1: End-to-End Enterprise Architecture...")

dot = graphviz.Digraph(
    "Segula_AI_Architecture",
    format="png",
    graph_attr={
        "rankdir": "LR",
        "fontsize": "24",
        "fontname": "Helvetica Neue, Arial, sans-serif",
        "bgcolor": "#FFFFFF",
        "pad": "0.6",
        "nodesep": "0.7",
        "ranksep": "1.1",
        "splines": "spline",
        "dpi": "220"
    },
    node_attr={
        "fontname": "Helvetica Neue, Arial, sans-serif",
        "fontsize": "11",
        "shape": "box",
        "style": "rounded,filled",
        "fillcolor": "#FFFFFF",
        "color": "#CBD5E1",
        "penwidth": "1.2",
        "margin": "0.18,0.12"
    },
    edge_attr={
        "fontname": "Helvetica Neue, Arial, sans-serif",
        "fontsize": "9",
        "color": "#475569",
        "penwidth": "1.3",
        "arrowsize": "0.8"
    }
)

# ── 1. Client Tier ──
with dot.subgraph(name="cluster_client") as c:
    c.attr(label="Client & User Tier", fontname="Helvetica Neue, Arial, sans-serif", fontsize="14", fontcolor="#1E293B", style="rounded,filled", fillcolor="#F8FAFC", color="#CBD5E1", penwidth="1.5")
    c.node(
        "user_ui",
        label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B><FONT COLOR="#0F172A" POINT-SIZE="13">Segula Engineering Portal</FONT></B></TD></TR>
        <TR><TD><FONT COLOR="#64748B" POINT-SIZE="10">React 18 SPA + Vite + Tailwind CSS</FONT></TD></TR>
        <TR><TD><FONT COLOR="#2563EB" POINT-SIZE="9">- Real-Time SSE Stream Consumer</FONT></TD></TR>
        <TR><TD><FONT COLOR="#2563EB" POINT-SIZE="9">- AI Admin Audit Dashboard</FONT></TD></TR>
        </TABLE>>''',
        fillcolor="#FFFFFF",
        color="#3B82F6",
        penwidth="1.8"
    )

# ── 2. CI/CD Tier ──
with dot.subgraph(name="cluster_cicd") as c:
    c.attr(label="Automated CI/CD Platform", fontname="Helvetica Neue, Arial, sans-serif", fontsize="14", fontcolor="#6B21A8", style="rounded,filled", fillcolor="#FAF5FF", color="#E9D5FF", penwidth="1.5")
    c.node(
        "github_actions",
        label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B><FONT COLOR="#581C87" POINT-SIZE="13">GitHub Actions Runner</FONT></B></TD></TR>
        <TR><TD><FONT COLOR="#6B21A8" POINT-SIZE="10">- 37 Pytest Unit Tests</FONT></TD></TR>
        <TR><TD><FONT COLOR="#6B21A8" POINT-SIZE="10">- Alembic Schema Migrations</FONT></TD></TR>
        <TR><TD><FONT COLOR="#6B21A8" POINT-SIZE="10">- Docker Build &amp; Deploy to Cloud Run</FONT></TD></TR>
        </TABLE>>''',
        fillcolor="#FFFFFF",
        color="#A855F7",
        penwidth="1.5"
    )

# ── 3. Google Cloud Run Runtime Tier ──
with dot.subgraph(name="cluster_cloudrun") as c:
    c.attr(label="Production Runtime Platform (Google Cloud Run Serverless)", fontname="Helvetica Neue, Arial, sans-serif", fontsize="14", fontcolor="#1E40AF", style="rounded,filled", fillcolor="#F0FDF4", color="#BBF7D0", penwidth="1.5")
    
    c.node(
        "fastapi_app",
        label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B><FONT COLOR="#0F172A" POINT-SIZE="13">FastAPI Application Core</FONT></B></TD></TR>
        <TR><TD><FONT COLOR="#64748B" POINT-SIZE="10">Uvicorn Async ASGI Server (Port 8080)</FONT></TD></TR>
        <TR><TD><FONT COLOR="#059669" POINT-SIZE="9">- Server-Sent Events (SSE) Gateway</FONT></TD></TR>
        <TR><TD><FONT COLOR="#059669" POINT-SIZE="9">- Async Connection Pool Manager</FONT></TD></TR>
        </TABLE>>''',
        fillcolor="#FFFFFF",
        color="#10B981",
        penwidth="1.8"
    )

    with c.subgraph(name="cluster_langgraph") as lg:
        lg.attr(label="LangGraph AI State Machine Engine", fontname="Helvetica Neue, Arial, sans-serif", fontsize="12", fontcolor="#B45309", style="rounded,dashed", fillcolor="#FFFBEB", color="#FCD34D", penwidth="1.2")
        lg.node("n1", label="1. Ingestion &\nSchema Rules", color="#F59E0B", fillcolor="#FFFFFF")
        lg.node("n2", label="2. Vector RAG\nSearch Node", color="#F59E0B", fillcolor="#FFFFFF")
        lg.node("n3", label="3. 5-Pillar Extraction\n(DeepSeek Reasoner)", color="#F59E0B", fillcolor="#FFFFFF")
        lg.node("n4", label="4. Scoring Engine\n(Rubrics & Veto)", color="#F59E0B", fillcolor="#FFFFFF")
        lg.node("n5", label="5. Dossier Builder\n(AI Advice)", color="#F59E0B", fillcolor="#FFFFFF")

# ── 4. Supabase Database Tier ──
with dot.subgraph(name="cluster_supabase") as c:
    c.attr(label="Managed Database Tier (Supabase PostgreSQL 17)", fontname="Helvetica Neue, Arial, sans-serif", fontsize="14", fontcolor="#15803D", style="rounded,filled", fillcolor="#F0FDF4", color="#86EFAC", penwidth="1.5")
    c.node(
        "pg_pooler",
        label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B><FONT COLOR="#14532D" POINT-SIZE="13">PgBouncer Pooler</FONT></B></TD></TR>
        <TR><TD><FONT COLOR="#16A34A" POINT-SIZE="10">Port 5432 (Session Mode)</FONT></TD></TR>
        <TR><TD><FONT COLOR="#64748B" POINT-SIZE="9">Statement Cache Disabled</FONT></TD></TR>
        </TABLE>>''',
        fillcolor="#FFFFFF",
        color="#22C55E",
        penwidth="1.5"
    )
    c.node(
        "pg_vector",
        label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B><FONT COLOR="#14532D" POINT-SIZE="13">pgvector Store</FONT></B></TD></TR>
        <TR><TD><FONT COLOR="#16A34A" POINT-SIZE="10">Historic Segula Index</FONT></TD></TR>
        <TR><TD><FONT COLOR="#64748B" POINT-SIZE="9">1024-dim Cosine (&lt;=&gt;)</FONT></TD></TR>
        </TABLE>>''',
        fillcolor="#FFFFFF",
        color="#22C55E",
        penwidth="1.5"
    )
    c.node(
        "pg_tables",
        label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B><FONT COLOR="#14532D" POINT-SIZE="13">Relational Audit Tables</FONT></B></TD></TR>
        <TR><TD><FONT COLOR="#16A34A" POINT-SIZE="10">- Submissions &amp; Facts</FONT></TD></TR>
        <TR><TD><FONT COLOR="#16A34A" POINT-SIZE="10">- Scores &amp; Dossiers</FONT></TD></TR>
        </TABLE>>''',
        fillcolor="#FFFFFF",
        color="#22C55E",
        penwidth="1.5"
    )

# ── 5. Sovereign GPU Compute Tier ──
with dot.subgraph(name="cluster_gpu") as c:
    c.attr(label="Sovereign AI Compute Tier (Lightning AI Studio - Tesla T4 16GB)", fontname="Helvetica Neue, Arial, sans-serif", fontsize="14", fontcolor="#C2410C", style="rounded,filled", fillcolor="#FFF7ED", color="#FDBA74", penwidth="1.5")
    c.node(
        "gpu_proxy",
        label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B><FONT COLOR="#9A3412" POINT-SIZE="13">Secure Gateway Proxy</FONT></B></TD></TR>
        <TR><TD><FONT COLOR="#C2410C" POINT-SIZE="10">FastAPI Port 8000</FONT></TD></TR>
        <TR><TD><FONT COLOR="#EA580C" POINT-SIZE="9">Bearer Token Auth &amp; Routing</FONT></TD></TR>
        </TABLE>>''',
        fillcolor="#FFFFFF",
        color="#F97316",
        penwidth="1.8"
    )
    c.node(
        "vllm_engine",
        label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B><FONT COLOR="#9A3412" POINT-SIZE="13">vLLM Inference Engine</FONT></B></TD></TR>
        <TR><TD><FONT COLOR="#C2410C" POINT-SIZE="10">Port 8001 | AWQ Marlin FP16</FONT></TD></TR>
        <TR><TD><FONT COLOR="#EA580C" POINT-SIZE="9"><B>DeepSeek-R1-Distill-Qwen-14B</B></FONT></TD></TR>
        <TR><TD><FONT COLOR="#64748B" POINT-SIZE="9">High-Speed Token Streaming</FONT></TD></TR>
        </TABLE>>''',
        fillcolor="#FFFFFF",
        color="#EA580C",
        penwidth="1.5"
    )
    c.node(
        "ollama_engine",
        label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B><FONT COLOR="#9A3412" POINT-SIZE="13">Ollama Embedding Engine</FONT></B></TD></TR>
        <TR><TD><FONT COLOR="#C2410C" POINT-SIZE="10">Port 11434 | 4x Parallel Workers</FONT></TD></TR>
        <TR><TD><FONT COLOR="#EA580C" POINT-SIZE="9"><B>Qwen3-Embedding:0.6b</B></FONT></TD></TR>
        <TR><TD><FONT COLOR="#64748B" POINT-SIZE="9">Permanent VRAM Keep-Alive</FONT></TD></TR>
        </TABLE>>''',
        fillcolor="#FFFFFF",
        color="#EA580C",
        penwidth="1.5"
    )

# ── Logical Connections ──
dot.edge("user_ui", "fastapi_app", label=" HTTPS / SSE Stream", color="#2563EB", fontcolor="#1E40AF")
dot.edge("github_actions", "fastapi_app", label=" Automated Deploy", color="#7C3AED", fontcolor="#6B21A8", style="dashed")

dot.edge("fastapi_app", "n1", label=" Trigger", color="#059669")
dot.edge("n1", "n2", color="#D97706")
dot.edge("n2", "n3", color="#D97706")
dot.edge("n3", "n4", color="#D97706")
dot.edge("n4", "n5", color="#D97706")

dot.edge("n2", "pg_pooler", label=" Search Similars", color="#16A34A", fontcolor="#15803D")
dot.edge("pg_pooler", "pg_vector", color="#16A34A")
dot.edge("n5", "pg_pooler", label=" Save Dossier", color="#16A34A", fontcolor="#15803D")
dot.edge("pg_pooler", "pg_tables", color="#16A34A")

dot.edge("n2", "gpu_proxy", label=" /api/embed", color="#EA580C", fontcolor="#C2410C", style="dashed")
dot.edge("n3", "gpu_proxy", label=" /v1/... (Stream)", color="#EA580C", fontcolor="#C2410C")
dot.edge("n5", "gpu_proxy", label=" Advice", color="#EA580C", fontcolor="#C2410C")

dot.edge("gpu_proxy", "vllm_engine", color="#EA580C")
dot.edge("gpu_proxy", "ollama_engine", color="#EA580C")

dot.render("segula_ai_hub_architecture", cleanup=True)
print("✅ Diagram 1 generated: segula_ai_hub_architecture.png")


# ==============================================================================
# Diagram 2: LangGraph 5-Pillar Decision Pipeline Flow
# ==============================================================================
print("🎨 Generating Diagram 2: LangGraph 5-Pillar Pipeline Flow...")

flow = graphviz.Digraph(
    "Segula_AI_Pipeline_Flow",
    format="png",
    graph_attr={
        "rankdir": "TB",
        "fontsize": "22",
        "fontname": "Helvetica Neue, Arial, sans-serif",
        "bgcolor": "#FFFFFF",
        "pad": "0.5",
        "nodesep": "0.5",
        "ranksep": "0.6",
        "dpi": "220"
    },
    node_attr={
        "fontname": "Helvetica Neue, Arial, sans-serif",
        "fontsize": "11",
        "shape": "box",
        "style": "rounded,filled",
        "fillcolor": "#FFFFFF",
        "color": "#CBD5E1",
        "penwidth": "1.2",
        "margin": "0.22,0.14"
    },
    edge_attr={
        "fontname": "Helvetica Neue, Arial, sans-serif",
        "fontsize": "10",
        "color": "#2563EB",
        "penwidth": "1.5",
        "arrowsize": "0.8"
    }
)

flow.node(
    "start",
    label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
    <TR><TD><B><FONT COLOR="#0F172A" POINT-SIZE="13">Project Requirement Submission</FONT></B></TD></TR>
    <TR><TD><FONT COLOR="#64748B" POINT-SIZE="10">8 Mandatory Form Fields + Optional Technical Attachments</FONT></TD></TR>
    </TABLE>>''',
    fillcolor="#EFF6FF",
    color="#3B82F6",
    penwidth="1.8"
)

flow.node(
    "step1",
    label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
    <TR><TD><B><FONT COLOR="#0F172A" POINT-SIZE="12">1. Ingestion &amp; Department Rules Gate</FONT></B></TD></TR>
    <TR><TD><FONT COLOR="#64748B" POINT-SIZE="10">Validates required fields &amp; department schema constraints</FONT></TD></TR>
    </TABLE>>''',
    fillcolor="#F8FAFC"
)

flow.node(
    "step2",
    label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
    <TR><TD><B><FONT COLOR="#0F172A" POINT-SIZE="12">2. Semantic Knowledge Base Search (Vector RAG)</FONT></B></TD></TR>
    <TR><TD><FONT COLOR="#059669" POINT-SIZE="10">- Qwen3-Embedding:0.6b (1024-dim dense vector generation)</FONT></TD></TR>
    <TR><TD><FONT COLOR="#059669" POINT-SIZE="10">- pgvector Cosine Distance Search across Historic Segula Projects</FONT></TD></TR>
    <TR><TD><FONT COLOR="#059669" POINT-SIZE="10">- Returns Top Similar Projects &amp; Historical Similarity Score %</FONT></TD></TR>
    </TABLE>>''',
    fillcolor="#F0FDF4",
    color="#86EFAC",
    penwidth="1.5"
)

flow.node(
    "step3",
    label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
    <TR><TD><B><FONT COLOR="#0F172A" POINT-SIZE="12">3. 5-Pillar Fact Extraction &amp; Deep Reasoning</FONT></B></TD></TR>
    <TR><TD><FONT COLOR="#EA580C" POINT-SIZE="10"><B>DeepSeek-R1-Distill-Qwen-14B-AWQ (vLLM)</B></FONT></TD></TR>
    <TR><TD><FONT COLOR="#475569" POINT-SIZE="10">- Real-Time Streaming &lt;think&gt; Architectural Reasoning</FONT></TD></TR>
    <TR><TD><FONT COLOR="#475569" POINT-SIZE="10">- AI Viability | Data Readiness | Problem Scope &amp; Clarity</FONT></TD></TR>
    <TR><TD><FONT COLOR="#475569" POINT-SIZE="10">- Integration Feasibility | Governance &amp; Compliance Risk</FONT></TD></TR>
    </TABLE>>''',
    fillcolor="#FFF7ED",
    color="#FDBA74",
    penwidth="1.5"
)

flow.node(
    "step4",
    label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
    <TR><TD><B><FONT COLOR="#0F172A" POINT-SIZE="12">4. Deterministic Scoring &amp; VETO Gate</FONT></B></TD></TR>
    <TR><TD><FONT COLOR="#D97706" POINT-SIZE="10">- Weighted 5-Pillar Rubric Calculation (0 - 100 Score)</FONT></TD></TR>
    <TR><TD><FONT COLOR="#DC2626" POINT-SIZE="10">- VETO Kill-Switches: IMPOSSIBLE, NOT_AI, CRITICAL_RISK, NO_DATA</FONT></TD></TR>
    </TABLE>>''',
    fillcolor="#FEF3C7",
    color="#FCD34D",
    penwidth="1.5"
)

flow.node(
    "step5",
    label='''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
    <TR><TD><B><FONT COLOR="#0F172A" POINT-SIZE="12">5. Decision Gate &amp; Feasibility Dossier</FONT></B></TD></TR>
    <TR><TD><FONT COLOR="#15803D" POINT-SIZE="10"><B>FAST_TRACK</B> (Exact Match / Score &gt;= 85%)</FONT></TD></TR>
    <TR><TD><FONT COLOR="#059669" POINT-SIZE="10"><B>GO</B> (High Viability / Score &gt;= 70%)</FONT></TD></TR>
    <TR><TD><FONT COLOR="#D97706" POINT-SIZE="10"><B>CLARIFY</B> (Partial Info / Score 50-69%)</FONT></TD></TR>
    <TR><TD><FONT COLOR="#DC2626" POINT-SIZE="10"><B>NO_GO</B> (Veto Triggered / Score &lt; 50%)</FONT></TD></TR>
    <TR><TD><FONT COLOR="#64748B" POINT-SIZE="10">- Generates Tailored Architecture, Tech Stack &amp; Next Action Plan</FONT></TD></TR>
    </TABLE>>''',
    fillcolor="#F0FDF4",
    color="#86EFAC",
    penwidth="1.8"
)

flow.edge("start", "step1")
flow.edge("step1", "step2")
flow.edge("step2", "step3")
flow.edge("step3", "step4")
flow.edge("step4", "step5")

flow.render("segula_ai_pipeline_flow", cleanup=True)
print("✅ Diagram 2 generated: segula_ai_pipeline_flow.png")
print("🎉 Clean professional vector diagrams generated successfully!")
