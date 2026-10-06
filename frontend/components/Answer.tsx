"use client";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { citationIdFromHref, linkifyCitations } from "@/lib/citations";
import type { Citation } from "@/lib/types";

export default function Answer({ text, citations, onCite }: { text: string; citations: Citation[]; onCite: (id: number) => void }) {
  return <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}
    components={{ a: ({ href, children }) => {
      const id = citationIdFromHref(href);
      return id === null ? <a href={href} rel="noopener noreferrer" target="_blank">{children}</a>
        : <button className="cite" aria-label={`Show evidence ${id}`} onClick={() => onCite(id)}>{children}</button>;
    } }}>{linkifyCitations(text, citations)}</ReactMarkdown>;
}
