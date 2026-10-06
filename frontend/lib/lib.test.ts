import { test } from "node:test";
import assert from "node:assert/strict";
import { SSEParser, readSSE } from "./sse.ts";
import { linkifyCitations, citationIdFromHref, citedIds } from "./citations.ts";
import { layoutGraph } from "./graph.ts";
import { ApiError, createClient } from "./api.ts";

test("SSE parser handles frames split across chunks and JSON/text data", () => {
  const p = new SSEParser();
  assert.deepEqual(p.push('event: token\ndata: "He'), []);
  const out = p.push('llo "\n\nevent: done\ndata: {"status":"answered"}\n\n');
  assert.deepEqual(out, [{ event: "token", data: "Hello " }, { event: "done", data: { status: "answered" } }]);
  assert.deepEqual(p.push("event: x\r\ndata: plain\r\n\r\n"), [{ event: "x", data: "plain" }]);
});

test("readSSE streams events from a Response body", async () => {
  const enc = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(c) { c.enqueue(enc.encode('event: token\ndata: "a"\n\nevent: do')); c.enqueue(enc.encode('ne\ndata: {"status":"answered","mock_mode":true}\n\n')); c.close(); },
  });
  const seen: string[] = [];
  await readSSE(new Response(body), (e) => seen.push(e.event));
  assert.deepEqual(seen, ["token", "done"]);
});

test("citations: only real ids become links; fabricated ids are dropped", () => {
  const cites = [{ id: 1 }, { id: 2 }];
  assert.equal(linkifyCitations("A claim [1]. Another [9].", cites), "A claim [\\[1\\]](#cite-1). Another.");
  assert.equal(citationIdFromHref("#cite-2"), 2);
  assert.equal(citationIdFromHref("https://x"), null);
  assert.deepEqual(citedIds("a [1] b [2] c [1]"), [1, 2]);
});

test("graph layout is deterministic, in bounds, and has unique positions", () => {
  const g = { nodes: [{ kind: "Paper", name: "P1" }, { kind: "Paper", name: "P2" }, { kind: "Model", name: "M" }, { kind: "Dataset", name: "D" }], edges: [] };
  const a = layoutGraph(g, 600, 400), b = layoutGraph(g, 600, 400);
  assert.deepEqual(a, b);
  for (const n of a) { assert.ok(n.x >= 0 && n.x <= 600 && n.y >= 0 && n.y <= 400); }
  assert.equal(new Set(a.map((n) => `${n.x.toFixed(1)},${n.y.toFixed(1)}`)).size, a.length);
  assert.equal(layoutGraph({ nodes: [], edges: [] }, 100, 100).length, 0);
});

test("api client: auth header, error mapping, upload form, stream", async () => {
  const calls: { url: string; init: RequestInit }[] = [];
  const mk = (res: () => Response) => createClient({
    baseUrl: "http://api", getToken: () => "tok",
    fetchImpl: (async (url: string, init: RequestInit) => { calls.push({ url, init }); return res(); }) as unknown as typeof fetch,
  });
  const ok = mk(() => Response.json([{ id: "d1" }]));
  assert.equal((await ok.documents())[0].id, "d1");
  assert.equal(new Headers(calls[0].init.headers).get("Authorization"), "Bearer tok");

  const bad = mk(() => Response.json({ error: { code: "rate_limited", message: "Too many requests." } }, { status: 429 }));
  await assert.rejects(bad.query("q"), (e: unknown) => e instanceof ApiError && e.code === "rate_limited" && e.status === 429);

  const html = mk(() => new Response("<html>", { status: 500 }));
  await assert.rejects(html.dashboard(), (e: unknown) => e instanceof ApiError && e.message === "Request failed (500).");

  const down = createClient({ baseUrl: "http://api", getToken: () => null, fetchImpl: (async () => { throw new TypeError("x"); }) as unknown as typeof fetch });
  await assert.rejects(down.health(), (e: unknown) => e instanceof ApiError && e.code === "network");

  const up = mk(() => Response.json({ id: "d2" }));
  await up.upload(new Blob(["hi"]), "a.txt");
  const last = calls[calls.length - 1];
  assert.ok(last.init.body instanceof FormData);
  assert.equal(new Headers(last.init.headers).has("Content-Type"), false); // browser sets multipart boundary

  const stream = mk(() => new Response('event: token\ndata: "x"\n\nevent: done\ndata: {"status":"answered","mock_mode":true}\n\n'));
  const evs: string[] = [];
  await stream.streamChat("q", (e) => evs.push(e.event));
  assert.deepEqual(evs, ["token", "done"]);
});
