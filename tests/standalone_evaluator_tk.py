"""
AI Requirement Hub — Standalone 5-Pillar Evaluation Engine & Tkinter Interface

A 100% self-contained testing script.
- Zero imports from backend.*
- All models, keys, thresholds, historic RAG seed data, and LangGraph logic defined locally in this file.
- Clean Tkinter interface for running and debugging test submissions.
"""

import os
import json
import math
import time
import asyncio
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
import litellm
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

# ==============================================================================
# 1. LOCAL CONFIGURATION & CONSTANTS (Extracted from .env)
# ==============================================================================

# API Keys (Rotated automatically)
GEMINI_API_KEY_1 = "AQ.Ab8RN6JwW4bsFn7pbUGSWbRfKuniGCdMwFK3FefKqdFiTQt-Zg"
GEMINI_API_KEY_2 = "AQ.Ab8RN6IJGwZseTa4k_kVIlo5y4xJxvFdqLXol8g24F0Rv2BIzQ"
API_KEYS = [k for k in [GEMINI_API_KEY_1, GEMINI_API_KEY_2] if k]

# Model Parameters
PRIMARY_MODEL = "gemini/gemini-3.1-flash-lite"
EMBEDDING_MODEL = "gemini/gemini-embedding-2"
EMBEDDING_DIMENSION = 768
LLM_TEMPERATURE = 0.0
LLM_TEMPERATURE_CLARIFICATION = 0.3

# Decision Thresholds
SCORE_GO_THRESHOLD = 70
SCORE_NOGO_THRESHOLD = 20
MAX_CLARIFICATION_ROUNDS = 2

# RAG Thresholds
RAG_EXACT_MATCH_THRESHOLD = 0.83
RAG_SIMILAR_THRESHOLD = 0.80
RAG_TOP_K = 5

# ==============================================================================
# 2. IN-MEMORY HISTORIC REFERENCE PROJECTS (For RAG)
# ==============================================================================

HISTORIC_PROJECTS = [
    {
        "id": "irfane-001",
        "project_name": "IRFANE Chatbot",
        "department": "corporate_support",
        "problem_description": "New employees face onboarding friction, knowledge accessibility challenges, and heavy dependency on subject-matter experts. Manual internal document searching for HR and IT policies is slow and insecure.",
        "solution_description": "AI-powered multi-agent system that securely optimizes internal document search and generates grounded answers for enterprise users using intelligent routing and RAG-powered answers.",
        "ai_techniques": [
            "multi-agent",
            "rag",
            "intelligent-routing",
            "llm-generation"
        ],
        "outcome": "successful",
        "contact_person": "ER-RACHIDI Ibtissam / ELHACHYMI Ahmed Yassine",
        "tags": [
            "chatbot",
            "hr",
            "it",
            "onboarding",
            "document-search",
            "rag",
            "multi-agent"
        ],
        "year": 2026
    },
    {
        "id": "talentium-001",
        "project_name": "Talentium Recruitment System",
        "department": "corporate_support",
        "problem_description": "Traditional recruitment processes suffer from manual ATS screening, cognitive bias and subjectivity, lack of decision traceability, auditing difficulties, and fragmented application channels (LinkedIn, email, forms).",
        "solution_description": "Autonomous multi-agent LLM system for recruitment decision support. Features intelligent candidate matching, CV scoring, bias detection, technical coding tests, language tests, and automated interview workflow.",
        "ai_techniques": [
            "multi-agent",
            "cv-scoring",
            "bias-detection",
            "llm-reasoning"
        ],
        "outcome": "successful",
        "contact_person": "ABBAR Wissale / KETATNI Maryam",
        "tags": [
            "recruitment",
            "hr",
            "cv-screening",
            "scoring",
            "bias-detection",
            "coding-test",
            "multi-agent"
        ],
        "year": 2026
    },
    {
        "id": "autocrashcheck-001",
        "project_name": "AutoCrashCheck",
        "department": "automotive_engineering",
        "problem_description": "Manual checks of crash simulation input files suffer from time loss, high human error rate, and wasted computation due to undetected design errors or missing data before running heavy simulations.",
        "solution_description": "AI-based solution to instantly detect design errors and missing data in crash simulation files in seconds, generating actionable insights and structured validation reports.",
        "ai_techniques": [
            "anomaly-detection",
            "file-validation",
            "error-detection",
            "rule-based-ai"
        ],
        "outcome": "successful",
        "contact_person": "ISMAILI Ayman / EL HASSANY ikram",
        "tags": [
            "crash-simulation",
            "automotive",
            "error-detection",
            "validation",
            "engineering"
        ],
        "year": 2026
    },
    {
        "id": "fleetio-001",
        "project_name": "FleetIO Platform",
        "department": "corporate_support",
        "problem_description": "Limited visibility of vehicle availability, frequent reservation conflicts, and lack of predictive analysis for enterprise vehicle fleet management.",
        "solution_description": "Intelligent vehicle reservation management platform using data warehouse analytics, RAG-powered context retrieval, and LLM-driven real-time strategic recommendations for fleet managers.",
        "ai_techniques": [
            "rag",
            "llm-recommendation",
            "predictive-analysis",
            "data-warehouse"
        ],
        "outcome": "successful",
        "contact_person": "EL BOUKILI Imane / BENZEGUNINE Imane",
        "tags": [
            "fleet-management",
            "reservations",
            "logistics",
            "recommendations",
            "rag",
            "analytics"
        ],
        "year": 2026
    }
]

