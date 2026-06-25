import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import AsyncOpenAI

from models import SoapNote
from prompts import SYSTEM_PROMPT, build_retry_prompt, build_user_prompt

load_dotenv()

MODEL = "gpt-4o"


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
    return AsyncOpenAI(api_key=api_key)


def _run_verbatim_guard(soap_note: SoapNote, transcript: str) -> list[str]:
    """Return list of quotes that are not exact substrings of the transcript."""
    return [
        quote
        for quote in soap_note.subjective.patient_quotes
        if quote not in transcript
    ]


def _format_verbatim_error(failing_quotes: list[str], transcript: str) -> str:
    lines = ["Verbatim guard failed. The following quotes are not substrings of the source transcript:\n"]
    for i, quote in enumerate(failing_quotes, 1):
        lines.append(f"  [{i}] Quote   : {repr(quote)}")
        # Find the closest window in the transcript for debugging context.
        first_word = quote.split()[0] if quote.split() else ""
        idx = transcript.find(first_word)
        if idx != -1:
            window = transcript[max(0, idx - 20) : idx + len(quote) + 40]
            lines.append(f"       Nearest : {repr(window)}")
        lines.append("")
    return "\n".join(lines)


async def _call_llm(messages: list[dict]) -> SoapNote:
    client = _get_client()
    response = await client.beta.chat.completions.parse(
        model=MODEL,
        messages=messages,  # type: ignore[arg-type]
        response_format=SoapNote,
        store=False,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise ValueError(
            "OpenAI returned a null parsed response. "
            "The model may have refused or returned malformed JSON."
        )
    return parsed


async def generate_soap_note(transcript_key: str, transcript: str) -> SoapNote:
    """
    Generate a SoapNote from a raw transcript string.

    Runs a verbatim guard after generation. If any patient quote is not an exact
    substring of the transcript, retries once with a reinforced prompt.
    Raises ValueError if the guard still fails after the retry.
    """
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(transcript)},
    ]

    soap_note = await _call_llm(messages)

    failing = _run_verbatim_guard(soap_note, transcript)

    if failing:
        # Single reinforced retry.
        retry_messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_retry_prompt(transcript, failing)},
        ]
        soap_note = await _call_llm(retry_messages)
        failing = _run_verbatim_guard(soap_note, transcript)

        if failing:
            raise ValueError(_format_verbatim_error(failing, transcript))

    return soap_note
