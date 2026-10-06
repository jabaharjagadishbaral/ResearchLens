import type { Citation } from "./types.ts";

const CITE = /\[(\d+)\]/g;

/** Turn [n] into markdown links "#cite-n" ONLY when n maps to a real citation; unknown ids are dropped. */
export function linkifyCitations(answer: string, citations: Pick<Citation, "id">[]): string {
  const valid = new Set(citations.map((c) => c.id));
  return answer
    .replace(CITE, (_m, n: string) => (valid.has(Number(n)) ? `[\\[${n}\\]](#cite-${n})` : ""))
    .replace(/\s+([.,;:!?])/g, "$1")
    .replace(/ {2,}/g, " ");
}

export function citationIdFromHref(href: string | undefined): number | null {
  const m = href?.match(/^#cite-(\d+)$/);
  return m ? Number(m[1]) : null;
}

export function citedIds(answer: string): number[] {
  return [...new Set([...answer.matchAll(CITE)].map((m) => Number(m[1])))];
}
