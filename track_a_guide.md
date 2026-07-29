# Track A Guide — "Understanding" Engineer

> **Your branch:** `feature/track-a`
> **Your job:** Everything that touches the LLM and knowledge base.

---

## Files You OWN (edit freely)

```
backend/services/llm.py                  # LiteLLM Router setup
backend/services/vectorstore.py          # ChromaDB setup + operations
backend/nodes/rag_search.py              # Query ChromaDB → return similar projects
backend/nodes/fast_track.py              # Handle exact match (score ≥ 95%)
backend/nodes/llm_analyze.py             # Call LLM → return FactExtraction JSON
backend/nodes/generate_questions.py      # Generate clarification questions
backend/prompts/base.py                  # Shared system prompt structure
backend/prompts/corporate_support.py     # Department prompt
backend/data/historic_projects.json      # Seed data (IRFANE, Talentium, AutoCrashCheck, FleetIO)
tests/test_rag.py
tests/test_llm_analyze.py
```

## Files you must NOT touch

```
❌ backend/nodes/parse_input.py            # Track B
❌ backend/nodes/validate_completeness.py  # Track B
❌ backend/nodes/deterministic_score.py    # Track B
❌ backend/nodes/generate_report.py        # Track B
❌ backend/data/department_configs.json    # Track B
❌ tests/test_scoring.py                   # Track B
❌ tests/test_validation.py               # Track B
```

If you need something from these → tell Person B, they edit their file.

## Shared files — ASK BEFORE EDITING

```
⚠️ backend/contracts/state.py       # Both agree first
⚠️ backend/contracts/schemas.py     # Both agree first
⚠️ backend/config.py                # Both agree first
```

## Files built TOGETHER (Phase 3)

```
🤝 backend/graph/builder.py         # Integration day
🤝 backend/graph/routing.py         # Integration day
🤝 backend/api/*                    # Integration day
🤝 backend/main.py                  # Integration day
🤝 frontend/*                       # Phase 4
```

---

## Your Build Order

### Step 1: LiteLLM Router (`services/llm.py`)
Set up Router with Gemini keys + OpenAI fallback. Create `structured_llm = llm.with_structured_output(FactExtraction)`. Test: call LLM, get valid FactExtraction back.

### Step 2: ChromaDB (`services/vectorstore.py`)
Set up collection with text-embedding-004. Write `add_project()`, `search_similar()`, `get_by_id()`.

### Step 3: Seed Data (`data/historic_projects.json`)
Create entries for all 4 projects (IRFANE, Talentium, AutoCrashCheck, FleetIO) with: name, department, problem, solution, technique, outcome, contact, tags. Load into ChromaDB on startup.

### Step 4: RAG Search Node (`nodes/rag_search.py`)
Build query from form_data + parsed_files_text. Call vectorstore. Determine exact match (≥ 0.95). Return: similar_projects, rag_scores, is_exact_match.

### Step 5: Fast Track Node (`nodes/fast_track.py`)
Format exact match response: project name, solution, contact. Set report_type = "fast_track".

### Step 6: LLM Analyze Node (`nodes/llm_analyze.py`)
Build prompt with: department prompt + form data + RAG context + clarification answers. Call structured_llm → FactExtraction. Return extracted_facts as dict.

### Step 7: Generate Questions (`nodes/generate_questions.py`)
When score is 40-69, generate targeted questions from gaps in extracted_facts. Max 5 questions. Increment clarification_round.

### Step 8: Department Prompt (`prompts/corporate_support.py`)
System prompt for Corporate & Support Services. Include IRFANE + Talentium as reference projects.

---

## Git Workflow

```bash
# Start of day
git checkout feature/track-a
git pull origin main --rebase      # Get any contract changes

# During the day — commit often
git add backend/services/llm.py
git commit -m "Track A: LiteLLM router with Gemini keys"

# End of day
git push origin feature/track-a

# Contract change needed?
# 1. Tell Person B → both agree
# 2. One person edits on main, pushes
# 3. Both rebase: git pull origin main --rebase

# Integration day (Phase 3)
git checkout main
git merge feature/track-a          # You merge first
git push origin main
# Then Person B merges (zero conflicts — different files)
```

---

## Test Independently (no need for Track B code)

```python
# Quick test: does your pipeline work end-to-end?
fake_state = {
    "form_data": {
        "project_name": "Smart Onboarding Assistant",
        "department": "corporate_support",
        "problem_description": "New employees waste 2 weeks finding HR info...",
        "current_process": "Ask colleagues or search SharePoint manually",
        "expected_outcome": "AI chatbot answers HR questions instantly",
    },
    "parsed_files_text": [],
    "department": "corporate_support",
    "clarification_round": 0,
    "clarification_answers": [],
}

# Test RAG: should find IRFANE as similar
state = rag_search(fake_state)
print(f"Exact match: {state['is_exact_match']}")
print(f"Top match: {state['similar_projects'][0]}")

# Test LLM: should return valid FactExtraction
state = llm_analyze({**fake_state, **state})
print(f"Facts: {state['extracted_facts']}")
```
