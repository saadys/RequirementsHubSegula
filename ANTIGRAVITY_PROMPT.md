# RequirementsHubSegula — Architecture Contract & Agent Prompt

> **How to use this file:** copy everything between the `=== BEGIN PROMPT ===` and
> `=== END PROMPT ===` markers and paste it into Antigravity (as a rules file, a
> `AGENTS.md`, or at the top of your session) **before** asking it to write, change,
> add or delete anything in this repository.
>
> It is written in English because the codebase's identifiers, docstrings and commit
> messages are English. User-facing UI strings stay French — that rule is inside the prompt.

---

=== BEGIN PROMPT ===

# SYSTEM CONTRACT — RequirementsHubSegula (Segula AI Requirement Hub)

You are contributing to an existing, working, multi-author codebase. It is **not** a
greenfield project. Your job is to extend it **in its own idiom**, not to introduce
yours. A change that works but breaks the conventions below is a rejected change.

Read this entire document before your first edit. When a rule here conflicts with your
default instincts, **this document wins**.

---

## 0. WHAT THIS PRODUCT IS (so you don't design the wrong thing)

Segula's business departments submit AI project requests through a web form. A
**LangGraph pipeline** parses them, validates completeness, searches historic projects
via **RAG (pgvector)**, extracts structured facts with an **LLM**, then scores them
with **pure deterministic Python** and routes to `GO` / `NO_GO` /
`NEEDS_CLARIFICATION`. Clarification loops back to the user (max 2 rounds). The final
artifact is a Markdown *cahier des charges*. An AI engineer reviews everything in an
admin dashboard and can override the decision — with a full audit trail.

Two personas, one backend, one repo (**monorepo — this is a settled decision, do not
propose splitting it**):

| Persona | Route | Sees |
|---|---|---|
| Business submitter | `/portal` | Guided wizard, readable status. **Never** score, breakdown, reviewer notes, override flags, raw enums |
| AI engineer / admin | `/admin` | Everything: raw score, 7-criteria breakdown, fact extraction, overrides, reports |

---

## 1. THE THREE INVARIANTS (violating any of these is a hard failure)

### INVARIANT 1 — The LLM never decides. Python decides.

The LLM's only job is `nodes/llm_analyze.py` → produce a `FactExtraction` Pydantic
object, and `nodes/generate_questions.py` → produce clarification questions.

**The GO / NO_GO / NEEDS_CLARIFICATION decision is computed by pure Python** in
`backend/nodes/deterministic_score.py::calculate_feasibility_score` — no LLM call, no
randomness, no network. Same facts in ⇒ same score out, forever.

- Never ask the LLM for a score, a decision, or a threshold judgement.
- Never move scoring logic into a prompt.
- Never add an LLM call inside `deterministic_score.py`, `validate_completeness.py`
  or `parse_input.py`.

This is the product's auditability guarantee. It is why `fact_extractions` and
`scoring_results` are separate DB tables: business rules can be re-run without paying
for or waiting on the LLM again.

### INVARIANT 2 — `contracts/state.py` and `backend/schemas/` are the shared contract.

`backend/contracts/state.py` carries the literal warning:
`⚠️ SHARED FILE — Do not edit without agreement from both engineers.`

Treat `backend/contracts/state.py`, `backend/schemas/Schemas.py`, `backend/schemas/Enums.py`
and `backend/config.py` as **frozen unless explicitly asked**. If your task genuinely
requires a new state key or a new schema field:

1. Do it as an **additive** change only (new optional key / new field with a default).
2. Never rename or remove an existing key/field.
3. Say so loudly in your summary: *"⚠️ SHARED CONTRACT CHANGED: added `x` to
   PipelineState — Track A and Track B must pull."*

### INVARIANT 3 — Audit history is append-only.

An AI engineer overriding a decision **never mutates** `scoring_results`. It writes a
new row into `reviewer_overrides` (`previous_decision`, `new_decision`,
`reviewer_name`, `reviewer_notes`) and updates `submissions.status`. The original
machine score must remain readable forever. Any feature touching decisions follows
this pattern.

---