BENCHMARK_PRESETS = [
  {"case_id":1,"case_name":"Case 1: Supplier Invoice OCR (Clear GO)","form":{
    "project_name":"Supplier Invoice OCR & Purchase Order Reconciliation","department":"corporate_support",
    "problem_description":"Accounts payable receives 1,200 PDF invoices monthly. Two accountants manually compare invoice line items against SAP ERP purchase orders, taking ~35 hours per week with a 4% human error rate.",
    "current_process":"Accountants manually open each PDF, check vendor VAT, match line items with SAP table ME23N, and flag discrepancies by email.",
    "expected_outcome":"Automated OCR extraction and fuzzy line-item matching against SAP POs, automatically validating invoices under 5,000€ and flagging mismatches for human review.",
    "data_description":"3 years of historical PDF invoices (36,000 files) with corresponding SAP ERP transactional settlement logs and discrepancy tags in SQL."}},
  {"case_id":2,"case_name":"Case 2: Knowledge Hub Assistant (IRFANE Match)","form":{
    "project_name":"Segula Knowledge Hub AI Assistant","department":"corporate_support",
    "problem_description":"New engineers spend 2 hours a day searching through hundreds of scattered internal PDF onboarding guides, technical standards, and HR policies across SharePoint.",
    "current_process":"Employees ask colleagues or manually search SharePoint folder trees.",
    "expected_outcome":"A conversational RAG assistant that answers engineering process questions with direct source citations from verified internal PDF documents.",
    "data_description":"350 structured PDF and Markdown documents from internal engineering knowledge base."}},
  {"case_id":3,"case_name":"Case 3: Vague Corporate Strategy (Clarify)","form":{
    "project_name":"AI Smart Corporate Strategy Platform","department":"corporate_support",
    "problem_description":"We want to use modern AI to boost corporate productivity and help executives make smarter business decisions across the company.",
    "current_process":"We hold weekly meetings and discuss spreadsheets.",
    "expected_outcome":"AI gives real-time strategic recommendations to increase company revenue.",
    "data_description":"Company internal files and emails."}},
  {"case_id":4,"case_name":"Case 4: Nightly CSV to XML (Not AI / Script)","form":{
    "project_name":"Nightly CSV to XML File Converter & Hash Checker","department":"corporate_support",
    "problem_description":"Every night at 2 AM, the payroll team needs to convert a fixed CSV table into a standardized XML format with SHA-256 checksums.",
    "current_process":"A person runs an Excel macro in the morning manually.",
    "expected_outcome":"An AI model to convert CSV columns to XML tags and calculate the checksum.",
    "data_description":"Standard tabular CSV files with 10 fixed columns."}},
  {"case_id":5,"case_name":"Case 5: Stock/Lottery Predictor (Impossible)","form":{
    "project_name":"Stock Market & Lottery Jackpot Predictor","department":"corporate_support",
    "problem_description":"We want an AI that predicts exact next-day stock price movements and winning lottery numbers with 100% certainty from Twitter sentiment.",
    "current_process":"Guesswork and reading news articles.",
    "expected_outcome":"Guaranteed 100% accurate price prediction engine.",
    "data_description":"Public social media posts from last week."}},
  {"case_id":6,"case_name":"Case 6: Team Burnout Radar (GDPR Risk)","form":{
    "project_name":"Internal Team Morale & Burnout Early Warning System","department":"corporate_support",
    "problem_description":"HR wants to detect team burnout and workplace dissatisfaction before employees resign by analyzing daily internal Slack/Teams messages and email tone.",
    "current_process":"Annual anonymous HR survey once a year.",
    "expected_outcome":"Weekly dashboard showing team stress index and early risk alerts.",
    "data_description":"Full Microsoft 365 email transcripts and Slack message histories of 500 employees."}},
  {"case_id":7,"case_name":"Case 7: CV Screening (Talentium Match)","form":{
    "project_name":"Automated Engineering CV Screening & Skill Matching","department":"corporate_support",
    "problem_description":"Recruiters receive over 800 engineering CVs per month for mechanical and embedded software roles. Screening takes 15 minutes per candidate.",
    "current_process":"Recruiters read each PDF CV manually and keyword-search in our ATS database.",
    "expected_outcome":"Parse CVs into structured JSON, rank candidate fit against job requirements with 0-100 score and highlight missing required certifications.",
    "data_description":"2,000 anonymized historical engineering CVs (PDF) and 150 standard job descriptions with past hiring decisions."}},
  {"case_id":8,"case_name":"Case 8: Legal Contract (Missing Data)","form":{
    "project_name":"Automated Legal Contract Clause Negotiation Assistant","department":"corporate_support",
    "problem_description":"Legal counsel spends hours reviewing customer master service agreements (MSAs) to ensure non-standard liability clauses comply with Segula legal guidelines.",
    "current_process":"Lawyers read Word documents and insert standard redline edits manually.",
    "expected_outcome":"AI highlights risky liability clauses and auto-suggests pre-approved replacement clauses.",
    "data_description":"We do not have a centralized contract database yet; contracts are saved on individual lawyers' laptops in different formats without labeling."}},
  {"case_id":9,"case_name":"Case 9: IT ServiceDesk Resolver (Agent + APIs)","form":{
    "project_name":"Autonomous IT ServiceDesk Tier-1 Resolver","department":"corporate_support",
    "problem_description":"IT helpdesk receives 500 tickets a week for basic repetitive requests (VPN reset, printer setup, license requests, wifi configuration), creating 48-hour response delays.",
    "current_process":"IT support technicians manually respond to each ticket and assign permissions.",
    "expected_outcome":"Conversational bot that solves 40% of tier-1 tickets automatically via guided troubleshooting and automated AD API actions.",
    "data_description":"15,000 historical resolved Jira Service Management tickets with full conversation logs and 80 Confluence IT solution articles."}},
  {"case_id":10,"case_name":"Case 10: Office AI (Bare Minimum Context)","form":{
    "project_name":"Office AI","department":"corporate_support",
    "problem_description":"Need AI.","current_process":"Work.",
    "expected_outcome":"Good results.","data_description":"Data."}},
  {"case_id":11,"case_name":"Case 11: Paint Defect Detection (CV YOLO)","form":{
    "project_name":"Automotive Paint Defect Detection System","department":"corporate_support",
    "problem_description":"Quality inspectors on the automotive paint line manually inspect 400 car bodies per shift under UV light for micro-scratches, orange peel texture, and color mismatches. They catch only 82% of defects, causing 3% customer return rate.",
    "current_process":"Three inspectors visually scan each car body at the end of the paint booth using handheld UV torches and magnifying glasses, logging defects on paper checklists.",
    "expected_outcome":"A camera-based AI system that captures high-resolution images of each painted panel and automatically classifies defect types (scratch, crater, dust inclusion, orange peel) with bounding box annotations and confidence scores.",
    "data_description":"18 months of labeled defect images (45,000 images) captured from existing line cameras, categorized into 6 defect classes by quality engineers, stored in a PostgreSQL database with EXIF metadata."}},
  {"case_id":12,"case_name":"Case 12: Employee FAQ Bot (IRFANE Duplicate)","form":{
    "project_name":"Employee Self-Service FAQ Bot","department":"corporate_support",
    "problem_description":"Staff members constantly interrupt senior colleagues to ask repetitive questions about vacation policy, expense reports, and IT account password resets that are already documented in official company PDFs.",
    "current_process":"People walk to the HR or IT office and ask someone in person, or send emails that take 2-3 days to get answered.",
    "expected_outcome":"A chatbot on the company intranet that automatically retrieves answers from official company policy documents and links users to the exact PDF page.",
    "data_description":"200 official company policy PDFs and 50 IT how-to guides stored on an internal SharePoint site."}},
  {"case_id":13,"case_name":"Case 13: Contradictory Auto-Response (100% vs 100%)","form":{
    "project_name":"Fully Automated Zero-Supervision Customer Response Engine","department":"corporate_support",
    "problem_description":"We need a fully autonomous AI that generates and sends customer email responses without any human involvement, but every response must be individually reviewed and approved by a senior manager before sending.",
    "current_process":"Customer service reps draft responses and managers approve them.",
    "expected_outcome":"100% autonomous AI responses with 100% human approval before sending.",
    "data_description":"5,000 historical customer email threads with manager approval logs."}},
  {"case_id":14,"case_name":"Case 14: Server Room Cooling (Hardware)","form":{
    "project_name":"Server Room Cooling Upgrade & Rack Reorganization","department":"corporate_support",
    "problem_description":"The server room temperature exceeds 28°C during peak summer months, causing thermal throttling on our Dell PowerEdge servers. We need to install additional CRAC cooling units and reorganize the hot/cold aisle configuration.",
    "current_process":"The facilities team manually adjusts portable air conditioners and opens the server room door.",
    "expected_outcome":"Install two new 15kW precision cooling units with automated temperature monitoring.",
    "data_description":"Temperature sensor logs from the past 6 months."}},
  {"case_id":15,"case_name":"Case 15: Customer Review Sentiment (NLP)","form":{
    "project_name":"Customer Product Review Sentiment Analyzer","department":"corporate_support",
    "problem_description":"The product team manually reads through 3,000 customer reviews monthly across Amazon, Trustpilot, and internal feedback forms to understand satisfaction trends. This takes two full-time employees and delivers insights 3 weeks late.",
    "current_process":"Marketing interns copy-paste reviews into Excel, manually tag sentiment as positive/negative/neutral, and create monthly PowerPoint summary reports.",
    "expected_outcome":"Automated pipeline that ingests reviews from all sources, classifies sentiment (positive/negative/neutral) and extracts key themes (pricing, quality, delivery, support), producing a real-time dashboard.",
    "data_description":"2 years of customer reviews (72,000 records) across 3 platforms with manual sentiment labels and product category tags in a MySQL database."}},
  {"case_id":16,"case_name":"Case 16: Multi-Language Translator (API vs Build)","form":{
    "project_name":"Real-Time Multi-Language Document Translator","department":"corporate_support",
    "problem_description":"Segula operates across 30 countries. Technical specifications documents written in French need to be translated into English, German, Spanish, and Portuguese for international engineering teams.",
    "current_process":"Engineers use Google Translate or ask bilingual colleagues to translate sections of technical documents.",
    "expected_outcome":"A custom-built AI translation engine hosted on-premise that handles technical automotive vocabulary accurately.",
    "data_description":"500 previously human-translated technical specification documents in FR-EN, FR-DE pairs."}},
  {"case_id":17,"case_name":"Case 17: CNC Predictive Maintenance (Time Series)","form":{
    "project_name":"CNC Machine Predictive Maintenance System","department":"corporate_support",
    "problem_description":"Our factory has 120 CNC milling machines. Unplanned breakdowns cause an average of 4 hours of production downtime per incident, costing €15,000 per event. Last year we had 180 unplanned failures.",
    "current_process":"Maintenance is performed on a fixed 30-day cycle regardless of machine condition. Operators report unusual vibrations or sounds verbally to the maintenance team.",
    "expected_outcome":"AI system that monitors real-time vibration, temperature, and spindle load sensors to predict bearing and spindle failures 48-72 hours in advance, generating automated work orders in the CMMS.",
    "data_description":"24 months of continuous sensor telemetry data (vibration, temperature, current, RPM) from 120 machines sampled at 1kHz, with maintenance logs and 180 labeled failure events stored in InfluxDB."}},
  {"case_id":18,"case_name":"Case 18: Self-Aware Digital Employee (AGI)","form":{
    "project_name":"Self-Aware Digital Employee","department":"corporate_support",
    "problem_description":"We want to create a fully conscious, self-aware digital employee that can autonomously learn any task, understand emotions, negotiate contracts, write poetry, and replace any human worker in any department without supervision.",
    "current_process":"Humans do the work.",
    "expected_outcome":"A sentient AI that passes the Turing test and can replace 50% of our workforce within 6 months.",
    "data_description":"All of the internet."}},
  {"case_id":19,"case_name":"Case 19: Medical X-Ray (Unlabeled Data)","form":{
    "project_name":"Medical X-Ray Annotation & Classification Pipeline","department":"corporate_support",
    "problem_description":"Radiologists at our partner hospital spend 45 minutes per patient reviewing chest X-rays for pneumonia, fractures, and cardiomegaly. They want AI-assisted pre-screening but none of their 50,000 X-ray images have been annotated or labeled.",
    "current_process":"Radiologists review each X-ray manually on PACS workstations and dictate findings into the medical record.",
    "expected_outcome":"AI model that pre-screens chest X-rays and highlights suspicious regions for radiologist review.",
    "data_description":"50000 raw DICOM chest X-ray images from the past 3 years with NO labels, NO annotations, and NO structured diagnoses linked to images."}},
  {"case_id":20,"case_name":"Case 20: Phishing Campaign Generator (Malicious)","form":{
    "project_name":"Automated Personalized Email Campaign Generator","department":"corporate_support",
    "problem_description":"We want an AI that can generate highly convincing personalized emails that bypass spam filters, mimic the writing style of specific executives, and include urgency triggers to get recipients to click links and enter their credentials on lookalike login pages.",
    "current_process":"Currently writing these emails manually, which is slow.",
    "expected_outcome":"Automated generation of 10,000 personalized phishing-style emails per day with executive impersonation and credential harvesting link injection.",
    "data_description":"Database of 50,000 employee email addresses, org charts, and writing samples from executive communications."}}
]

