"""
SOAP Note Generator — Standalone Eval Harness

Calls the running FastAPI backend (localhost:8000) for each of the 5 pre-seeded
transcripts and runs 5 deterministic checks per transcript (25 assertions total).

Usage:
    # Backend must be running first:
    #   cd backend && uvicorn main:app --reload
    #
    python eval/eval.py              # prints scorecard table, exits 0 on full pass
    pytest eval/eval.py -v           # same logic surfaced as 5 pytest tests
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

BASE_URL = "http://localhost:8000"
TRANSCRIPTS_DIR = Path(__file__).resolve().parent.parent / "transcripts"
TRANSCRIPT_KEYS = ["pc", "neph", "derm", "psych", "uc"]

CHECK_LABELS = [
    "sections   ",  # padded for table alignment
    "sub_keys   ",
    "ap_merge   ",
    "qty (3–5)  ",
    "verbatim   ",
]


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    passed: bool
    detail: str = ""


@dataclass
class TranscriptResult:
    key: str
    checks: list[CheckResult] = field(default_factory=list)
    api_error: str = ""

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def all_passed(self) -> bool:
        return not self.api_error and self.pass_count == self.total


# ── HTTP helpers ─────────────────────────────────────────────────────────────

def post_generate(key: str) -> tuple[int, dict]:
    """POST /generate. Returns (status_code, parsed_body)."""
    url = f"{BASE_URL}/generate"
    payload = json.dumps({"transcript_key": key}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read()) if exc.fp else {}
        return exc.code, body
    except urllib.error.URLError as exc:
        raise ConnectionError(
            f"Cannot reach backend at {BASE_URL}. "
            f"Start it with: cd backend && uvicorn main:app --reload\n"
            f"Underlying error: {exc.reason}"
        ) from exc


# ── The 5 deterministic checks ───────────────────────────────────────────────

def check_required_sections(note: dict) -> CheckResult:
    for key in ("subjective", "objective", "assessment_and_plan"):
        if key not in note:
            return CheckResult(False, f"Missing top-level key: '{key}'")
    return CheckResult(True)


def check_subjective_sub_keys(note: dict) -> CheckResult:
    subj = note.get("subjective", {})
    for key in ("chief_complaint", "hpi", "patient_quotes"):
        if key not in subj:
            return CheckResult(False, f"Missing subjective key: '{key}'")
    return CheckResult(True)


def check_ap_not_split(note: dict) -> CheckResult:
    for bad_key in ("assessment", "plan"):
        if bad_key in note:
            return CheckResult(
                False,
                f"Key '{bad_key}' exists as a top-level field — "
                "Assessment and Plan must be combined into 'assessment_and_plan'.",
            )
    return CheckResult(True)


def check_quote_count(note: dict) -> CheckResult:
    quotes = note.get("subjective", {}).get("patient_quotes", [])
    n = len(quotes)
    if 3 <= n <= 5:
        return CheckResult(True, f"{n} quotes")
    return CheckResult(False, f"Expected 3–5 patient quotes, got {n}.")


def check_quotes_verbatim(note: dict, transcript: str) -> CheckResult:
    quotes = note.get("subjective", {}).get("patient_quotes", [])
    failing: list[str] = [q for q in quotes if q not in transcript]
    if not failing:
        return CheckResult(True)
    lines = [f"{len(failing)} quote(s) failed exact substring match:"]
    for q in failing:
        lines.append(f"  FAIL: {repr(q)}")
        first_word = q.split()[0] if q.split() else ""
        idx = transcript.find(first_word)
        if idx != -1:
            window = transcript[max(0, idx - 10) : idx + len(q) + 30]
            lines.append(f"  NEAR: {repr(window)}")
    return CheckResult(False, "\n".join(lines))


# ── Core runner ──────────────────────────────────────────────────────────────

def run_eval(key: str) -> TranscriptResult:
    """Run all 5 checks for one transcript key. Returns a TranscriptResult."""
    result = TranscriptResult(key=key)
    transcript = (TRANSCRIPTS_DIR / f"{key}.txt").read_text(encoding="utf-8")

    status, body = post_generate(key)

    if status != 200:
        error_msg = body.get("error") or body.get("detail") or f"HTTP {status}"
        result.api_error = f"API returned {status}: {error_msg}"
        result.checks = [CheckResult(False, result.api_error)] * 5
        return result

    result.checks = [
        check_required_sections(body),
        check_subjective_sub_keys(body),
        check_ap_not_split(body),
        check_quote_count(body),
        check_quotes_verbatim(body, transcript),
    ]
    return result


# ── Scorecard printer ────────────────────────────────────────────────────────

def print_scorecard(results: list[TranscriptResult]) -> int:
    """Print a formatted scorecard. Returns exit code (0 = all pass)."""
    col_w = 10
    key_w = 10
    header_labels = [lbl.strip() for lbl in CHECK_LABELS]

    sep = "─" * (key_w + (col_w + 3) * 5 + col_w + 4)

    print()
    print("  SOAP Note Generator — Eval Harness Results")
    print(f"  {sep}")

    header = f"  {'key':<{key_w}}"
    for lbl in header_labels:
        header += f"  {lbl:^{col_w}}"
    header += f"  {'result':^8}"
    print(header)
    print(f"  {sep}")

    all_passed = True
    col_totals = [0] * 5

    for res in results:
        row = f"  {res.key:<{key_w}}"
        for i, chk in enumerate(res.checks):
            cell = "PASS" if chk.passed else "FAIL"
            row += f"  {cell:^{col_w}}"
            if chk.passed:
                col_totals[i] += 1
        score = f"{res.pass_count}/{res.total}"
        mark = "✓" if res.all_passed else "✗"
        row += f"  {score:^6} {mark}"
        print(row)
        if not res.all_passed:
            all_passed = False

    print(f"  {sep}")
    totals_row = f"  {'TOTAL':<{key_w}}"
    grand = sum(col_totals)
    for t in col_totals:
        totals_row += f"  {t}/5:^{col_w}".replace(f"{t}/5:^{col_w}", f"{t}/5".center(col_w))
    totals_row += f"  {grand}/25 "
    print(totals_row)
    print(f"  {sep}")
    print()

    if not all_passed:
        print("  FAILURES:")
        for res in results:
            for label, chk in zip(CHECK_LABELS, res.checks):
                if not chk.passed:
                    print(f"  [{res.key}] {label.strip()}: {chk.detail}")
        print()

    verdict = "ALL 25 CHECKS PASSED" if all_passed else "ONE OR MORE CHECKS FAILED"
    exit_code = 0 if all_passed else 1
    print(f"  {verdict} — exit code {exit_code}")
    print()
    return exit_code


# ── Entrypoint ───────────────────────────────────────────────────────────────

def main() -> None:
    try:
        results = [run_eval(key) for key in TRANSCRIPT_KEYS]
    except ConnectionError as exc:
        print(f"\n  ERROR: {exc}\n", file=sys.stderr)
        sys.exit(1)

    exit_code = print_scorecard(results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()


# ── Pytest-compatible test functions ─────────────────────────────────────────
# Run with: pytest eval/eval.py -v
# Each function maps to one transcript (5 tests total, all 5 checks per test).

import pytest  # noqa: E402 — intentional late import; pytest not needed for standalone run


@pytest.mark.parametrize("transcript_key", TRANSCRIPT_KEYS)
def test_transcript(transcript_key: str) -> None:
    result = run_eval(transcript_key)
    failures = [
        f"[{label.strip()}] {chk.detail}"
        for label, chk in zip(CHECK_LABELS, result.checks)
        if not chk.passed
    ]
    if result.api_error:
        pytest.fail(f"API error for '{transcript_key}': {result.api_error}")
    if failures:
        pytest.fail(
            f"Transcript '{transcript_key}' failed {len(failures)}/5 checks:\n"
            + "\n".join(failures)
        )
