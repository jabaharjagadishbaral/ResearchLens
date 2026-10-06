import type { StreamEvent } from "./types.ts";

export interface RawEvent { event: string; data: unknown }

/** Incremental Server-Sent-Events parser: frames may be split across network chunks. */
export class SSEParser {
  private buf = "";

  push(chunk: string): RawEvent[] {
    this.buf += chunk.replace(/\r\n/g, "\n");
    const out: RawEvent[] = [];
    let i: number;
    while ((i = this.buf.indexOf("\n\n")) >= 0) {
      const frame = this.buf.slice(0, i);
      this.buf = this.buf.slice(i + 2);
      let event = "message";
      const data: string[] = [];
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""));
      }
      if (!data.length) continue;
      const raw = data.join("\n");
      let parsed: unknown = raw;
      try { parsed = JSON.parse(raw); } catch { /* keep raw text */ }
      out.push({ event, data: parsed });
    }
    return out;
  }
}

export async function readSSE(res: Response, onEvent: (e: StreamEvent) => void): Promise<void> {
  if (!res.body) throw new Error("Response has no body");
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  const p = new SSEParser();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    for (const e of p.push(dec.decode(value, { stream: true }))) onEvent(e as StreamEvent);
  }
}