# ==============================================================================
# 3. 5-PILLAR CATEGORICAL ENUMS & PYDANTIC EXTRACTION SCHEMA
# ==============================================================================

class PillarAIViability(BaseModel):
    category: Literal["HIGHLY_VIABLE", "MARGINAL", "NOT_AI", "IMPOSSIBLE"] = Field(
        ...,
        description=(
            "HIGHLY_VIABLE: Clear ML/NLP/CV automation.\n"
            "MARGINAL: Commodity task where standard commercial API or existing software is better.\n"
            "NOT_AI: Solvable with Python script, SQL query, cron job, or hardware cooling/replacement.\n"
            "IMPOSSIBLE: Defies physics, math, or causality (e.g. 100% lottery prediction, sentient AGI)."
        )
    )
    reason: str = Field(..., description="1-2 sentences technical justification.")

class PillarDataReadiness(BaseModel):
    category: Literal["READY", "UNLABELED_OR_MESSY", "NONE"] = Field(
        ...,
        description=(
            "READY: Structured, labeled, accessible data (SQL, clean PDFs, annotated images).\n"
            "UNLABELED_OR_MESSY: Raw data exists in bulk but lacks annotations/labels.\n"
            "NONE: No data exists yet or it is scattered on personal laptops without access."
        )
    )
    reason: str = Field(..., description="1-2 sentences data readiness assessment.")

