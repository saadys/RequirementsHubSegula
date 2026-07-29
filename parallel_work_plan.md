# AI Requirement Hub — Parallel Work Plan (2 Engineers)

## The Core Principle

Your LangGraph nodes are **independent functions**: each takes state in, returns state updates out. Two people can build different nodes in parallel **as long as you agree on the state schema first**.

```
┌─────────────────────────────────────────────────┐
│              SHARED CONTRACT (Day 1)            │
│    state.py · schemas.py · config.py            │
│         Both agree on this BEFORE splitting     │
└──────────────┬──────────────────┬───────────────┘
               │                  │
       ┌───────▼───────┐  ┌──────▼────────┐
       │   TRACK A     │  │   TRACK B     │
       │ "Understanding"│  │  "Decision"   │
       │               │  │               │
       │ • RAG setup   │  │ • Scoring     │
       │ • LLM analyze │  │ • Validation  │
       │ • Clarify Qs  │  │ • Report gen  │
       │ • Dept prompts│  │ • File parsing│
       └───────┬───────┘  └──────┬────────┘
               │                  │
       ┌───────▼──────────────────▼───────┐
       │         INTEGRATION (Together)    │
       │    graph.py · API routes · test   │
       └──────────────────────────────────┘
```

---

## Revised Project Structure (with ownership)

```
AI_requirement_hub/
│
├── backend/
│   ├── main.py                          # [TOGETHER] FastAPI entry
│   ├── config.py                        # [SHARED]   Settings, keys, thresholds
│   │
│   ├── contracts/                       # [SHARED — BUILD FIRST]
│   │   ├── state.py                     #   PipelineState TypedDict
│   │   └── schemas.py                   #   All Pydantic models
│   │
│   ├── nodes/                           # Each file = one graph node
│   │   ├── parse_input.py               # [TRACK B]  File parsing logic
│   │   ├── validate_completeness.py     # [TRACK B]  Rule-based field checks
│   │   ├── rag_search.py                # [TRACK A]  Vector search
│   │   ├── fast_track.py                # [TRACK A]  Exact match handler
│   │   ├── llm_analyze.py              # [TRACK A]  LLM fact extraction
│   │   ├── deterministic_score.py       # [TRACK B]  Scoring engine
│   │   ├── generate_questions.py        # [TRACK A]  Clarification Qs
│   │   └── generate_report.py           # [TRACK B]  Cahier de charge
│   │
│   ├── graph/
│   │   ├── builder.py                   # [TOGETHER] Wire nodes + edges
│   │   └── routing.py                   # [TOGETHER] Conditional edge functions
│   │
│   ├── services/
│   │   ├── llm.py                       # [TRACK A]  LiteLLM Router setup
│   │   └── vectorstore.py              # [TRACK A]  ChromaDB setup
│   │
│   ├── prompts/
│   │   ├── base.py                      # [TRACK A]  Shared prompt parts
│   │   └── manufacturing.py             # [TRACK A]  MVP department prompt
│   │
│   ├── api/
│   │   ├── routes_submissions.py        # [TOGETHER]
│   │   ├── routes_clarification.py      # [TOGETHER]
│   │   └── routes_dashboard.py          # [TOGETHER]
│   │
│   └── data/
│       ├── historic_projects.json       # [TRACK A]  Seed RAG data
│       └── department_configs.json      # [TRACK B]  Form field configs
│
├── frontend/                            # [PHASE 3 — TOGETHER]
│   └── ...
│
├── tests/
│   ├── test_scoring.py                  # [TRACK B]
│   ├── test_rag.py                      # [TRACK A]
│   ├── test_llm_analyze.py             # [TRACK A]
│   ├── test_validation.py              # [TRACK B]
│   └── test_graph_e2e.py               # [TOGETHER]
│
├── requirements.txt
├── .env.example
└── README.md
```

**Key change from previous structure:** `nodes/` directory with **one file per node**. This is what eliminates merge conflicts — each person owns different files entirely.

---

## Track Assignments

### Track A — "Understanding" (You or your co-intern)

**What you own:** Everything that touches the LLM and knowledge base.

| File | What to Build |
|---|---|
| `services/llm.py` | LiteLLM Router with Gemini keys + fallback |
| `services/vectorstore.py` | ChromaDB collection setup, embed + store + search functions |
| `nodes/rag_search.py` | Embed the request, query ChromaDB, return similar projects |
| `nodes/fast_track.py` | Handle exact match: format existing solution response |
| `nodes/llm_analyze.py` | Call LLM with structured output → FactExtraction |
| `nodes/generate_questions.py` | Generate targeted clarification questions from gaps in facts |
| `prompts/base.py` | Common system prompt structure |
| `prompts/manufacturing.py` | Manufacturing-specific prompt (MVP department) |
| `data/historic_projects.json` | Seed data: 10-15 fake but realistic past projects |
| `tests/test_rag.py` | Test retrieval accuracy |
| `tests/test_llm_analyze.py` | Test structured output extraction |

**You can test independently:** Give your LLM node a hardcoded form input → check it returns valid `FactExtraction` JSON. Give your RAG a query → check it returns relevant projects.

### Track B — "Decision" (The other intern)

**What you own:** Everything deterministic — scoring, validation, reports, parsing.

