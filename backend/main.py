from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from llm import generate_soap_note
from models import GenerateErrorResponse, GenerateRequest, SoapNote

TRANSCRIPTS_DIR = Path(__file__).resolve().parent.parent / "transcripts"

TRANSCRIPT_KEYS: list[str] = ["pc", "neph", "derm", "psych", "uc"]

app = FastAPI(title="SOAP Note Generator")


@app.get("/transcripts")
async def list_transcripts() -> dict[str, list[str]]:
    return {"keys": TRANSCRIPT_KEYS}


@app.post("/generate", response_model=SoapNote)
async def generate(request: GenerateRequest) -> SoapNote | JSONResponse:
    transcript_path = TRANSCRIPTS_DIR / f"{request.transcript_key}.txt"

    try:
        transcript = transcript_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Transcript '{request.transcript_key}' not found on disk.")

    try:
        return await generate_soap_note(request.transcript_key, transcript)
    except ValueError as exc:
        return JSONResponse(
            status_code=422,
            content=GenerateErrorResponse(error=str(exc)).model_dump(),
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content=GenerateErrorResponse(error=f"Unexpected error during generation: {type(exc).__name__}: {exc}").model_dump(),
        )
