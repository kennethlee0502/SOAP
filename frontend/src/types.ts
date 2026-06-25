export type TranscriptKey = "pc" | "neph" | "derm" | "psych" | "uc";

export const TRANSCRIPT_KEYS: TranscriptKey[] = ["pc", "neph", "derm", "psych", "uc"];

export const TRANSCRIPT_LABELS: Record<TranscriptKey, string> = {
  pc: "Primary Care",
  neph: "Nephrology",
  derm: "Dermatology",
  psych: "Psychiatry",
  uc: "Urgent Care",
};

export interface SubjectiveSection {
  chief_complaint: string;
  hpi: string;
  patient_quotes: string[];
}

export interface SoapNote {
  subjective: SubjectiveSection;
  objective: string;
  assessment_and_plan: string;
}

export interface GenerateRequest {
  transcript_key: TranscriptKey;
}

export interface GenerateErrorResponse {
  error: string;
  failed_quotes: string[];
}