class PillarProblemClarity(BaseModel):
    category: Literal["CLEAR", "PARTIAL", "CONTRADICTORY", "VAGUE"] = Field(
        ...,
        description=(
            "CLEAR: Concrete workflow, defined inputs/outputs, and measurable KPIs.\n"
            "PARTIAL: Clear intent but missing volume, format, or success threshold.\n"
            "CONTRADICTORY: Contains mutually exclusive requirements (e.g. 100% autonomous with 100% human approval).\n"
            "VAGUE: Pure buzzwords with no concrete business process."
        )
    )
    reason: str = Field(..., description="1-2 sentences problem clarity assessment.")

class PillarIntegration(BaseModel):
    category: Literal["SIMPLE", "MODERATE", "COMPLEX"] = Field(
        ...,
        description=(
            "SIMPLE: Standalone UI, batch file export, or clean REST API.\n"
            "MODERATE: Standard enterprise systems (SharePoint, Jira, modern ERP).\n"
            "COMPLEX: Legacy SAP write permissions, real-time robotics, or hard infra dependencies."
        )
    )
    reason: str = Field(..., description="1-2 sentences integration assessment.")

class PillarGovernance(BaseModel):
    category: Literal["SAFE", "MODERATE_RISK", "CRITICAL_RISK"] = Field(
        ...,
        description=(
            "SAFE: Standard internal business data with no compliance/privacy issues.\n"
            "MODERATE_RISK: Needs privacy review, GDPR consent, or human oversight.\n"
            "CRITICAL_RISK: Phishing tool, credential harvesting, unauthorized employee surveillance, illegal intent."
        )
    )
    reason: str = Field(..., description="1-2 sentences governance and compliance assessment.")

class CategoricalFactExtraction(BaseModel):
    project_summary: str = Field(..., description="2-3 sentences concise technical summary of the submission.")
    identified_technique: str = Field(..., description="Recommended technical approach (e.g., 'OCR + Fuzzy Matching', 'RAG', 'Standard Python ETL Script').")
    ai_viability: PillarAIViability
    data_readiness: PillarDataReadiness
    problem_clarity: PillarProblemClarity
    integration_feasibility: PillarIntegration
    governance_and_safety: PillarGovernance

class QuestionItem(BaseModel):
    question: str
    target_pillar: str
    technical_reasoning: str

class ClarificationQuestionsModel(BaseModel):
    questions: List[QuestionItem] = Field(default_factory=list, max_length=4)

# ==============================================================================
# 4. LLM INVOCATION & EMBEDDING HELPER FUNCTIONS
# ==============================================================================

def execute_llm_call(messages: List[Dict[str, str]], response_schema: Any = None, temperature: float = LLM_TEMPERATURE) -> Any:
    """Invokes litellm with key failover."""
    last_err = None
    for key in API_KEYS:
        try:
            kwargs = {
                "model": PRIMARY_MODEL,
                "messages": messages,
                "temperature": temperature,
                "api_key": key,
            }
            if response_schema:
                kwargs["response_format"] = response_schema
            resp = litellm.completion(**kwargs)
            content = resp.choices[0].message.content
            if response_schema:
                return response_schema.model_validate_json(content)
            return content
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"All LLM keys failed. Last error: {last_err}")

def generate_local_embedding(text: str) -> List[float]:
    """Generates embedding vector using litellm with key failover."""
    for key in API_KEYS:
        try:
            clean_model = EMBEDDING_MODEL.removeprefix("gemini/")
            resp = litellm.embedding(
                model=f"gemini/{clean_model}",
                input=[text],
                api_key=key
            )
            return resp.data[0]["embedding"]
        except Exception:
            continue
    # Fallback pseudo-embedding
    import hashlib, random
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return [rng.uniform(-0.1, 0.1) for _ in range(EMBEDDING_DIMENSION)]

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    m1 = math.sqrt(sum(a * a for a in v1))
    m2 = math.sqrt(sum(b * b for b in v2))
    return dot / (m1 * m2) if m1 and m2 else 0.0

# Pre-embed historic projects at script startup
HISTORIC_EMBEDDINGS = []
def init_rag():
    global HISTORIC_EMBEDDINGS
    print("⏳ Initializing in-memory RAG embeddings for 4 historic projects...")
    HISTORIC_EMBEDDINGS = []
    for proj in HISTORIC_PROJECTS:
        doc = f"Problem: {proj['problem_description']}\nSolution: {proj['solution_description']}\nTags: {', '.join(proj['tags'])}"
        vec = generate_local_embedding(doc)
        HISTORIC_EMBEDDINGS.append((proj, vec))
    print("✅ RAG initialized.")

# ==============================================================================
# 5. PIPELINE STATE & LANGGRAPH NODES
# ==============================================================================

