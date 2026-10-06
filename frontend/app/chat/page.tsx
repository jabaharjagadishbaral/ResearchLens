"use client";
import { useRef, useState, type FormEvent } from "react";
import Shell from "@/components/Shell";
import Answer from "@/components/Answer";
import EvidencePanel from "@/components/EvidencePanel";
import { Err, MockBanner, StatusBadge } from "@/components/ui";
import { api } from "@/lib/client";
import type { Citation, ClaimVerification } from "@/lib/types";

interface Turn { question: string; answer: string; citations: Citation[]; verification: ClaimVerification[]; mock: boolean; status: string }

export default function Chat() {
  const [q, setQ] = useState(""), [turns, setTurns] = useState<Turn[]>([]), [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null), [sel, setSel] = useState<number | null>(null), abort = useRef<AbortController | null>(null);
  const cur = turns[turns.length - 1];
  const patch = (f: (t: Turn) => Turn) => setTurns((ts) => ts.map((t, i) => (i === ts.length - 1 ? f(t) : t)));

  async function ask(question: string) {
    abort.current?.abort(); abort.current = new AbortController();
    setBusy(true); setErr(null); setSel(null);
    setTurns((t) => [...t, { question, answer: "", citations: [], verification: [], mock: false, status: "" }]);
    try {
      await api.streamChat(question, (e) => {
        if (e.event === "evidence") patch((t) => ({ ...t, citations: e.data }));
        else if (e.event === "token") patch((t) => ({ ...t, answer: t.answer + e.data }));
        else if (e.event === "verification") patch((t) => ({ ...t, verification: e.data }));
        else if (e.event === "done") patch((t) => ({ ...t, mock: e.data.mock_mode, status: e.data.status }));
        else if (e.event === "error") setErr({ message: e.data.message });
      }, abort.current.signal);
    } catch (x) { if (!(x instanceof DOMException)) setErr(x); } finally { setBusy(false); }
  }
  const submit = (e: FormEvent) => { e.preventDefault(); if (q.trim() && !busy) { ask(q.trim()); setQ(""); } };
  const exportMd = () => {
    const md = turns.map((t) => `## ${t.question}\n\n${t.answer}\n\n${t.citations.map((c) => `[${c.id}] ${c.document_title}, p. ${c.page}, ${c.section}`).join("\n")}`).join("\n\n");
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([md], { type: "text/markdown" })); a.download = "conversation.md"; a.click();
  };
  return (<Shell><h1>Research chat</h1><MockBanner on={cur?.mock} />
    <div className="grid cols"><div>
      {turns.map((t, i) => <section className="card" key={i}><p><strong>{t.question}</strong></p>
        {t.status === "insufficient_evidence" ? <p>{t.answer}</p> : <Answer text={t.answer} citations={t.citations} onCite={setSel} />}
        {t.verification.length > 0 && <details><summary>Claim verification ({t.verification.length})</summary>
          {t.verification.map((v, j) => <div key={j} className="card"><StatusBadge s={v.status} /> {v.claim}
            {v.page && <p className="muted">{v.document_title}, page {v.page}</p>}{v.evidence_sentence && <blockquote>{v.evidence_sentence}</blockquote>}</div>)}</details>}
        {i === turns.length - 1 && !busy && <div className="row">
          <button onClick={() => ask(t.question)}>Regenerate</button>
          <button onClick={() => navigator.clipboard.writeText(t.answer)}>Copy</button></div>}</section>)}
      <Err e={err} />
      <form onSubmit={submit} className="card"><label>Ask a research question<textarea rows={3} value={q} onChange={(e) => setQ(e.target.value)} maxLength={2000} /></label>
        <div className="row" style={{ marginTop: ".6rem" }}><button className="primary" disabled={busy}>{busy ? "Working…" : "Ask"}</button>
          {turns.length > 0 && <button type="button" onClick={exportMd}>Export conversation</button>}</div></form>
      <p className="muted">Conversation history is kept in this tab only; it is not saved to your account.</p></div>
      <EvidencePanel citations={cur?.citations ?? []} selected={sel} onSelect={setSel} /></div></Shell>);
}