## 2. LAYERED ARCHITECTURE — DEPENDENCIES FLOW ONE WAY

```
                    backend/main.py            (FastAPI app, lifespan, CORS)
                          │
                    backend/api/router.py      (aggregates sub-routers under /api)
                          │
        ┌─────────────────┴──────────────────┐
        ▼                                    ▼
  backend/api/routes_*.py             backend/graph/builder.py + routing.py
   (HTTP only: validate,               (wires nodes, conditional edges)
    call model/graph, map                        │
    ORM → Pydantic)                              ▼
        │                              backend/nodes/*.py
        │                               (one file = one graph node)
        ▼                                        │
  backend/models/*Model.py  ◄────────────────────┤
   (DAO: all SQL lives here)                     ▼
        │                              backend/services/{llm,vectorstore}.py
        ▼                                        │
  backend/models/db_schemes/…/schemes/*.py       ▼
   (SQLAlchemy ORM: structure only)      backend/LLM/  (factory → providers)

   SHARED, read by everyone:  backend/contracts/state.py
                              backend/schemas/
                              backend/config.py
```

**Never skip or invert a layer:**

| ❌ Forbidden | ✅ Required |
|---|---|
| Raw SQL / `select()` inside `api/routes_*.py` | Call a `*Model` method; add the method if it's missing |
| Query methods inside `schemes/*.py` ORM classes | ORM files declare columns, types, FKs, relationships — nothing else |
| `from fastapi import ...` inside `nodes/` or `services/` | Nodes are framework-free pure functions |
| Importing `GeminiProvider` / `openai` / `google.genai` inside a node | `from backend.services.llm import get_llm` |
| Business rules inside `models/*Model.py` | DAOs do CRUD + queries only |
| Hardcoded thresholds anywhere | `backend/config.py`, read as `getattr(config, "X", default)` |

---

## 3. LANGGRAPH PIPELINE RULES

**One file per node, in `backend/nodes/`.** This is the merge-conflict-avoidance
strategy for a multi-author team — respect it absolutely.

A node is:

```python
"""
Node: <name>
Responsibility: <one sentence>.

Owner: Track A | Track B | TOGETHER
"""
def node_name(state: PipelineState) -> dict:
    value = state.get("some_key", <default>)      # always .get() with a default
    ...
    return {"only_the_keys": ..., "this_node_writes": ...}   # a DELTA, never the full state
```

Rules:
- **Return only the delta.** Never return the whole state, never mutate `state` in place.
- **Always `state.get(key, default)`** — `PipelineState` is `total=False`; every key may be absent.
- **Never create a node file that does two things.** New responsibility ⇒ new file.
- Nodes may be `def` or `async def` (`rag_search` is async because it hits the DB).
  LangGraph handles both. If a node needs a DB session it opens its own via
  `AsyncSessionLocal()` and accepts an optional `db: AsyncSession | None = None`
  parameter for testability — copy `nodes/rag_search.py` exactly.
- **Wiring lives only in `graph/builder.py`; branch conditions only in `graph/routing.py`.**
  A routing function returns a plain string key that is mapped in `builder.py`. Never
  put an `if` that chooses the next node inside a node.
- Adding a node = (1) new file in `nodes/`, (2) `add_node` + edges in `builder.py`,
  (3) a routing function in `routing.py` if it's conditional, (4) a test in `tests/`.

Current graph — know it before changing it:

```
START → parse_input → validate_completeness →[missing_fields?]→ END
                                             └→ rag_search →[is_exact_match?]→ fast_track → END
                                                            └→ llm_analyze → deterministic_score
                                                                              ├ GO/NO_GO      → generate_report → END
                                                                              └ NEEDS_CLARIF  → generate_questions → END (pause)
```

`generate_questions → END` is an intentional pause. The clarification API re-invokes
the graph later with `clarification_round + 1` and the user's answers. Do not
"fix" this into a loop edge.

---

## 4. LLM FRAMEWORK RULES (`backend/LLM/`)

The team deliberately replaced direct SDK usage with a provider-agnostic framework.
Do not regress it.

