# SOAP

## 1. A high-level overview of your app

This project takes de-identified doctor-patient conversation transcripts and converts them into structured SOAP notes.

The application uses a language model to analyze the transcript and generate a clinical note containing the following sections:

Chief Complaint
History of Present Illness
Patient Quotes
Objective
Assessment and Plan

The goal is to turn unstructured conversations into a format that is easier to review and aligns with common clinical documentation practices.

## 2. How to run the app

## 2.1 Backend Setup (FastAPI)

### Move to backend root

```
cd backend
```

### Re-create a clean virtual environment and activate it

```
python3 -m venv .venv
source .venv/bin/activate
```

### Install core production dependencies (FastAPI, Uydantic, OpenAI SDK, etc.)

```
pip install -r requirements.txt
```

### Create your private environment context file

```
echo "OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY" > .env
```

### Fire up the live hot-reloading development server

```
uvicorn main:app --reload
```

## 2.2 frontend root

```
cd frontend
```

#### Install package dependencies cleanly

```
npm install
```

#### Boot up the Vite local dev server with proxy settings configured

```
npm run dev
```

## 3. How to run the eval harness

```
python3 eval/eval.py
```

## 4.How you initially approached the problem

My first step was to carefully understand the requirements and identify everything that needed to be built, especially since clarifying questions were not allowed. I reviewed the input transcript format, the expected SOAP note structure, and the evaluation requirements before making any implementation decisions.

Once I had a clear understanding of the problem, I used Claude as a planning partner. Rather than asking it to generate code immediately, I first discussed my proposed architecture and implementation approach. We discussed on the design until I was satisfied that it met the requirements.

After defining the approach, I asked Claude to create a detailed CLAUDE.md file to document the project's architecture, coding standards, requirements, and implementation plan. This served as a reference throughout development to help keep the project consistent and prevent the implementation from drifting away from the original design.

To keep the work organized, I divided the project into seven tasks:

1. backend/models.py — Pydantic v2 schema definitions
2. backend/prompts.py — system and user prompt templates
3. backend/llm.py — OpenAI integration and verbatim quote validation
4. backend/main.py — FastAPI endpoints
5. eval/eval.py — standalone evaluation harness
6. frontend/src/types.ts and api.ts
7. frontend/src/App.tsx and index.css

After completing each task, I reviewed the implementation against the documented requirements in CLAUDE.md to ensure the project remained aligned with the original design and requirements.

## 5. Bugs/blockers/tradeoffs you encountered and how you handled them

My local environment was running Python 3.9, but part of the FastAPI code used the newer union type syntax (SoapNote | JSONResponse). When I started Uvicorn, the application immediately crashed with a TypeError: unsupported operand type(s) for |.

My first instinct wasn't to upgrade Python right away. Instead, I wanted to understand why the error was happening and see if there was a simpler fix. After looking into it, I added from **future** import annotations to main.py, which allowed the code to work correctly in Python 3.9 without requiring any environment changes.

## 6. What you'd do differently if you could start over

Because of the time limit of the exercise, I didn't fully incorporate all of the HIPAA-related considerations that I would normally want to include in a production system.

If I were starting over or had more time, I would add stronger HIPAA-focused features, such as securely storing both the transcripts and the SOAP notes in an encrypted database. This would provide a reliable audit trail, make it easier to review and improve prompt performance over time, and support future compliance and auditing needs.
