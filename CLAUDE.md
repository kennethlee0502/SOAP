# CLAUDE.md — SOAP Note Generator

Project memory and behavioral contract for AI-assisted development.
Read this file in full before touching any code in this repository.

---

## 1. Project Overview

**What this is:** A full-stack web application that ingests a raw patient-provider encounter transcript and generates a structured SOAP note using an LLM (OpenAI GPT-4o), with an automated evaluation harness to verify structural correctness and verbatim quote fidelity.

**HIPAA Compliance Posture (Non-negotiable):**
- **Stateless architecture.** No database. No persistent storage of any kind. Transcripts and generated notes exist only in memory for the duration of a single request.
- **Zero Data Retention on the LLM layer.** All OpenAI API calls must include `store=False`. This disables OpenAI's 30-day request log retention. This is not optional and must never be removed.
- **No PII linkage.** The `user` field must never be passed to the OpenAI API.
- **No request body logging.** Do not add any middleware, interceptor, or logger that captures or persists the transcript or SOAP note payloads.
- **API key hygiene.** The `OPENAI_API_KEY` is loaded exclusively from `.env` via `python-dotenv`. The `.env` file is always in `.gitignore`. It is never hardcoded, interpolated into strings for display, or returned in any API response.
- **De-identified dataset.** The 5 sample transcripts are de-identified, but the code architecture must treat all transcript data as if it contains PHI.

**Dataset:** 5 pre-seeded, de-identified encounter transcripts in `transcripts/`:
- `pc.txt` — Primary Care
- `neph.txt` — Nephrology
- `derm.txt` — Dermatology
- `psych.txt` — Psychiatry
- `uc.txt` — Urgent Care

---

## 2. Architecture Decisions & Data Flow

### Core Decisions (Do Not Revisit Without Explicit User Approval)

| Decision | Rationale |
|---|---|
| No database | HIPAA minimal retention; out of scope for 4hr timebox |
| Single-shot LLM generation | No multi-turn; stateless by design |
| No streaming | Adds frontend complexity for marginal UX gain |
| No auth layer | Out of scope; noted as production gap |
| Pre-seeded transcripts only | No file upload endpoint — eliminates attack surface |
| Assessment + Plan combined | Schema enforces this — single `assessment_and_plan` field, no separate keys |

### Request Lifecycle

```
Browser
  └─ POST /generate  { transcript_key: "pc" }
       │
       ▼
  FastAPI (main.py)
       │  validates input via Pydantic
       │  reads transcript from disk (transcripts/{key}.txt)
       ▼
  llm.py
       │  builds prompt (prompts.py)
       │  calls OpenAI with response_format + strict=True + store=False
       │  receives JSON → parses into SoapNote Pydantic model
       │  runtime verbatim quote guard (raises if any quote fails substring match)
       ▼
  FastAPI returns SoapNote JSON
       │
       ▼
  React (App.tsx)
       └─ renders CC / HPI / Patient Quotes / Objective / Assessment and Plan
```

**The transcript is read from disk on each request and never stored beyond the function scope.**

---

## 3. Tech Stack Specification

### Backend

| Component | Library | Version Constraint |
|---|---|---|
| Framework | FastAPI | >=0.111 |
| ASGI server | uvicorn | >=0.29 |
| Schema validation | Pydantic | v2 (not v1) |
| LLM client | openai | >=1.30 |
| Env management | python-dotenv | >=1.0 |
| Test runner | pytest | >=7 |
| Python version | CPython | 3.11+ |

### Frontend

| Component | Library | Version Constraint |
|---|---|---|
| Build tool | Vite | 5+ |
| UI framework | React | 18+ |
| Language | TypeScript | 5+ |
| HTTP client | Native `fetch` | — |
| Styling | Plain CSS only | — |

**Explicitly banned:**
- No Axios (native fetch is sufficient)
- No Redux, Zustand, or any state management library (useState is sufficient)
- No UI component libraries (MUI, Chakra, shadcn, Ant Design, etc.)
- No ORMs, no database drivers, no caching layers
- No Docker (adds setup time within the 4hr timebox)

---

## 4. Coding Standards

### Python / FastAPI

- All route handler functions must be `async def`.
- All function parameters and return types must be explicitly annotated.
- Never use `dict` as a return type where a Pydantic model exists. Return Pydantic model instances.
- FastAPI dependency injection is acceptable for config/settings; do not use it to pass mutable state.
- Exceptions: raise `HTTPException` with appropriate status codes. Do not swallow exceptions silently.
- The `llm.py` module is the only place that may import `openai`. No other module touches the OpenAI client.

