import type { GraphData } from "./types.ts";

export interface PositionedNode { kind: string; name: string; x: number; y: number }

/** Deterministic concentric layout: papers on the inner ring, each other kind on its own outer ring. */
export function layoutGraph(g: GraphData, width: number, height: number): PositionedNode[] {
  const kinds = ["Paper", ...[...new Set(g.nodes.map((n) => n.kind))].filter((k) => k !== "Paper").sort()];
  const cx = width / 2, cy = height / 2, maxR = Math.min(width, height) / 2 - 30;
  const out: PositionedNode[] = [];
  kinds.forEach((kind, ring) => {
    const nodes = g.nodes.filter((n) => n.kind === kind).sort((a, b) => a.name.localeCompare(b.name));
    const r = kinds.length === 1 ? 0 : maxR * (0.25 + (0.75 * ring) / (kinds.length - 1));
    nodes.forEach((n, i) => {
      const a = (2 * Math.PI * i) / nodes.length + ring * 0.4;
      out.push({ ...n, x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) });
    });
  });
  return out;
}
