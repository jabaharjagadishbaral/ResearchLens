"use client";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Shell from "@/components/Shell";
import { Card, Err } from "@/components/ui";
import { api } from "@/lib/client";

export default function Compare() {
  const docs = useQuery({ queryKey: ["docs"], queryFn: api.documents }), [sel, setSel] = useState<string[]>([]);
  const cmp = useMutation({ mutationFn: () => api.compare(sel) });
  const toggle = (id: string) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  return (<Shell><h1>Compare papers</h1><Err e={docs.error} />
    <Card title="Select two or more">{docs.data?.map((d) => <label key={d.id} style={{ display: "block" }}>
      <input type="checkbox" style={{ width: "auto" }} checked={sel.includes(d.id)} onChange={() => toggle(d.id)} /> {d.title}</label>)}
      <button className="primary" disabled={sel.length < 2 || cmp.isPending} onClick={() => cmp.mutate()}>Compare</button></Card>
    <Err e={cmp.error} />{cmp.data && <div style={{ overflowX: "auto" }}><table><thead><tr><th>Category</th>{cmp.data.papers.map((p) => <th key={p}>{p}</th>)}</tr></thead>
      <tbody>{Object.entries(cmp.data.rows).map(([k, v]) => <tr key={k}><th scope="row">{k}</th>{v.map((c, i) => <td key={i} className={c === "Not reported" ? "muted" : ""}>{c}</td>)}</tr>)}</tbody></table></div>}</Shell>);
}
