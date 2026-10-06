"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/client";
import type { Citation } from "@/lib/types";
import { Err } from "./ui";

export default function EvidencePanel({ citations, selected, onSelect }: { citations: Citation[]; selected: number | null; onSelect: (id: number) => void }) {
  const cur = citations.find((c) => c.id === selected);
  const full = useQuery({ queryKey: ["evidence", cur?.chunk_id], queryFn: () => api.evidence(cur!.chunk_id), enabled: !!cur });
  return (<aside aria-label="Evidence"><h2>Evidence</h2>
    {!citations.length && <p className="muted">No evidence retrieved.</p>}
    {citations.map((c) => (<button key={c.id} onClick={() => onSelect(c.id)} aria-pressed={c.id === selected}
      style={{ display: "block", width: "100%", textAlign: "left", margin: ".3rem 0", borderColor: c.id === selected ? "var(--accent)" : undefined }}>
      <strong>[{c.id}] {c.document_title}</strong><br /><span className="muted">Page {c.page} · {c.section} · relevance {c.relevance.toFixed(2)}</span></button>))}
    {cur && <div className="card"><p className="muted">SOURCE EVIDENCE — {cur.document_title}, page {cur.page}, {cur.section}</p>
      <Err e={full.error} />{full.isLoading ? <p>Loading…</p> : <blockquote>{full.data?.text ?? cur.quote}</blockquote>}</div>}
  </aside>);
}