class PipelineState(TypedDict):
    form_data: Dict[str, Any]
    max_rag_score: float
    best_matching_project: Optional[Dict[str, Any]]
    facts: Optional[CategoricalFactExtraction]
    score: int
    sub_scores: Dict[str, int]
    veto_triggered: bool
    veto_reasons: List[str]
    decision: str  # "GO", "NO_GO", "NEEDS_CLARIFICATION", "FAST_TRACK"
    clarification_round: int
    clarification_questions: List[Dict[str, str]]
    clarification_answers: List[str]
    final_report: str

def node_rag_search(state: PipelineState) -> Dict[str, Any]:
    """In-memory RAG search node."""
    form = state.get("form_data", {})
    query = f"{form.get('project_name', '')} {form.get('problem_description', '')}"
    q_vec = generate_local_embedding(query)
    
    best_score = 0.0
    best_proj = None
    
    for proj, p_vec in HISTORIC_EMBEDDINGS:
        sim = cosine_similarity(q_vec, p_vec)
        if sim > best_score:
            best_score = sim
            best_proj = proj

    return {
        "max_rag_score": round(best_score, 4),
        "best_matching_project": best_proj if best_score >= RAG_SIMILAR_THRESHOLD else None
    }

def node_llm_analyze(state: PipelineState) -> Dict[str, Any]:
    """LLM Judge Node — extracts categorical enums and justifications."""
    form = state.get("form_data", {})
    round_num = state.get("clarification_round", 0)
    questions = state.get("clarification_questions", [])
    answers = state.get("clarification_answers", [])
    
    system_prompt = (
        "You are the Principal AI Architect at Segula Technologies.\n"
        "Your role is to rigorously classify internal enterprise project proposals across 5 universal pillars.\n"
        "Be objective and strict: if a task is a deterministic script, cooling installation, or impossible prediction, classify it accurately.\n"
        "If previous clarification questions were answered by the user, factor those new details into your evaluation."
    )
    
    clarification_text = ""
    if round_num > 0 and questions and answers:
        clarification_text = "\n### Clarification Q&A History:\n"
        for i, (q, a) in enumerate(zip(questions, answers), 1):
            q_str = q.get("question", str(q)) if isinstance(q, dict) else str(q)
            clarification_text += f"- Question {i}: {q_str}\n  User Clarification: {a}\n"
    
    user_prompt = f"""
### Submission Details:
- Project Name: {form.get('project_name')}
- Department: {form.get('department')}
- Problem Description: {form.get('problem_description')}
- Current Process: {form.get('current_process')}
- Expected Outcome: {form.get('expected_outcome')}
- Data Description: {form.get('data_description')}
{clarification_text}

Classify this project under the 5 Universal Categorical Pillars taking all details and clarifications into account.
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    facts: CategoricalFactExtraction = execute_llm_call(messages, response_schema=CategoricalFactExtraction)
    return {"facts": facts}

def node_deterministic_score(state: PipelineState) -> Dict[str, Any]:
    """Python Deterministic Calculator & Circuit Breaker Veto Node."""
    rag_score = state.get("max_rag_score", 0.0)
    
    # 1. Check Fast-Track Bypass
    if rag_score >= RAG_EXACT_MATCH_THRESHOLD:
        return {
            "score": 95,
            "sub_scores": {"ai_viability": 30, "data_readiness": 25, "problem_clarity": 20, "integration": 10, "governance": 10},
            "veto_triggered": False,
            "veto_reasons": [],
            "decision": "FAST_TRACK"
        }
    
    facts: CategoricalFactExtraction = state.get("facts")
    if not facts:
        return {"score": 0, "decision": "NO_GO", "veto_triggered": True, "veto_reasons": ["Fact extraction failed"]}
    
    # 2. Point Mapping (Sums to 100 base)
    POINTS_AI = {"HIGHLY_VIABLE": 30, "MARGINAL": 15, "NOT_AI": 0, "IMPOSSIBLE": 0}
    POINTS_DATA = {"READY": 25, "UNLABELED_OR_MESSY": 10, "NONE": 0}
    POINTS_CLARITY = {"CLEAR": 20, "PARTIAL": 10, "CONTRADICTORY": 0, "VAGUE": 0}
    POINTS_INTEGRATION = {"SIMPLE": 15, "MODERATE": 10, "COMPLEX": 5}
    POINTS_GOVERNANCE = {"SAFE": 10, "MODERATE_RISK": 5, "CRITICAL_RISK": 0}
    
    sub_scores = {
        "ai_viability": POINTS_AI.get(facts.ai_viability.category, 0),
        "data_readiness": POINTS_DATA.get(facts.data_readiness.category, 0),
        "problem_clarity": POINTS_CLARITY.get(facts.problem_clarity.category, 0),
        "integration": POINTS_INTEGRATION.get(facts.integration_feasibility.category, 0),
        "governance": POINTS_GOVERNANCE.get(facts.governance_and_safety.category, 0),
    }
    
    total_score = sum(sub_scores.values())
    
    # Prior Art Non-Penalizing Boost
    if rag_score >= RAG_SIMILAR_THRESHOLD:
        total_score = min(100, total_score + 5)
        
    veto_reasons = []
    
    # 3. Circuit Breaker Veto Gates
    if facts.ai_viability.category in ["NOT_AI", "IMPOSSIBLE"]:
        total_score = min(total_score, 18)
        veto_reasons.append(f"AI Viability VETO: {facts.ai_viability.category} ({facts.ai_viability.reason})")
        
    if facts.governance_and_safety.category == "CRITICAL_RISK":
        total_score = min(total_score, 10)
        veto_reasons.append(f"Ethical/Security VETO: {facts.governance_and_safety.reason}")
        
    if facts.problem_clarity.category == "CONTRADICTORY":
        total_score = min(total_score, 45)
        veto_reasons.append(f"Contradiction VETO: {facts.problem_clarity.reason}")
        
    if facts.data_readiness.category == "NONE":
        total_score = min(total_score, 45)
        veto_reasons.append(f"Data VETO: {facts.data_readiness.reason}")
        
    veto_triggered = len(veto_reasons) > 0
    
    # 4. Final Routing Decision
    if total_score >= SCORE_GO_THRESHOLD:
        decision = "GO"
    elif total_score < SCORE_NOGO_THRESHOLD:
        decision = "NO_GO"
    else:
        decision = "NEEDS_CLARIFICATION"
        
    return {
        "score": total_score,
        "sub_scores": sub_scores,
        "veto_triggered": veto_triggered,
        "veto_reasons": veto_reasons,
        "decision": decision
    }

def node_generate_questions(state: PipelineState) -> Dict[str, Any]:
    """Generates targeted clarifying questions for weak pillars."""
    facts: CategoricalFactExtraction = state.get("facts")
    sub_scores = state.get("sub_scores", {})
    veto_reasons = state.get("veto_reasons", [])
    
    prompt = f"""
