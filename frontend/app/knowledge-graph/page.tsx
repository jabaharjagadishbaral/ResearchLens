"use client";
import { useQuery } from "@tanstack/react-query";
import Shell from "@/components/Shell";
import { Err } from "@/components/ui";
import { api } from "@/lib/client";
import { layoutGraph } from "@/lib/graph";

const COLORS: Record<string, string> = { Paper: "#1d4ed8", Model: "#b45309", Dataset: "#15803d", Metric: "#7c3aed", Author: "#be185d" };
export default function GraphPage() {
  const q = useQuery({ queryKey: ["graph"], queryFn: api.graph }), g = q.data, W = 900, H = 560;
  const pos = g ? layoutGraph(g, W, H) : [], at = new Map(pos.map((n) => [n.name, n]));
  return (<Shell><h1>Knowledge graph</h1><Err e={q.error} />
    {g && !g.nodes.length && <p className="muted">Upload papers to build the graph.</p>}
    {g && g.nodes.length > 0 && <><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Knowledge graph" style={{ width: "100%", border: "1px solid var(--line)", borderRadius: 10 }}>
      {g.edges.map((e, i) => { const a = at.get(e.source), b = at.get(e.target); return a && b ? <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="currentColor" opacity=".25"><title>{e.relation}</title></line> : null; })}
      {pos.map((n) => <g key={n.kind + n.name}><circle cx={n.x} cy={n.y} r={n.kind === "Paper" ? 9 : 6} fill={COLORS[n.kind] ?? "#78716c"} />
        <text x={n.x + 10} y={n.y + 4} fontSize="11" fill="currentColor">{n.name.slice(0, 28)}</text></g>)}</svg>
      <table><thead><tr><th>Source</th><th>Relation</th><th>Target</th><th>Page</th></tr></thead><tbody>
        {g.edges.map((e, i) => <tr key={i}><td>{e.source}</td><td>{e.relation}</td><td>{e.target}</td><td>{e.page ?? "—"}</td></tr>)}</tbody></table></>}</Shell>);
}
