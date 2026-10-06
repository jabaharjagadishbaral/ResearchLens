import Link from "next/link";
const FEATURES: [string, string][] = [
  ["Evidence grounding", "Answers are built only from retrieved passages. Every [n] maps to a real chunk with its page and section; unknown citation ids are removed."],
  ["Hybrid retrieval + reranking", "BM25 and vector search are combined with configurable weights, then reranked to a small evidence set."],
  ["Claim verification", "Each answer sentence is checked against its cited evidence: supported, partial, unsupported, contradicted, or insufficient."],
  ["Paper comparison", "Models, datasets and metrics are extracted with page references. Missing values are shown as “Not reported”."],
  ["Knowledge graph", "Papers, models, datasets and metrics linked by typed relationships."],
  ["Measured evaluation", "Recall@K, MRR, nDCG, faithfulness and citation metrics. If nothing has been run, the page says “Not evaluated”."],
];
export default function Landing() {
  return (<main><section className="hero"><p className="muted">ResearchMind AI</p>
    <h1>Understand research.<br />Verify evidence.<br />Discover what comes next.</h1>
    <p className="muted" style={{ maxWidth: 560 }}>An evidence-grounded research assistant for searching, analyzing, comparing, and synthesizing academic literature.</p>
    <div className="row"><Link href="/login"><button className="primary">Start Research</button></Link>
      <Link href="/login?demo=1"><button>Explore Demo</button></Link></div></section>
    <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))" }}>
      {FEATURES.map(([t, d]) => <section className="card" key={t}><h2>{t}</h2><p className="muted">{d}</p></section>)}</div>
    <p className="muted">Multimodal figure understanding and OCR are planned, not yet available.</p></main>);
}
