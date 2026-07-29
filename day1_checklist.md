# Day 1 Checklist — AGREED ✅

> All items reviewed and agreed upon by both engineers.

---

## ✅ Item 1: PipelineState — AGREED

```python
# backend/contracts/state.py
from typing import TypedDict, Literal

class PipelineState(TypedDict, total=False):
    # ── Input (set by API route before graph starts) ──
    request_id: str
    form_data: dict
    department: str
    uploaded_files: list[str]
    
    # ── Parse & Validate (Track B writes, others read) ──
    parsed_files_text: list[str]
    missing_fields: list[str]
    is_complete: bool
    
    # ── RAG (Track A writes, scoring reads) ──
    similar_projects: list[dict]
    rag_scores: list[float]
    is_exact_match: bool
    exact_match_project: dict | None
    
    # ── LLM Analysis (Track A writes, Track B scoring reads) ──
    extracted_facts: dict | None
    
    # ── Clarification (both tracks interact) ──
    clarification_round: int
    clarification_questions: list[str]
    clarification_answers: list[str]
    
    # ── Scoring (Track B writes, report reads) ──
    score: int
    score_breakdown: dict
    decision: str  # "GO" | "NO_GO" | "NEEDS_CLARIFICATION"
    
    # ── Output (Track B writes) ──
    report: str
    report_type: str  # "go" | "no_go" | "partial" | "fast_track"
```

---

## ✅ Item 2: FactExtraction Schema — AGREED

```python
# backend/contracts/schemas.py
from pydantic import BaseModel, Field
from typing import Literal

class FactExtraction(BaseModel):
    """Structured facts the LLM extracts from a business team's AI request."""
    
    has_clear_problem_statement: bool = Field(
        description="The team clearly described what problem they want to solve"
    )
    problem_is_ai_solvable: bool = Field(
        description="The described problem can realistically be solved with AI/ML"
    )
    problem_category: Literal[
        "classification", "regression", "clustering", "nlp", 
        "computer_vision", "time_series", "recommendation",
        "optimization", "generative", "other", "unknown"
    ] = Field(description="The AI/ML problem type that best fits this request")
    
    data_availability: Literal["none", "partial", "full"] = Field(
        description="How much relevant data the team currently has"
    )
    data_volume_sufficient: Literal["yes", "no", "unknown"] = Field(
        description="Whether the described data volume is enough for the approach"
    )
    
    ai_technique_identified: str = Field(
        description="Specific AI technique recommended, or 'unknown'"
    )
    requires_new_research: bool = Field(
        description="Whether this requires research beyond established techniques"
    )
    integration_complexity: Literal["low", "medium", "high"] = Field(
        description="How complex it would be to integrate the AI solution"
    )
    estimated_effort: Literal["small", "medium", "large"] = Field(
        description="small (<4 weeks), medium (4-12), large (>12)"
    )
    
    risks_identified: list[str] = Field(
        description="List of potential risks or blockers"
    )
    extracted_requirements: list[str] = Field(
        description="Concrete requirements extracted from the request"
    )
    summary: str = Field(
        description="2-3 sentence summary of what the team needs"
    )
```

---

## ✅ Item 3: Other Pydantic Models — AGREED

```python
# Also in backend/contracts/schemas.py

class FormSubmission(BaseModel):
    project_name: str
    department: str
    team_contact_name: str
    team_contact_email: str
    problem_description: str
    current_process: str
    expected_outcome: str
    data_description: str | None = None
    deadline_urgency: Literal["low", "medium", "high", "critical"]
    department_specific: dict = {}

class ScoringResult(BaseModel):
    score: int
    percentage: int
    decision: Literal["GO", "NO_GO", "NEEDS_CLARIFICATION"]
    breakdown: dict

class ClarificationQuestions(BaseModel):
    questions: list[str] = Field(
        description="Targeted questions to clarify gaps, max 5 questions"
    )
    reasoning: list[str] = Field(
        description="Why each question is being asked (1:1 with questions)"
    )
```

---

## ✅ Item 4: Department — AGREED → Corporate & Support Services

Based on the 4 historic AI projects:
- **IRFANE** → internal chatbot (HR/IT document search) → maps to Corporate
- **Talentium** → AI recruitment system (CV scoring, multi-agent) → maps to Corporate
- AutoCrashCheck → System Dev (future department)
- FleetIO → Industrial Performance (future department)

```json
{
  "corporate_support": {
    "display_name": "Corporate & Support Services",
    "description": "HR, IT, Internal Tools, Recruitment, Onboarding, Knowledge Management",
    "enabled": true,
    "specific_fields": [
      {
        "name": "service_area",
        "label": "Service Area",
        "type": "select",
        "options": ["hr", "it", "finance", "legal", "facilities", "communication", "other"],
        "required": true
      },
      {
        "name": "target_users",
        "label": "Who will use this tool?",
        "type": "select",
        "options": ["employees", "managers", "hr_team", "it_team", "candidates", "external", "other"],
        "required": true
      },
      {
        "name": "estimated_user_count",
        "label": "Estimated Number of Users",
        "type": "select",
        "options": ["1-10", "10-50", "50-200", "200+"],
        "required": false
      },
      {
        "name": "has_existing_system",
        "label": "Is there an existing system/tool being used today?",
        "type": "boolean",
        "required": true
      }
    ],
    "required_base_fields": [
      "project_name", "team_contact_name", "team_contact_email",
      "problem_description", "current_process", "expected_outcome",
      "deadline_urgency"
    ]
  }
}
```

---

## ✅ Item 5: Scoring Weights — AGREED

| Criterion | Max Points | Source |
|---|---|---|
| Problem clarity | 20 | `has_clear_problem_statement` |
| AI solvability | 15 | `problem_is_ai_solvable` |
| Data availability | 20 | `data_availability` |
| Similar project exists | 15 | RAG results |
| Research required | 10 | `requires_new_research` |
| Technique identified | 10 | `ai_technique_identified` |
| Integration complexity | 10 | `integration_complexity` |
| **Total** | **100** | |

Thresholds: **≥ 70 = GO** · **40–69 = NEEDS_CLARIFICATION** · **< 40 = NO_GO**

---

## ✅ Item 6: Git Repo — AGREED

```bash
cd /home/aboubakr/Desktop/AI_requirement_hub
git init && git branch -M main

# .gitignore
echo ".env
__pycache__/
*.pyc
node_modules/
data/*.db
data/chroma/
.venv/
dist/" > .gitignore

# .env.example
echo "GEMINI_API_KEY_1=
GEMINI_API_KEY_2=
OPENAI_API_KEY=" > .env.example

# Commit contracts → create branches
git add -A
git commit -m "Phase 1: shared contracts and project skeleton"
git checkout -b feature/track-a    # Person A
git checkout main
git checkout -b feature/track-b    # Person B
```

---

## ✅ Item 7: Communication — AGREED

- Daily 15-min standup
- Never edit a file you don't own without telling the other person
- Contract changes require both to agree
- Commit often, push daily

---

## ✅ Item 8: Track Assignment — AGREED

- Decided between yourselves who is Track A and who is Track B
- See `track_a_guide.md` and `track_b_guide.md` for your individual instructions