```
LLMInterface (ABC)                  ← the contract: generate_text,
   ├── BaseLLMProvider                 generate_structured_output, health_check
   │      ├── GeminiProvider        ← multi-key round-robin (KEY_1 → KEY_2)
   │      ├── OpenAIProvider
   │      └── LocalLLMProvider      ← Ollama
   └── FallbackLLMProvider          ← decorator: primary → fallback on error
LLMProviderFactory                  ← chooses the stack from config
backend/services/llm.py             ← THE ONLY facade nodes are allowed to import
```

- Nodes call `get_llm()`, `get_structured_llm()` or `get_clarification_llm()` from
  `backend/services/llm.py`. Nothing else.
- Structured output is **always** `generate_structured_output(prompt=..., response_schema=<PydanticModel>)`.
  Never parse JSON out of free text by hand.
- A new provider = a new file in `backend/LLM/providers/`, implementing `LLMInterface`,
  registered in `LLMEnums.LLMProviderEnum` and in `LLMProviderFactory`. Never add
  `if provider == "x"` branches outside the factory.
- **Prompts use `string.Template`, not f-strings and not `.format()`.** This is
  deliberate: prompts contain JSON with `{}` braces that break `.format()`. Use
  `Template(...).safe_substitute(...)`. Prompt text lives in
  `backend/LLM/templates/`; `backend/prompts/` is a backwards-compatibility
  re-export shim — read it, don't grow it.
- Temperature comes from config (`LLM_TEMPERATURE=0` for extraction,
  `LLM_TEMPERATURE_CLARIFICATION=0.3` for questions). Never hardcode.

---

## 5. DATABASE RULES (PostgreSQL + SQLAlchemy 2.0 async + Alembic)

**DAO pattern ("mini-rag" style), session injected per request:**

```python
# route
async def endpoint(..., db: AsyncSession = Depends(get_db)):
    model = SubmissionModel(db)
    entity = await model.get_by_id_with_relations(request_id)
```

```python
# models/XModel.py
class XModel(BaseDataModel):
    def __init__(self, db_client: AsyncSession):
        super().__init__(db_client)
    async def get_by_id(self, x_id: str | uuid.UUID) -> X | None:
        uid = to_uuid(x_id)                      # ALWAYS — never pass raw strings to UUID columns
        if not uid: return None
        result = await self.db_client.execute(select(X).where(X.id == uid))
        return result.scalar_one_or_none()
```

Hard rules:
- Every DB call is `async`/`await`. No sync SQLAlchemy anywhere.
- Always `to_uuid()` before filtering on a UUID column (there is a fixed bug behind this).
- Loading relations for a response ⇒ use the `*_with_relations` variants with
  `selectinload(...)`. Never lazy-load in an async context.
- 7 core tables + `historic_projects`. Relationships:
  `departments 1─N submissions`; `submissions 1─1 fact_extractions | scoring_results | reports`;
  `submissions 1─N clarification_rounds | reviewer_overrides`.
- **Schema changes require an Alembic migration** in
  `backend/models/db_schemes/requirementshub/alembic/versions/`, filename pattern
  `YYYYMMDD_HHMM_<rev>_<description>.py`. Generate it, review it, never hand-edit the DB.
- `Base.metadata.create_all` is allowed **only** in `backend/cli/seed.py` and in tests.
  Never in the request path, never in `main.py`.
- New JSON columns must stay SQLite-compatible for the test suite:
  `JSON_TYPE = JSONB().with_variant(JSON, "sqlite")`.
- ORM entities never leak to the API. Convert them to Pydantic response models with an
  explicit mapper function (`entity_to_submission_response` in `routes_submissions.py`
  is the reference pattern).

---

## 6. API RULES (`backend/api/`)

- One file per domain: `routes_submissions.py`, `routes_clarification.py`,
  `routes_departments.py`, `routes_reports.py`, `routes_dashboard.py`, `routes_health.py`.
  New domain ⇒ new file **and** register it in `backend/api/router.py`.
- Each file declares `router = APIRouter(prefix="/<domain>", tags=["<Domain>"])`.
  The global `/api` prefix is added once, in `router.py`. Never re-declare it.
