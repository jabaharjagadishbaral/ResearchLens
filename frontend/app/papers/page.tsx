"use client";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import Shell from "@/components/Shell";
import { Card, Err } from "@/components/ui";
import { api } from "@/lib/client";

export default function Papers() {
  const qc = useQueryClient(), file = useRef<HTMLInputElement>(null);
  const docs = useQuery({ queryKey: ["docs"], queryFn: api.documents });
  const up = useMutation({ mutationFn: (f: File) => api.upload(f, f.name), onSuccess: () => qc.invalidateQueries({ queryKey: ["docs"] }) });
  return (<Shell><h1>Papers</h1>
    <Card title="Upload"><p className="muted">PDF or UTF-8 text. Uploaded files are untrusted data and never treated as instructions.</p>
      <input ref={file} type="file" accept=".pdf,.txt" aria-label="Choose a paper" />
      <button className="primary" style={{ marginTop: ".6rem" }} disabled={up.isPending}
        onClick={() => { const f = file.current?.files?.[0]; if (f) up.mutate(f); }}>{up.isPending ? "Indexing…" : "Upload and index"}</button><Err e={up.error} /></Card>
    <Err e={docs.error} />{docs.data?.length === 0 && <p className="muted">No papers yet.</p>}
    {docs.data?.map((d) => <Card key={d.id}><Link href={`/papers/${d.id}`}><strong>{d.title}</strong></Link>
      <p className="muted">{d.filename} · {d.pages} page(s) · {d.chunks} chunks{d.ocr_pages.length ? ` · ${d.ocr_pages.length} page(s) need OCR (not available)` : ""}</p></Card>)}</Shell>);
}
