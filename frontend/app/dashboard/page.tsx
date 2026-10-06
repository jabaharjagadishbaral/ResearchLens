"use client";
import { useQuery } from "@tanstack/react-query";
import Shell from "@/components/Shell";
import { Card, Err, MockBanner } from "@/components/ui";
import { api } from "@/lib/client";

export default function DashboardPage() {
  const q = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const d = q.data, counts = d ? Object.entries(d.verification_counts) : [], max = Math.max(1, ...counts.map(([, n]) => n));
  return (<Shell><h1>Dashboard</h1><Err e={q.error} /><MockBanner on={d?.mock_mode} />
    {d && <><div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(170px,1fr))" }}>
      {([["Indexed documents", d.documents], ["Evidence chunks", d.chunks], ["Research queries", d.queries], ["Claims verified", d.claims_verified]] as const)
        .map(([l, n]) => <Card key={l}><p className="muted">{l}</p><h1>{n}</h1></Card>)}</div>
      <Card title="Verification outcomes">{counts.length ? counts.map(([k, n]) => <div key={k}><span>{k} — {n}</span><div className="bar" style={{ width: `${(100 * n) / max}%` }} /></div>)
        : <p className="muted">No claims verified yet.</p>}</Card></>}</Shell>);
}
