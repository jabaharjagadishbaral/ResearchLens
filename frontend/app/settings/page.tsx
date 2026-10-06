"use client";
import { useQuery } from "@tanstack/react-query";
import Shell from "@/components/Shell";
import { Card, Err, MockBanner } from "@/components/ui";
import { api } from "@/lib/client";

export default function Settings() {
  const h = useQuery({ queryKey: ["health"], queryFn: api.health });
  return (<Shell><h1>Settings</h1><Err e={h.error} /><MockBanner on={h.data?.mock_mode} />
    <Card title="Providers"><p className="muted">Providers are configured on the server through environment variables (LLM_PROVIDER, EMBEDDING_PROVIDER, RERANKER_PROVIDER). They cannot be changed from the browser.</p>
      <p>Server status: {h.data?.status ?? "…"}</p></Card></Shell>);
}
