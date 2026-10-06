"use client";
import { useQuery } from "@tanstack/react-query";
import Shell from "@/components/Shell";
import { Card, Err } from "@/components/ui";
import { api } from "@/lib/client";

const fmt = (v: unknown) => (typeof v === "number" ? v.toFixed(3) : "Not evaluated");
export default function Evaluation() {
  const q = useQuery({ queryKey: ["eval"], queryFn: api.evaluation }), r = q.data as Record<string, any> | undefined;
  return (<Shell><h1>Evaluation</h1><Err e={q.error} />
    {r && !r.evaluated && <p>Not evaluated. Run <code>make eval</code> and reload.</p>}
    {r?.evaluated && <><p className="banner">{r.note}</p>{["retrieval", "rag", "citations", "verification"].map((g) =>
      <Card key={g} title={g}><table><tbody>{Object.entries(r[g] ?? {}).map(([k, v]) => <tr key={k}><th scope="row">{k}</th><td>{k === "n_claims" ? String(v) : fmt(v)}</td></tr>)}</tbody></table></Card>)}</>}</Shell>);
}
