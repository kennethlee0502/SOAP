import type {
  GenerateErrorResponse,
  GenerateRequest,
  SoapNote,
  TranscriptKey,
} from "./types";

async function parseErrorMessage(res: Response): Promise<string> {
  try {
    // fetch().json() returns unknown; shape matches backend GenerateErrorResponse
    const body = (await res.json()) as GenerateErrorResponse;
    return body.error || `Request failed with status ${res.status}`;
  } catch {
    return `Request failed with status ${res.status}`;
  }
}

export async function fetchTranscriptKeys(): Promise<TranscriptKey[]> {
  const res = await fetch("/api/transcripts");
  if (!res.ok) throw new Error(`Failed to fetch transcript keys: ${res.status}`);
  // fetch().json() returns unknown; shape is { keys: TranscriptKey[] } per backend contract
  const data = (await res.json()) as { keys: TranscriptKey[] };
  return data.keys;
}

export async function generateSoapNote(key: TranscriptKey): Promise<SoapNote> {
  const body: GenerateRequest = { transcript_key: key };

  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const message = await parseErrorMessage(res);
    throw new Error(message);
  }

  // fetch().json() returns unknown; shape is SoapNote per backend Pydantic schema
  return (await res.json()) as SoapNote;
}