### Pydantic v2 Conventions

- Use `model_config = ConfigDict(...)` — not the inner `class Config:` pattern (that is v1).
- Use `Field(...)` with `description=` on every field. These descriptions are passed to OpenAI as the JSON schema and directly influence LLM output quality.
- All string fields that represent extracted text must use `str`, not `Optional[str]`, unless absence is a valid business state.
- The `SoapNote` Pydantic model is the single source of truth for the SOAP structure. The TypeScript `types.ts` must mirror it exactly. When the Pydantic model changes, update `types.ts` immediately.

### TypeScript / React

- `strict: true` in `tsconfig.json`. No `any`. No type assertions (`as SomeType`) without a comment explaining why.
- All API response types must be defined in `src/types.ts` and imported — never inlined.
- Components: functional only, no class components.
- No `useEffect` for data fetching; use event handlers triggered by user action (the "Generate" button click).
- Keep `App.tsx` as the single stateful component. Extract sub-components only if a section exceeds ~60 lines.

### General

- No commented-out code in commits.
- No `TODO` comments — either implement it now or log it as a known gap in the README.
- No `console.log` in production paths. Use it only during active debugging and remove before committing.

---

## 5. Folder Structure Conventions

This structure is fixed. Do not add top-level directories without explicit discussion.

```
SOAP/                          ← repo root
├── CLAUDE.md                  ← this file
├── .gitignore
├── README.md
│
├── backend/
│   ├── main.py                ← FastAPI app; single route POST /generate
│   ├── models.py              ← All Pydantic schemas (SoapNote and sub-models)
│   ├── llm.py                 ← OpenAI client, prompt assembly, verbatim guard
│   ├── prompts.py             ← System prompt + user prompt template strings only
│   ├── requirements.txt
│   └── .env                   ← Never committed; OPENAI_API_KEY only
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx            ← Main component; transcript selector + SOAP renderer
│   │   ├── api.ts             ← Typed fetch wrapper for POST /generate
│   │   ├── types.ts           ← TypeScript mirror of backend Pydantic models
│   │   └── main.tsx           ← Vite entry point
│   ├── index.html
│   ├── vite.config.ts         ← Proxy /api → localhost:8000
│   ├── tsconfig.json
│   └── package.json
│
├── transcripts/
│   ├── pc.txt
│   ├── neph.txt
│   ├── derm.txt
│   ├── psych.txt
│   └── uc.txt
│
└── eval/
    └── eval.py                ← Standalone eval harness; no FastAPI dependency
```

**File placement rules:**
- All prompt text lives in `prompts.py`. Never inline prompt strings in `llm.py` or `main.py`.
- All Pydantic models live in `models.py`. Never define schemas inline in route handlers.
- `eval.py` has zero imports from `backend/`. It is a self-contained script that calls the running API over HTTP or imports models directly for schema inspection.

---

## 6. Development Workflow Rules & Limits

### Within the 4-Hour Timebox

Build in this strict order. Do not advance to the next phase until the current one is verified working:

1. **Schema first** (`models.py`) — everything derives from this
2. **Backend endpoint** (`llm.py` → `main.py`) — verified via `curl`
3. **Eval harness** (`eval.py`) — run against all 5 transcripts before touching the frontend
4. **Frontend** (`App.tsx`, `api.ts`) — connect to verified backend
5. **Integration pass** — run eval harness again end-to-end, fix failures
6. **README + cleanup** — last

### Hard Limits

- Do not spend time on: CSS animations, responsive design, dark mode, loading skeletons, toast notifications, or any visual polish beyond basic readable layout.
- Do not configure: CORS headers manually (Vite proxy handles this), environment-specific configs, or deployment pipelines.
- Do not install any package that is not listed in Section 3. If a package seems useful, flag it and ask before installing.
- If a feature would take more than 20 minutes to implement cleanly, cut scope and note it in the README under "Known Gaps."

### Git Hygiene

- `.env` is in `.gitignore` from commit zero.
- Commit after each phase is verified: schema, backend, eval, frontend.
- Commit messages follow the pattern: `phase(N): brief description` (e.g., `phase(2): pydantic soap schema and llm wrapper`).

---

## 7. Testing & Evaluation Strategy

### Eval Harness (`eval/eval.py`)