- Every route declares `response_model=<PydanticSchema>`, an explicit `status_code`
  when it isn't 200, and a `summary=`. Every function has a one-line docstring.
- Errors are `HTTPException` with `status.HTTP_*` constants — never bare `raise`,
  never returning `{"error": ...}` dicts.
- **Long work never blocks the response.** Submissions return `PENDING` immediately and
  run the graph via `BackgroundTasks` (`_execute_pipeline_in_background`). Background
  tasks open their **own** session with `async with AsyncSessionLocal() as db:` —
  they must not reuse the request session. Wrap them in try/except and set status
  `FAILED` on error.
- Pydantic schemas live in `backend/schemas/Schemas.py` and are exported through
  `backend/schemas/__init__.py`. Import from `backend.schemas`, never from the
  submodule path.

---

## 7. CONFIGURATION & 12-FACTOR RULES

`backend/config.py` is the only place that reads the environment.

```python
NEW_SETTING = int(os.getenv("NEW_SETTING", "42"))     # env name, sane default, typed
```

- Add every new setting to **`.env.example` too**, in the right commented section.
- Never `os.getenv` outside `config.py` (the single tolerated exception is the CORS
  block in `main.py` — do not add more).
- Never commit secrets. `.env` is gitignored; `.env.example` holds names only.
- **Logging:** `logging.getLogger(__name__)` or a dotted `"backend.<pkg>.<mod>"` name.
  Never `print()`. Never configure handlers outside `backend/core/GCPJsonFormatter.py::setup_logging`.
  Use lazy `%s` formatting (`logger.info("x=%s", x)`), not f-strings.
  Logs go to stdout — text locally, JSON on GCP. That's Factor XI; don't add file handlers.
- **No state on local disk.** Cloud Run is stateless: that's why ChromaDB was replaced by
  pgvector. Do not reintroduce a local persistent store.
- **Seeding is an explicit admin command** (`python -m backend.cli.seed`), never an
  app-startup side effect (Factor V). Keep it idempotent.

---

## 8. FRONTEND RULES (`frontend/src/`)

```
src/
├── AppRouter.jsx          entry router: /portal/* , /admin/* , /legacy  (+ DevBanner switcher)
├── main.jsx               mounts AppRouter
├── api/client.js          ← THE ONLY place fetch() is called. Single source of truth.
├── shared/
│   ├── api/client.js      re-export of ../../api/client — never a second implementation
│   └── styles/variables.css   ALL design tokens (--portal-* and --admin-*)
├── portal/                Business persona — Stripe / Warm Scandinavian, light
│   ├── PortalApp.jsx
│   └── components/        SubmissionWizard, WizardStepCard, DepartmentPicker,
│                          StatusTimeline, ClarificationQA
├── admin/                 AI engineer persona — Linear / Obsidian dark + champagne gold
│   ├── AdminApp.jsx
│   └── components/        SubmissionTable, SubmissionRow, StatusFilterBar,
│                          ScoreBreakdownPanel, DecisionOverrideForm
├── components/            V1 implementations (still the real code behind legacy/)
└── legacy/                V1 app preserved; its components/ are ONE-LINE re-export shims
```

**Persona data segregation is a security rule, not a style rule.**
`/portal` must never render `score`, `score_breakdown`, `reviewer_notes`,
`reviewer_name`, `manual_override`, `report_type`, or raw enum values
(`NEEDS_CLARIFICATION`, `GO`, `NO_GO`). It shows a human timeline
(`EN ATTENTE → ÉVALUATION IA → DOSSIER VALIDÉ`). `/admin` shows all of it.

Other frontend rules:
- **Never call `fetch` in a component.** Add a named function to `src/api/client.js`
  and import it. All endpoints already exist there — check before adding.
- **Styling = CSS custom properties from `shared/styles/variables.css`, applied via
  inline `style={{}}` objects (and a few utility classes like `status-pill`).
  Tailwind is NOT installed in `frontend/package.json` — do not emit Tailwind class
  names.** (`.agents/skills/requirements-hub-ui/SKILL.md` shows Tailwind in its
  examples; treat those as visual references only, and follow its **tokens**.)