| File | What to Build |
|---|---|
| `nodes/parse_input.py` | Extract text from PDF (pdfplumber) and Excel (pandas) |
| `nodes/validate_completeness.py` | Check required fields per department, return missing list |
| `nodes/deterministic_score.py` | Scoring engine: facts dict → weighted score → decision |
| `nodes/generate_report.py` | Build cahier de charge from template + state data |
| `data/department_configs.json` | Department form fields, required fields, validation rules |
| `tests/test_scoring.py` | Test every scoring scenario (edge cases around thresholds) |
| `tests/test_validation.py` | Test completeness checks |

**You can test independently:** Feed hardcoded `FactExtraction` dicts into the scoring engine → verify scores and decisions. Feed test PDFs/Excels into the parser → verify text extraction.

---

## Phase Plan

### Phase 1: Contracts (Together, Day 1, ~2-3 hours)

**Both of you sit together** and agree on:

```python
# contracts/state.py — THE source of truth
class PipelineState(TypedDict):
    # Input
    form_data: dict
    department: str
    parsed_files: list[str]
    missing_fields: list[str]
    
    # RAG
    similar_projects: list[dict]
    is_exact_match: bool
    
    # LLM
    extracted_facts: dict | None
    
    # Clarification
    clarification_round: int
    clarification_questions: list[str]
    clarification_answers: list[str]
    
    # Scoring
    score: int
    score_breakdown: dict
    decision: str  # "GO" | "NO_GO" | "NEEDS_CLARIFICATION"
    
    # Output
    report: str
    report_type: str  # "full" | "partial" | "no_go" | "fast_track"
```

```python
# contracts/schemas.py — All Pydantic models
class FactExtraction(BaseModel):
    """What Track A's LLM returns, what Track B's scoring consumes."""
    has_clear_problem_statement: bool
    problem_is_ai_solvable: bool
    data_availability: Literal["none", "partial", "full"]
    # ... agree on EVERY field
```

Also set up:
- Git repo with branches
- `.env.example` with key names
- `requirements.txt` installed
- `config.py` with shared settings

### Phase 2: Parallel Build (Each on their track, 3-5 days)

```
Day 1:  [TOGETHER] Phase 1 contracts + repo setup
        
Day 2-4: [PARALLEL]
         Track A: llm.py → vectorstore.py → rag_search → llm_analyze → generate_questions
         Track B: parse_input → validate_completeness → deterministic_score → generate_report
         
Day 5:  [TOGETHER] Phase 3 integration
```

**Daily sync:** 15-min standup. "What I finished, what I'm doing today, am I blocked?"

If during Phase 2, someone realizes the contract needs a new field:
1. Tell the other person
2. Both agree
3. One person adds it to `contracts/state.py`
4. The other pulls

### Phase 3: Integration (Together, 1-2 days)

1. Wire all nodes into `graph/builder.py`
2. Write routing functions in `graph/routing.py`
3. Build API routes
4. Run end-to-end test

### Phase 4: Frontend (Together, 2-3 days)

Both work on frontend AFTER the backend pipeline works end-to-end. The frontend is:
- A form page (one person)
- A results/dashboard page (other person)
- Not complex enough to cause conflicts

---

## Why Frontend Last?

1. Your value is the **AI pipeline**, not the UI. A working backend you can demo with Postman/curl is already impressive
2. The frontend is just forms and displays — it maps 1:1 to your API endpoints
3. You need the API to be stable before building the frontend, otherwise you're changing both simultaneously
4. If time runs out, a working API + basic frontend beats a polished UI with a broken backend

---

## Git Strategy

```
main ──────────────────────────────────────────────────►
  │
  ├── feature/contracts ─── (Phase 1, together) ──► merge to main
  │
  ├── feature/track-a ───── (Phase 2, person A) ──► merge to main
  │
  ├── feature/track-b ───── (Phase 2, person B) ──► merge to main
  │
  ├── feature/integration ─ (Phase 3, together) ──► merge to main
  │
  └── feature/frontend ──── (Phase 4, together) ──► merge to main
```

**Why no conflicts:** Track A and Track B touch **completely different files**. The only shared files (`contracts/`) are set in Phase 1 and rarely change. If they do, one person makes the change, the other pulls.

---

## MVP Department: Manufacturing

One department only. Why Manufacturing:
- Clear AI use cases (predictive maintenance, visual inspection, process optimization)
- Data types are concrete (sensor data, images, production logs)
- Segula has deep Manufacturing expertise (from your posters)

Frontend shows all departments in the dropdown but only Manufacturing is functional. Others show: *"Coming soon — this department is not yet configured."*

---

## Communication Protocol

| When | What | How |
|---|---|---|
| Day 1 | Agree on contracts | Together, same screen |
| Daily | 15-min standup | "Done / Doing / Blocked" |
| When contract changes needed | Notify immediately | Message + update `contracts/` |
| Before integration | Both demo their nodes | Run individually, show output |
| Integration day | Pair program | Together, same screen |

### The One Rule

> **Never edit a file you don't own without telling the other person first.**

Track A never touches `deterministic_score.py`. Track B never touches `llm_analyze.py`. If you need something from the other track, you ask: *"Can you add a field X to the output?"* — and they do it in their file.