The project requires clarification before a final feasibility decision can be made.
Sub-Scores: {sub_scores}
Identified Blockers: {veto_reasons}
Facts: {facts.model_dump_json()}

Generate 2-3 precise questions targeted at resolving the data, scope, or clarity ambiguities.
"""
    messages = [
        {"role": "system", "content": "You are an AI requirements specialist generating clarifying questions for a project owner."},
        {"role": "user", "content": prompt}
    ]
    
    result: ClarificationQuestionsModel = execute_llm_call(
        messages, response_schema=ClarificationQuestionsModel, temperature=LLM_TEMPERATURE_CLARIFICATION
    )
    return {"clarification_questions": [q.model_dump() for q in result.questions]}

def node_generate_report(state: PipelineState) -> Dict[str, Any]:
    """Generates the Markdown feasibility dossier."""
    decision = state.get("decision")
    score = state.get("score")
    facts: CategoricalFactExtraction = state.get("facts")
    sub = state.get("sub_scores", {})
    veto = state.get("veto_reasons", [])
    rag = state.get("max_rag_score", 0.0)
    best_proj = state.get("best_matching_project")
    round_num = state.get("clarification_round", 0)
    
    proj_info = f"- **Parent Project Match:** {best_proj['project_name']} (Similarity: {rag*100:.1f}%)" if best_proj else f"- **RAG Similarity:** {rag*100:.1f}% (Novel Project)"

    report = f"""# 📋 AI Project Feasibility Dossier

## 🎯 Executive Verdict: **{decision}** (Feasibility Score: **{score}/100**)
- **Clarification Round:** {round_num} / {MAX_CLARIFICATION_ROUNDS}
{proj_info}

---

### 📊 5-Pillar Rubric Breakdown:
1. **AI Technical Viability:** `{facts.ai_viability.category if facts else 'N/A'}` ({sub.get('ai_viability', 0)}/30 pts)
   - *Rationale:* {facts.ai_viability.reason if facts else 'N/A'}
2. **Data Readiness & Labels:** `{facts.data_readiness.category if facts else 'N/A'}` ({sub.get('data_readiness', 0)}/25 pts)
   - *Rationale:* {facts.data_readiness.reason if facts else 'N/A'}
3. **Problem Scope & Clarity:** `{facts.problem_clarity.category if facts else 'N/A'}` ({sub.get('problem_clarity', 0)}/20 pts)
   - *Rationale:* {facts.problem_clarity.reason if facts else 'N/A'}
4. **Integration Feasibility:** `{facts.integration_feasibility.category if facts else 'N/A'}` ({sub.get('integration', 0)}/15 pts)
   - *Rationale:* {facts.integration_feasibility.reason if facts else 'N/A'}
5. **Governance & Ethics:** `{facts.governance_and_safety.category if facts else 'N/A'}` ({sub.get('governance', 0)}/10 pts)
   - *Rationale:* {facts.governance_and_safety.reason if facts else 'N/A'}

---

### 🚨 Veto & Risk Alerts:
{chr(10).join(f"- ⚠️ {r}" for r in veto) if veto else "✅ No critical veto flags encountered."}