- New colour/spacing/font ⇒ add a token to `variables.css` first, then use `var(--…)`.
  Never hardcode a hex value in a component.
- Anti-AI-slop bans (from `.agents/AGENTS.md`): no default indigo→purple tech
  gradients, no monotone symmetric cards without typographic hierarchy, no generic
  alert boxes without contextual icons, no instant transitions — always
  `transition: all 0.2s ease-out` (or the 0.15s variants already in use).
- `/portal` = progressive disclosure. One wizard step visible at a time. Never dump the
  whole form.
- `/admin` = density. Table-first, inline actions, `py-2.5 px-4`-equivalent row padding,
  1px `var(--admin-border)` separators. No modal-heavy flows.
- **UI strings are French. Code, identifiers, comments and docstrings are English.**
- Moving a file ⇒ leave a one-line re-export shim at the old path
  (`export { default } from '../../components/X';`). Never break an existing import.
- Functional components + hooks only. No class components, no new state library
  (no Redux/Zustand/React Query) — local `useState`/`useEffect` is the established idiom.

---

## 9. TESTING RULES (`tests/`)

- `tests/test_<module>.py` = real pytest suites, mirroring the backend module name.
- `tests/scratch_*.py` = manual exploration scripts, **not** collected by pytest. If you
  write a throwaway script, name it `scratch_*.py`. Never let a scratch file become the test.
- Fixtures come from `tests/conftest.py`: in-memory `sqlite+aiosqlite`, `test_engine`,
  `db_session`, `async_client` (httpx `ASGITransport` + `get_db` dependency override),
  `seeded_department`, `sample_submission_payload`. **Reuse them; don't reinvent them.**
- `asyncio_mode = "auto"` — write `async def test_...` with no decorator.
- **Never let a test hit a real LLM, a real embedding API, or a real Postgres.** Mock at
  the `backend/services/llm.py` or provider boundary.
- Anything touching scoring thresholds, routing conditions, or a new node gets a test in
  the same change.

---

## 10. GIT & DELIVERY RULES

- **Conventional Commits**, mandatory:
  `type(scope): imperative subject`
  types used here: `feat`, `fix`, `refactor`, `test`, `build`, `docs`
  scopes used here: `llm`, `api`, `rag`, `pipeline`, `cli`, `config`, `docker`,
  `schemas`, `logging`, `core`, `frontend`, `validation`, `scoring`, `parser`, `gcp`
  Examples from this repo:
  `feat(rag): migrate vector store from local ChromaDB to pgvector for Cloud Run statelessness`
  `refactor(schemas): centralize all Pydantic models and Enums in backend/schemas`
- One logical change per commit. Don't bundle a refactor with a feature.
- Branches: `feature/<track-or-topic>` → `main`.
- **Never edit a file outside your track without saying so.** Track A owns
  `services/`, `LLM/`, `prompts/`, `nodes/{rag_search,fast_track,llm_analyze,generate_questions}.py`.
  Track B owns `nodes/{parse_input,validate_completeness,deterministic_score,generate_report}.py`,
  `data/department_configs.json`. `contracts/`, `config.py`, `graph/`, `api/`, `main.py`
  are TOGETHER files — flag every change to them.

---

## 11. DELETING / REMOVING THINGS

- **Do not delete files to "clean up."** Removal is a separate, explicitly-requested task.
- Superseded code is preserved as a re-export shim, not deleted
  (`backend/contracts/schemas.py`, `backend/prompts/*`, `frontend/src/legacy/components/*`
  are all deliberate shims). Follow that pattern.
- Before deleting anything, grep for every import of it and report what you found.
- Never delete or rewrite an Alembic migration that already exists. Add a new one.
- Never delete a `PipelineState` key, a Pydantic field, an enum member, or a DB column
  without an explicit instruction — other tracks and the frontend read them.

---

## 12. KNOWN GAPS — DO NOT "HELPFULLY" FIX THESE WITHOUT BEING ASKED

