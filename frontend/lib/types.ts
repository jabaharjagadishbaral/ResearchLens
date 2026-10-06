// Mirrors the backend response shapes (app/services/research_service.py).
export interface Citation {
  id: number; chunk_id: string; document_id: string; document_title: string; authors: string[];
  page: number; section: string; quote: string; relevance: number;
}
export type VerificationStatus =
  | "SUPPORTED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED" | "CONTRADICTED" | "INSUFFICIENT_EVIDENCE";
export interface ClaimVerification {
  claim: string; status: VerificationStatus; score: number; chunk_id: string | null;
  document_title: string | null; page: number | null; evidence_sentence: string | null; cited: boolean;
}
export interface QueryResult {
  question: string; status: "answered" | "insufficient_evidence"; answer: string; citations: Citation[];
  invalid_citations: number[]; uncited_sentences: string[]; injection_flagged: string[]; confidence: number;
  verification: ClaimVerification[]; verification_summary: Record<string, number | null>;
  comparison_markdown: string; report: string; trace: string[]; errors: string[]; mock_mode: boolean;
}
export interface DocumentMeta {
  id: string; title: string; filename: string; pages: number; chunks: number; ocr_pages: number[]; status: string;
}
export interface Fact { value: string; page: number; chunk_id: string }
export interface PaperAnalysis {
  document_id: string; title: string; authors: string[]; year: string | null; models: Fact[]; datasets: Fact[];
  metrics: Record<string, Fact>; limitations: Fact[]; future_work: Fact[]; not_extracted: string[]; filename: string;
}
export interface Comparison { papers: string[]; rows: Record<string, string[]>; markdown: string }
export interface EvidenceChunk {
  chunk_id: string; document_id: string; document_title: string; authors: string[]; page: number;
  section: string; text: string; source: string;
}
export interface GraphData {
  nodes: { kind: string; name: string }[];
  edges: { source: string; relation: string; target: string; page: number | null }[];
}
export interface Dashboard {
  documents: number; chunks: number; queries: number; claims_verified: number;
  verification_counts: Record<string, number>; mock_mode: boolean;
}
export type StreamEvent =
  | { event: "evidence"; data: Citation[] }
  | { event: "token"; data: string }
  | { event: "verification"; data: ClaimVerification[] }
  | { event: "done"; data: { status: string; mock_mode: boolean } }
  | { event: "error"; data: { code: string; message: string } };
export interface TableData { table_id: string; page: number; caption: string | null; headers: string[]; rows: string[][] }
