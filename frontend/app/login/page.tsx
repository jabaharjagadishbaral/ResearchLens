"use client";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { api } from "@/lib/client";
import { setToken } from "@/lib/session";
import { Err } from "@/components/ui";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState(""), [pw, setPw] = useState(""), [mode, setMode] = useState<"login" | "register">("login");
  const [err, setErr] = useState<unknown>(null), [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      if (mode === "register") await api.register(email, pw);
      setToken((await api.login(email, pw)).access_token); router.replace("/dashboard");
    } catch (x) { setErr(x); } finally { setBusy(false); }
  }
  return (<main style={{ maxWidth: 420 }}><h1>{mode === "login" ? "Sign in" : "Create account"}</h1>
    <form onSubmit={submit} className="card"><label>Email<input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" /></label>
      <label>Password (min 10 characters)<input type="password" required minLength={10} value={pw} onChange={(e) => setPw(e.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>
      <Err e={err} /><div className="row" style={{ marginTop: ".8rem" }}><button className="primary" disabled={busy}>{mode === "login" ? "Sign in" : "Register"}</button>
        <button type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "Need an account?" : "Have an account?"}</button></div></form>
    <p className="muted">The demo has no bundled sample papers yet: register, then upload your own PDFs or text files.</p></main>);
}