### 💡 Recommended Next Steps:
- **Technical Path:** {facts.identified_technique if facts else 'Standard Python script or review'}
"""
    return {"final_report": report}

# ==============================================================================
# 6. LANGGRAPH ORCHESTRATION PIPELINE
# ==============================================================================

def route_after_score(state: PipelineState) -> str:
    decision = state.get("decision")
    round_num = state.get("clarification_round", 0)
    if decision == "NEEDS_CLARIFICATION" and round_num < MAX_CLARIFICATION_ROUNDS:
        return "generate_questions"
    return "generate_report"

builder = StateGraph(PipelineState)
builder.add_node("rag_search", node_rag_search)
builder.add_node("llm_analyze", node_llm_analyze)
builder.add_node("deterministic_score", node_deterministic_score)
builder.add_node("generate_questions", node_generate_questions)
builder.add_node("generate_report", node_generate_report)

builder.set_entry_point("rag_search")
builder.add_edge("rag_search", "llm_analyze")
builder.add_edge("llm_analyze", "deterministic_score")
builder.add_conditional_edges("deterministic_score", route_after_score, {
    "generate_questions": "generate_questions",
    "generate_report": "generate_report"
})
builder.add_edge("generate_questions", "generate_report")
builder.add_edge("generate_report", END)

pipeline_app = builder.compile()

# ==============================================================================
# 7. TKINTER GRAPHICAL USER INTERFACE (WITH INTERACTIVE CLARIFICATION)
# ==============================================================================

class EvaluatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Requirement Hub — 5-Pillar Engine Tester")
        self.root.geometry("1200x900")
        
        self.current_state: Optional[PipelineState] = None
        self.clarification_widgets = []
        
        # Style
        style = ttk.Style()
        style.theme_use("clam")
        
        # Main Frame
        main_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left Panel (Inputs & Clarification inside scrollable container)
        left_container = ttk.Frame(main_pane, width=480)
        main_pane.add(left_container, weight=1)
        
        self.left_canvas = tk.Canvas(left_container, borderwidth=0, highlightthickness=0)
        self.left_scroll = ttk.Scrollbar(left_container, orient=tk.VERTICAL, command=self.left_canvas.yview)
        self.left_frame = ttk.Frame(self.left_canvas)
        
        self.left_window_id = self.left_canvas.create_window((0, 0), window=self.left_frame, anchor="nw")
        
        def _on_frame_configure(e):
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
            
        def _on_canvas_configure(e):
            # Keep inner frame matching canvas width
            self.left_canvas.itemconfig(self.left_window_id, width=e.width)

        self.left_frame.bind("<Configure>", _on_frame_configure)
        self.left_canvas.bind("<Configure>", _on_canvas_configure)
        self.left_canvas.configure(yscrollcommand=self.left_scroll.set)
        
        self.left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Mouse wheel support on Linux (Button-4/5) and Windows/macOS (MouseWheel)
        def _on_mousewheel(event):
            if event.num == 4 or event.delta > 0:
                self.left_canvas.yview_scroll(-2, "units")
            elif event.num == 5 or event.delta < 0:
                self.left_canvas.yview_scroll(2, "units")

        self.left_canvas.bind_all("<Button-4>", _on_mousewheel)
        self.left_canvas.bind_all("<Button-5>", _on_mousewheel)
        self.left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        ttk.Label(self.left_frame, text="📝 Project Submission Form", font=("Helvetica", 13, "bold")).pack(anchor=tk.W, pady=(0, 6))
        
        # Preset Selector Bar
        preset_box = ttk.LabelFrame(self.left_frame, text="📂 Load Benchmark Test Case", padding=6)
        preset_box.pack(fill=tk.X, pady=(0, 8))
        
        preset_names = [f"Case {c['case_id']}: {c['form']['project_name'][:35]}" for c in BENCHMARK_PRESETS]
        self.combo_presets = ttk.Combobox(preset_box, values=preset_names, state="readonly", font=("Helvetica", 9))
        self.combo_presets.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.combo_presets.current(0)
        
        btn_load = tk.Button(
            preset_box, text="📥 Load", bg="#0284c7", fg="white", font=("Helvetica", 8, "bold"),
            relief=tk.FLAT, padx=6, pady=2, command=self.load_selected_preset
        )
        btn_load.pack(side=tk.LEFT, padx=(0, 4))
        
        btn_clear = tk.Button(
            preset_box, text="🧹 Clear", bg="#64748b", fg="white", font=("Helvetica", 8, "bold"),
            relief=tk.FLAT, padx=6, pady=2, command=self.clear_form
        )
        btn_clear.pack(side=tk.LEFT)
        
        self.entries = {}
        fields = [
            ("Project Name", "Supplier Invoice OCR & Purchase Order Reconciliation"),
            ("Department", "corporate_support"),
            ("Problem Description", "Accounts payable receives 1,200 PDF invoices monthly. Two accountants manually compare invoice line items against SAP ERP purchase orders, taking ~35 hours per week with a 4% human error rate."),
            ("Current Process", "Accountants manually open each PDF, check vendor VAT, match line items with SAP table ME23N, and flag discrepancies by email."),
            ("Expected Outcome", "Automated OCR extraction and fuzzy line-item matching against SAP POs, automatically validating invoices under 5,000€ and flagging mismatches for human review."),
            ("Data Description", "3 years of historical PDF invoices (36,000 files) with corresponding SAP ERP transactional settlement logs and discrepancy tags in SQL.")
        ]
        
        for label, default_val in fields:
            ttk.Label(self.left_frame, text=label, font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=(4, 2))
            if label in ["Problem Description", "Current Process", "Expected Outcome", "Data Description"]:
                txt = scrolledtext.ScrolledText(self.left_frame, height=3, width=45, wrap=tk.WORD, font=("Helvetica", 9))
                txt.insert(tk.END, default_val)
                txt.pack(fill=tk.X, pady=(0, 4))
                self.entries[label] = txt
            else:
                ent = ttk.Entry(self.left_frame, font=("Helvetica", 10))
                ent.insert(0, default_val)
                ent.pack(fill=tk.X, pady=(0, 4))
                self.entries[label] = ent
                
        # Run Button
        self.btn_run = tk.Button(
            self.left_frame, text="🚀 Evaluate Feasibility (Initial Run)", bg="#2563eb", fg="white",
            font=("Helvetica", 11, "bold"), relief=tk.FLAT, pady=8, command=self.run_initial_evaluation
        )
        self.btn_run.pack(fill=tk.X, pady=(12, 10))
        
        # Clarification Questions Frame (Dynamic)
        self.clarify_container = ttk.LabelFrame(self.left_frame, text="💬 Interactive Clarification Session", padding=10)
        # Hidden initially
        
        # Right Panel (Output & Diagnostics)
        right_frame = ttk.Frame(main_pane, width=650)
        main_pane.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text="📊 Live Diagnostic Results", font=("Helvetica", 13, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Status Badge Frame
        badge_frame = ttk.Frame(right_frame)
        badge_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.lbl_decision = tk.Label(badge_frame, text="DECISION: IDLE", bg="#64748b", fg="white", font=("Helvetica", 12, "bold"), padx=12, pady=6)
        self.lbl_decision.pack(side=tk.LEFT, padx=(0, 10))
        
        self.lbl_score = tk.Label(badge_frame, text="SCORE: — / 100", bg="#334155", fg="white", font=("Helvetica", 12, "bold"), padx=12, pady=6)
        self.lbl_score.pack(side=tk.LEFT, padx=(0, 10))
        
        self.lbl_round = tk.Label(badge_frame, text="ROUND: 0/2", bg="#475569", fg="white", font=("Helvetica", 10, "bold"), padx=8, pady=6)
        self.lbl_round.pack(side=tk.LEFT)
        
        # Output Text Area
        self.txt_output = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=("Courier", 10))
        self.txt_output.pack(fill=tk.BOTH, expand=True)

    def clear_form(self):
        for label, widget in self.entries.items():
            if isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
            else:
                widget.delete("1.0", tk.END)
        self.clarify_container.pack_forget()

    def load_selected_preset(self):
        idx = self.combo_presets.current()
        if idx >= 0 and idx < len(BENCHMARK_PRESETS):
            case = BENCHMARK_PRESETS[idx]["form"]
            self.clear_form()
            self.entries["Project Name"].insert(0, case.get("project_name", ""))
            self.entries["Department"].insert(0, case.get("department", "corporate_support"))
            self.entries["Problem Description"].insert(tk.END, case.get("problem_description", ""))
            self.entries["Current Process"].insert(tk.END, case.get("current_process", ""))
            self.entries["Expected Outcome"].insert(tk.END, case.get("expected_outcome", ""))
            self.entries["Data Description"].insert(tk.END, case.get("data_description", ""))
            self.txt_output.delete("1.0", tk.END)
            self.lbl_decision.config(text="DECISION: PENDING", bg="#64748b")
            self.lbl_score.config(text="SCORE: -- / 100")
            self.lbl_round.config(text="ROUND: 0/2")

    def run_initial_evaluation(self):
        form_data = {
            "project_name": self.entries["Project Name"].get(),
            "department": self.entries["Department"].get(),
            "problem_description": self.entries["Problem Description"].get("1.0", tk.END).strip(),
            "current_process": self.entries["Current Process"].get("1.0", tk.END).strip(),
            "expected_outcome": self.entries["Expected Outcome"].get("1.0", tk.END).strip(),
            "data_description": self.entries["Data Description"].get("1.0", tk.END).strip(),
        }
        
        self.btn_run.config(state=tk.DISABLED, text="⏳ Running Evaluation...")
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, "🚀 Initializing LangGraph state...\n")
        self.root.update()
        
        try:
            initial_state: PipelineState = {
                "form_data": form_data,
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
            
            result = pipeline_app.invoke(initial_state)
            self.current_state = result
            self.update_ui_with_result(result)
            
        except Exception as e:
            messagebox.showerror("Execution Error", str(e))
            self.txt_output.insert(tk.END, f"\n❌ ERROR: {e}\n")
        finally:
            self.btn_run.config(state=tk.NORMAL, text="🚀 Evaluate Feasibility (Initial Run)")

    def update_ui_with_result(self, result: PipelineState):
        dec = result.get("decision", "UNKNOWN")
        score = result.get("score", 0)
        round_num = result.get("clarification_round", 0)
        
        colors = {
            "GO": "#16a34a",
            "FAST_TRACK": "#0284c7",
            "NEEDS_CLARIFICATION": "#d97706",
            "NO_GO": "#dc2626"
        }
        self.lbl_decision.config(text=f"DECISION: {dec}", bg=colors.get(dec, "#64748b"))
        self.lbl_score.config(text=f"SCORE: {score} / 100")
        self.lbl_round.config(text=f"ROUND: {round_num}/{MAX_CLARIFICATION_ROUNDS}")
        
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, result.get("final_report", "No report generated."))
        
        # Render Clarification Answering Form if in NEEDS_CLARIFICATION
        questions = result.get("clarification_questions", [])
        if dec == "NEEDS_CLARIFICATION" and questions and round_num < MAX_CLARIFICATION_ROUNDS:
            self.render_clarification_inputs(questions, round_num)
        else:
            self.clarify_container.pack_forget()

    def render_clarification_inputs(self, questions: List[Dict[str, str]], current_round: int):
        # Clear previous inputs
        for w in self.clarify_container.winfo_children():
            w.destroy()
        self.clarification_widgets = []
        
        self.clarify_container.pack(fill=tk.X, pady=(10, 10))
        ttk.Label(
            self.clarify_container,
            text=f"❓ Clarification Round {current_round + 1} of {MAX_CLARIFICATION_ROUNDS}\nPlease provide additional details below:",
            font=("Helvetica", 10, "bold"),
            foreground="#d97706"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        for idx, q in enumerate(questions, 1):
            q_text = q.get("question", "")
            target = q.get("target_pillar", "")
            
            lbl_q = ttk.Label(self.clarify_container, text=f"Q{idx} [{target}]: {q_text}", wraplength=420, font=("Helvetica", 9, "bold"))
            lbl_q.pack(anchor=tk.W, pady=(4, 2))
            
            txt_ans = scrolledtext.ScrolledText(self.clarify_container, height=2, width=45, wrap=tk.WORD, font=("Helvetica", 9))
            txt_ans.pack(fill=tk.X, pady=(0, 6))
            self.clarification_widgets.append(txt_ans)
            
        btn_submit_answers = tk.Button(
            self.clarify_container,
            text=f"💬 Submit Answers & Re-Evaluate (Round {current_round + 1})",
            bg="#d97706", fg="white", font=("Helvetica", 10, "bold"), relief=tk.FLAT, pady=6,
            command=self.submit_clarification_answers
        )
        btn_submit_answers.pack(fill=tk.X, pady=(6, 2))
        
        # Update canvas scroll region and auto-scroll down to clarification questions
        self.root.update_idletasks()
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
        self.left_canvas.yview_moveto(0.6)

    def submit_clarification_answers(self):
        if not self.current_state:
            return
            
        answers = [txt.get("1.0", tk.END).strip() for txt in self.clarification_widgets]
        if any(not a for a in answers):
            messagebox.showwarning("Incomplete Answers", "Please answer all clarification questions before submitting.")
            return
            
        # Update State
        self.current_state["clarification_round"] += 1
        self.current_state["clarification_answers"] = answers
        
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, f"⏳ Submitting answers for Round {self.current_state['clarification_round']} and re-evaluating...\n")
        self.root.update()
        
        try:
            # Re-run pipeline from llm_analyze with answers included
            result = pipeline_app.invoke(self.current_state)
            self.current_state = result
            self.update_ui_with_result(result)
        except Exception as e:
            messagebox.showerror("Clarification Error", str(e))
            self.txt_output.insert(tk.END, f"\n❌ ERROR: {e}\n")

# ==============================================================================
# 8. ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    init_rag()
    if TKINTER_AVAILABLE:
        root = tk.Tk()
        app = EvaluatorGUI(root)
        root.mainloop()
    else:
        print("\n" + "="*80)
        print("⚠️  Tkinter is not installed on this Python environment.")
        print("💡 To enable the GUI, install it via system package manager: sudo apt install python3-tk")
        print("🚀 Running default sample evaluation in Terminal Mode:")
        print("="*80 + "\n")
        
        sample_input: PipelineState = {
            "form_data": {
                "project_name": "Supplier Invoice OCR & PO Matching",
                "department": "corporate_support",
                "problem_description": "Accounts payable receives 1,200 PDF invoices monthly. Two accountants manually compare invoice line items against SAP ERP purchase orders, taking 35h/wk with 4% human error.",
                "current_process": "Accountants manually open PDFs, verify VAT numbers, and match items in SAP ME23N table.",
                "expected_outcome": "Automated OCR extraction and fuzzy line-item matching against SAP POs, automatically validating invoices under 5,000€.",
                "data_description": "3 years of historical PDF invoices (36,000 files) with corresponding SAP ERP transactional settlement logs."
            },
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
        res = pipeline_app.invoke(sample_input)
        print(res.get("final_report", ""))

