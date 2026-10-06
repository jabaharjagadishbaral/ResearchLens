"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Shell from "@/components/Shell";
import { Card, Err } from "@/components/ui";
import { api } from "@/lib/client";
import type { Fact } from "@/lib/types";

const Facts = ({ f }: { f: Fact[] }) => f.length ? <ul>{f.map((x) => <li key={x.value + x.chunk_id}>{x.value} <span className="muted">(p. {x.page})</span></li>)}</ul> : <p className="muted">Not reported</p>;

export default function Paper() {
  const { id } = useParams<{ id: string }>();
  const tb = useQuery({ queryKey: ["tables", id], queryFn: () => api.tables(id) });
  const q = useQuery({ queryKey: ["analysis", id], queryFn: () => api.analyze(id) }), a = q.data;
  return (<Shell><Err e={q.error} />{a && <><h1>{a.title}</h1>
    <p className="muted">Extracted with heuristic rules, not an LLM. Not extracted by this build: {a.not_extracted.join(", ")}.</p>
    <Card title="Models"><Facts f={a.models} /></Card><Card title="Datasets"><Facts f={a.datasets} /></Card>
    <Card title="Metrics">{Object.keys(a.metrics).length ? <ul>{Object.entries(a.metrics).map(([k, f]) => <li key={k}>{k}: {f.value} <span className="muted">(p. {f.page})</span></li>)}</ul> : <p className="muted">Not reported</p>}</Card>
    <Card title="Limitations"><Facts f={a.limitations} /></Card><Card title="Future work"><Facts f={a.future_work} /></Card>
    <Card title="Extracted tables">{tb.data?.length ? tb.data.map((t) => <div key={t.table_id} style={{ overflowX: "auto" }}>
      <p className="muted">{t.table_id} · page {t.page}{t.caption ? ` · ${t.caption}` : ""}</p>
      <table><thead><tr>{t.headers.map((h, i) => <th key={i}>{h}</th>)}</tr></thead><tbody>{t.rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody></table></div>)
      : <p className="muted">No tables detected (detection is text-layout based).</p>}</Card></>}</Shell>);
}