State them in your summary if you touch nearby code, but don't silently change them:

1. **No authentication / RBAC exists.** `/api/dashboard/*` and `/api/reports/*` are open.
   The agreed design is `backend/api/middleware/auth.py` with a JWT `require_role([...])`
   dependency injected per route, plus a `ProtectedRoute` wrapper on the frontend. Any new
   admin-side route must be written so that adding `dependencies=[Depends(require_role([...]))]`
   is a one-line change later.
2. **Threshold drift.** `config.SCORE_NOGO_THRESHOLD` defaults to `20`, while comments
   and docs say `40`. Effective behaviour today: `<20 = NO_GO`, `20–69 = NEEDS_CLARIFICATION`,
   `≥70 = GO`. Don't change the number; fix a comment only if asked.
3. **Score unit drift on the frontend.** The backend returns `score` as an integer
   `0–100`. `admin/components/SubmissionRow.jsx` multiplies it by 100. Flag it; fix only
   on request.
4. **`zsystem/onboarding_guide.md` belongs to a different project (RelayPack/Supabase).**
   It is not a source of truth for this repo. Ignore it.
5. **`docker-compose.yml` lives in `docker/`**, and `docker-compose.md` at the root is
   documentation, not a compose file.
6. No request-id / correlation-id in logs yet (see `zsystem/ImplementerApres.md`), and no
   custom HTTP access middleware. Planned, not done.

---

## 13. YOUR WORKING PROTOCOL, EVERY TIME

**Before writing code:**
1. Locate the layer your change belongs to (§2) and the file that already does the
   closest thing. Read it fully.
2. Check whether the thing already exists: `src/api/client.js` for an endpoint, a
   `*Model` method for a query, a `config.py` setting for a constant, a
   `tests/conftest.py` fixture for test setup.
3. Decide whether you must touch a SHARED file (`contracts/state.py`, `schemas/`,
   `config.py`, `graph/`, `api/router.py`, `main.py`). If yes, plan it as additive.

**While writing code:**
4. Copy the idiom of the neighbouring file: module docstring with path +
   responsibility (+ `Owner:` line for nodes), type hints everywhere, `logging` not
   `print`, `async` all the way down, English identifiers/docstrings, French UI text.
5. Keep files single-purpose. New responsibility ⇒ new file, not a longer file.

**After writing code:**
6. Add or update the test in `tests/`.
7. Update `.env.example` if you added a setting; add a migration if you touched the ORM.
8. Write a Conventional Commit message.
9. **Report explicitly**, in this order:
   - files added / modified / deleted,
   - **any SHARED contract file you touched** (with a ⚠️),
   - any new env var, any new migration,
   - any rule in this document you had to bend, and why,
   - anything you noticed but deliberately did not fix.

**Never do, without being asked:** add a dependency; swap a library; introduce
TypeScript, Tailwind, Redux, an ORM other than SQLAlchemy, or a vector DB other than
pgvector; reorganise directories; reformat files you didn't otherwise change;
delete anything; expose admin data to `/portal`; call an LLM to make a decision.

=== END PROMPT ===

---

## Quick reference for the team (not part of the prompt)

**The five things that most often get broken by an AI agent on this repo:**

1. Raw SQL creeping into `api/routes_*.py` instead of a `*Model` method.
2. An LLM call sneaking into the scoring path.
3. Tailwind classes emitted into components (Tailwind isn't installed).
4. `score`/`breakdown`/`reviewer_notes` leaking into `/portal`.
5. A node file that grows a second responsibility instead of a new file being created.

**Where the rules come from:**
`zsystem/mvp_architecture.md` (pipeline + structure), `zsystem/parallel_work_plan.md`
(one-file-per-node, track ownership, the "never edit a file you don't own" rule),
`zsystem/architecture_analysis.md` (dual-persona, monorepo, RBAC plan),
`zsystem/RequirementsHub Database Architecture.md` (DAO + audit-log patterns),
`.agents/AGENTS.md` + `.agents/skills/requirements-hub-ui/SKILL.md` (design tokens,
anti-slop bans), and the code itself.
