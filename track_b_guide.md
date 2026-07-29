# Track B Guide — "Decision" Engineer

> **Your branch:** `feature/track-b`
> **Your job:** Everything deterministic — scoring, validation, reports, file parsing.

---

## Files You OWN (edit freely)

```
backend/nodes/parse_input.py               # Extract text from PDF/Excel
backend/nodes/validate_completeness.py     # Check required fields per department
backend/nodes/deterministic_score.py       # Scoring engine (fixed weights, pure Python)
backend/nodes/generate_report.py           # Build cahier de charge from template
backend/data/department_configs.json       # Department form fields + validation rules
tests/test_scoring.py
tests/test_validation.py
```

## Files you must NOT touch

```
❌ backend/services/llm.py                 # Track A
❌ backend/services/vectorstore.py         # Track A
❌ backend/nodes/rag_search.py             # Track A
❌ backend/nodes/fast_track.py             # Track A
❌ backend/nodes/llm_analyze.py            # Track A
❌ backend/nodes/generate_questions.py     # Track A
❌ backend/prompts/*                       # Track A
❌ backend/data/historic_projects.json     # Track A
❌ tests/test_rag.py                       # Track A
❌ tests/test_llm_analyze.py              # Track A
```

If you need something from these → tell Person A, they edit their file.

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

### Step 1: Department Config (`data/department_configs.json`)
Create the Corporate & Support Services config with form fields (service_area, target_users, estimated_user_count, has_existing_system) + required base fields. Also add disabled placeholder entries for System Dev, Industrial Performance, etc.

### Step 2: Validation Node (`nodes/validate_completeness.py`)
Load department config. Check all required_base_fields + required specific_fields are present and non-empty. Return missing_fields list and is_complete boolean.

### Step 3: File Parser Node (`nodes/parse_input.py`)
Accept uploaded file paths. For PDF: extract text with pdfplumber. For Excel/CSV: extract with pandas as readable text. For unsupported types: return "[Unsupported file]". Return parsed_files_text list.

### Step 4: Scoring Engine (`nodes/deterministic_score.py`)
**This is your most important file.** Pure Python, zero LLM calls.

```python
def calculate_feasibility_score(facts: dict, similar_projects: list, rag_scores: list) -> dict:
    score = 0
    breakdown = {}

    # Problem clarity (20 pts)
    s = 20 if facts["has_clear_problem_statement"] else 0
    breakdown["problem_clarity"] = {"score": s, "max": 20}
    score += s

    # AI solvability (15 pts)
    s = 15 if facts["problem_is_ai_solvable"] else 0
    breakdown["ai_solvability"] = {"score": s, "max": 15}
    score += s

    # Data availability (20 pts)
    data_map = {"none": 0, "partial": 10, "full": 20}
    s = data_map.get(facts["data_availability"], 0)
    breakdown["data_availability"] = {"score": s, "max": 20}
    score += s

    # Similar project exists (15 pts)
    if rag_scores and max(rag_scores) >= 0.95:
        s = 15  # exact match
    elif rag_scores and max(rag_scores) >= 0.60:
        s = 12  # similar exists
    else:
        s = 5   # novel — not penalized heavily
    breakdown["similar_projects"] = {"score": s, "max": 15}
    score += s

    # Research required (10 pts)
    s = 10 if not facts["requires_new_research"] else 3
    breakdown["research_needed"] = {"score": s, "max": 10}
    score += s

    # Technique identified (10 pts)
    s = 10 if facts["ai_technique_identified"] != "unknown" else 0
    breakdown["technique_clarity"] = {"score": s, "max": 10}
    score += s

    # Integration complexity (10 pts)
    complexity_map = {"low": 10, "medium": 7, "high": 3}
    s = complexity_map.get(facts["integration_complexity"], 5)
    breakdown["integration"] = {"score": s, "max": 10}
    score += s

    # Decision
    if score >= 70:
        decision = "GO"
    elif score >= 40:
        decision = "NEEDS_CLARIFICATION"
    else:
        decision = "NO_GO"

    return {
        "score": score,
        "percentage": score,  # max is 100
        "decision": decision,
        "breakdown": breakdown
    }
```

### Step 5: Report Generator (`nodes/generate_report.py`)
Build the cahier de charge as markdown from a template. Fill in: project overview, score breakdown table, problem statement, extracted requirements, similar projects, risks, recommended approach, uncertainties. Handle 3 report types: "go", "no_go", "partial".

### Step 6: Tests (`tests/test_scoring.py`, `tests/test_validation.py`)
Test every edge case in scoring: all perfect = 100, all worst = minimum, threshold boundaries (69 vs 70, 39 vs 40). Test validation: missing fields, complete submission, empty description.

---

## Git Workflow

```bash
# Start of day
git checkout feature/track-b
git pull origin main --rebase      # Get any contract changes

# During the day — commit often
git add backend/nodes/deterministic_score.py
git commit -m "Track B: scoring engine with 7 criteria"

# End of day
git push origin feature/track-b

# Contract change needed?
# 1. Tell Person A → both agree
# 2. One person edits on main, pushes
# 3. Both rebase: git pull origin main --rebase

# Integration day (Phase 3)
# Person A merges first, then you:
git checkout main
git pull origin main               # Get Person A's merge
git merge feature/track-b          # Zero conflicts — different files
git push origin main
```

---

## Test Independently (no need for Track A code)

You don't need the LLM or RAG to test your scoring. Use hardcoded dicts:

```python
# tests/test_scoring.py
from backend.nodes.deterministic_score import calculate_feasibility_score

# Test 1: Perfect score → GO
perfect_facts = {
    "has_clear_problem_statement": True,
    "problem_is_ai_solvable": True,
    "data_availability": "full",
    "requires_new_research": False,
    "ai_technique_identified": "classification",
    "integration_complexity": "low",
}
result = calculate_feasibility_score(perfect_facts, [], [0.98])
assert result["decision"] == "GO"
assert result["score"] == 100
print(f"✅ Perfect: {result['score']} → {result['decision']}")

# Test 2: Worst score → NO_GO
bad_facts = {
    "has_clear_problem_statement": False,
    "problem_is_ai_solvable": False,
    "data_availability": "none",
    "requires_new_research": True,
    "ai_technique_identified": "unknown",
    "integration_complexity": "high",
}
result = calculate_feasibility_score(bad_facts, [], [])
assert result["decision"] == "NO_GO"
print(f"✅ Worst: {result['score']} → {result['decision']}")

# Test 3: Edge case at threshold → 70 = GO, 69 = NEEDS_CLARIFICATION
# Build a facts dict that scores exactly 70, then tweak one field

# Test 4: Validation
from backend.nodes.validate_completeness import validate_completeness
state = {"form_data": {"project_name": "Test"}, "department": "corporate_support"}
result = validate_completeness(state)
assert len(result["missing_fields"]) > 0  # should be missing many fields
print(f"✅ Validation caught {len(result['missing_fields'])} missing fields")
```
