from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SubjectiveSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chief_complaint: str = Field(
        description=(
            "A single concise sentence capturing the patient's primary reason for today's visit. "
            "Use the patient's own words where possible. "
            "Example: 'Patient presents with a 3-day history of worsening lower back pain.'"
        )
    )

    hpi: str = Field(
        description=(
            "A structured clinical narrative paragraph describing the History of Present Illness. "
            "Cover onset, location, duration, character, aggravating and relieving factors, "
            "radiation, timing, and severity (OLDCARTS framework where applicable). "
            "Write in clinical third-person prose. Do not use bullet points."
        )
    )

    patient_quotes: list[str] = Field(
        description=(
            "A list of exactly 3 to 5 statements spoken directly by the patient, "
            "copied VERBATIM — word-for-word, character-for-character — from the transcript. "
            "Do NOT paraphrase, summarize, correct grammar, fix spelling, or alter punctuation in any way. "
            "Each string in this list MUST be an exact substring of the source transcript. "
            "If you change even one word, the output is invalid."
        ),
        min_length=3,
        max_length=5,
    )


class SoapNote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subjective: SubjectiveSection = Field(
        description=(
            "The Subjective section of the SOAP note, containing the chief complaint, "
            "history of present illness, and verbatim patient quotes."
        )
    )

    objective: str = Field(
        description=(
            "The Objective section. Record all measurable, observable clinical findings from the transcript: "
            "vital signs (BP, HR, RR, Temp, SpO2, weight), physical examination findings, "
            "and any laboratory or imaging results mentioned. "
            "Use clinical shorthand where appropriate (e.g., 'BP 138/86 mmHg, HR 78 bpm'). "
            "If no objective data is present in the transcript, write 'Not documented in transcript.'"
        )
    )

    assessment_and_plan: str = Field(
        description=(
            "A single unified section combining both the clinical Assessment and the Plan. "
            "Do NOT separate these into two distinct sections. "
            "Begin with the provider's diagnostic impression or working diagnoses (Assessment), "
            "then immediately follow with the management plan (Plan): medications, referrals, "
            "follow-up instructions, patient education, and next steps. "
            "Use numbered or structured prose as appropriate to the encounter complexity."
        )
    )


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript_key: Literal["pc", "neph", "derm", "psych", "uc"] = Field(
        description=(
            "The identifier for one of the five pre-seeded de-identified encounter transcripts. "
            "'pc' = Primary Care, 'neph' = Nephrology, 'derm' = Dermatology, "
            "'psych' = Psychiatry, 'uc' = Urgent Care."
        )
    )


class GenerateErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: str = Field(description="Human-readable description of what failed.")
    failed_quotes: list[str] = Field(
        default_factory=list,
        description="Quotes that failed the verbatim substring check, if applicable.",
    )
