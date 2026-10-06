"use client";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import Shell from "@/components/Shell";
import { Card, Err } from "@/components/ui";
import { api } from "@/lib/client";

export default function Reports() {
  const [title, setTitle] = useState("Literature Review"), [question, setQuestion] = useState("");
  const m = useMutation({ mutationFn: () => api.review(title, question) });
  const download = () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([m.data!.markdown], { type: "text/markdown" })); a.download = "literature-review.md"; a.click(); };
  return (<Shell><h1>Literature review</h1>
    <Card><label>Title<input value={title} onChange={(e) => setTitle(e.target.value)} /></label>
      <label>Research question<textarea rows={2} value={question} onChange={(e) => setQuestion(e.target.value)} /></label>
      <button className="primary" disabled={!question.trim() || m.isPending} onClick={() => m.mutate()}>{m.isPending ? "Generating…" : "Generate"}</button>
      <p className="muted">Export is Markdown only; PDF and DOCX export are not implemented.</p></Card>
    <Err e={m.error} />{m.data && <Card><div className="row"><button onClick={download}>Download .md</button></div><ReactMarkdown>{m.data.markdown}</ReactMarkdown></Card>}</Shell>);
}