The eval harness is a **deterministic, standalone Python script**. It does not use mocking. It calls the live running backend (or parses response JSON directly) and applies rule-based checks.

**Checks performed for each of the 5 transcripts:**

| Check | Method | Pass Condition |
|---|---|---|
| Required sections present | Key existence on parsed JSON | `subjective`, `objective`, `assessment_and_plan` all present |
| Subjective sub-sections present | Key existence | `chief_complaint`, `hpi`, `patient_quotes` all present |
| Assessment and Plan combined | Negative key check | Keys `assessment` and `plan` do NOT exist as top-level keys |
| Patient quotes count | `len()` check | `3 <= len(patient_quotes) <= 5` |
| Patient quotes verbatim | Substring match | `all(quote in source_transcript for quote in patient_quotes)` |

**Verbatim match is a hard failure.** A quote that is even one character off (punctuation, capitalization, added word) must cause the test to fail with a clear diff showing the expected vs. actual string.

**Running the harness:**
```bash
# Backend must be running on localhost:8000
cd eval
python eval.py
# or
pytest eval.py -v
```

**Output format:** Per-transcript pass/fail table printed to stdout. Exit code 0 only if all 5 transcripts pass all checks. Non-zero exit code on any failure (suitable for CI integration).

### Runtime Guard in `llm.py`

Before returning from the generation function, `llm.py` must verify verbatim quotes programmatically:

```
for each quote in soap_note.subjective.patient_quotes:
    assert quote in source_transcript  # raises on failure
```

If any quote fails, the function raises a descriptive exception (not a generic 500). The FastAPI handler catches this and returns a structured error response — it does not silently return a partially-valid note.

---

## 8. AI Assistant Behavior Rules

These rules govern how Claude (this assistant) must behave when working in this codebase. They are not suggestions.

### Package & Dependency Rules
- **Do not install any package not listed in Section 3.** If a new package seems necessary, stop and explain why to the user before touching `requirements.txt` or `package.json`.
- **Do not upgrade existing packages** without explicit instruction.
- **Do not add dev tooling** (linters, formatters, pre-commit hooks) unless the user asks. They consume timebox budget.

### Schema & Type Rules
- **Always use strict Pydantic v2 models.** Never use `dict`, `Any`, or untyped return values where a model exists.
- **Never split Assessment and Plan.** The field is always `assessment_and_plan: str`. If you find yourself writing `assessment:` and `plan:` as separate fields, stop — this violates the core requirement.
- **Mirror TypeScript types immediately.** Any change to `models.py` must be followed by the corresponding update to `src/types.ts` in the same response.

### LLM Integration Rules
- **`store=False` is mandatory on every OpenAI API call.** Never omit it. Never suggest removing it for debugging. If you need to inspect LLM behavior, log the response JSON locally to a scratchpad file — not via OpenAI's platform.
- **Never pass the `user` field** to the OpenAI API in this codebase.
- **Prompt strings live in `prompts.py` only.** Do not inline prompt text in `llm.py` or anywhere else.
- **`strict=True` in `response_format`.** Always use strict JSON schema mode for structured output calls.

### Verbatim Quote Guard Rules
- **The runtime verbatim guard in `llm.py` must always be present.** Do not remove it for performance, simplicity, or any other reason.
- **Do not use fuzzy/semantic matching** for the verbatim check. The check is `quote in source_transcript` — exact substring, case-sensitive. That is the contract.
- **If the guard fails, raise an exception with a descriptive message** identifying which quote failed and what the source transcript substring context looks like. Do not silently return the note with failing quotes.

### Scope & Complexity Rules
- **Do not add features not in the requirements.** No export-to-PDF, no history panel, no copy-to-clipboard button, no multi-language support, no dark mode.
- **Do not refactor working code** during the 4-hour timebox unless it is directly blocking a requirement. Note refactoring opportunities in comments for post-timebox work.
- **Do not add error boundaries, retry logic, or fallback UI** beyond what is explicitly specified. A simple error message string in the UI is sufficient.
- **Prefer the simplest implementation that satisfies the requirement.** Three lines of explicit code beats one line of clever abstraction every time in a timebox.

### Communication Rules
- When asked to implement a phase, write all files for that phase completely before asking for feedback.
- When a design decision has a trade-off, state the trade-off in one sentence and make the pragmatic call — do not present a menu of options.
- If a requirement is ambiguous, resolve it using the constraints already established (HIPAA posture, timebox, simplicity) and state the resolution explicitly.
