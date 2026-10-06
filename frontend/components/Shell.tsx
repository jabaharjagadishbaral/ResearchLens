"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { clearToken, getToken } from "@/lib/session";

const LINKS = [["/dashboard", "Dashboard"], ["/papers", "Papers"], ["/chat", "Chat"], ["/compare", "Compare"],
  ["/knowledge-graph", "Graph"], ["/reports", "Reports"], ["/evaluation", "Evaluation"], ["/settings", "Settings"]];

export default function Shell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  useEffect(() => { if (!getToken()) router.replace("/login"); else setReady(true); }, [router]);
  if (!ready) return null;
  return (<>
    <nav className="top" aria-label="Main"><strong>ResearchMind AI</strong>
      {LINKS.map(([h, l]) => <Link key={h} href={h}>{l}</Link>)}
      <button style={{ marginLeft: "auto" }} onClick={() => { clearToken(); router.replace("/login"); }}>Sign out</button></nav>
    <main>{children}</main></>);
}
