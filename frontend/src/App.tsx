import { useState } from "react";
import { generateSoapNote } from "./api";
import type { SoapNote, TranscriptKey } from "./types";
import { TRANSCRIPT_KEYS, TRANSCRIPT_LABELS } from "./types";

export default function App() {
  const [selectedKey, setSelectedKey] = useState<TranscriptKey>(
    TRANSCRIPT_KEYS[0],
  );
  const [soapNote, setSoapNote] = useState<SoapNote | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPrivacyMode, setIsPrivacyMode] = useState(true);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setSoapNote(null);
    try {
      const note = await generateSoapNote(selectedKey);
      setSoapNote(note);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unexpected error occurred.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header>
        <h1>SOAP Note Generator</h1>
        <p className="subtitle">
          AI-generated clinical documentation from patient encounter transcripts
        </p>
      </header>

      <div className="controls">
        <select
          value={selectedKey}
          onChange={(e) => {
            // Value is constrained to TranscriptKey by the option list below
            setSelectedKey(e.target.value as TranscriptKey);
            setSoapNote(null);
            setError(null);
          }}
          disabled={loading}
        >
          {TRANSCRIPT_KEYS.map((key) => (
            <option key={key} value={key}>
              {TRANSCRIPT_LABELS[key]}
            </option>
          ))}
        </select>
        <button onClick={handleGenerate} disabled={loading} type="button">
          {loading ? "Generating…" : "Generate SOAP Note"}
        </button>
        {soapNote && (
          <label className="privacy-toggle">
            <input
              type="checkbox"
              checked={isPrivacyMode}
              onChange={(e) => setIsPrivacyMode(e.target.checked)}
            />
            🔒 HIPAA Privacy Mask
          </label>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {soapNote && (
        <div
          className={`soap-note ${isPrivacyMode ? "privacy-mode-active" : ""}`}
        >
          <div className="card">
            <p className="card-label">Subjective</p>

            <div className="field">
              <p className="field-label">Chief Complaint</p>
              <p className="field-text">
                {soapNote.subjective.chief_complaint}
              </p>
            </div>

            <div className="field">
              <p className="field-label">History of Present Illness</p>
              <p className="field-text">{soapNote.subjective.hpi}</p>
            </div>

            <div className="field">
              <p className="field-label">
                Patient Quotes
                <span className="badge">verbatim</span>
              </p>
              <ul className="quotes">
                {soapNote.subjective.patient_quotes.map((quote, i) => (
                  <li key={i}>{quote}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="card">
            <p className="card-label">Objective</p>
            <p className="field-text">{soapNote.objective}</p>
          </div>

          <div className="card">
            <p className="card-label">Assessment and Plan</p>
            <p className="field-text">{soapNote.assessment_and_plan}</p>
          </div>
        </div>
      )}
    </div>
  );
}
