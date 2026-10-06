"use client";
import type { ReactNode } from "react";
import type { VerificationStatus } from "@/lib/types";
import { ApiError } from "@/lib/api";

const STYLE: Record<VerificationStatus, [string, string]> = {
  SUPPORTED: ["✓ Supported", "var(--ok)"], PARTIALLY_SUPPORTED: ["◐ Partially supported", "var(--warn)"],
  UNSUPPORTED: ["✕ Unsupported", "var(--bad)"], CONTRADICTED: ["⚠ Contradicted", "var(--bad)"],
  INSUFFICIENT_EVIDENCE: ["? Insufficient evidence", "var(--muted)"],
};
export const StatusBadge = ({ s }: { s: VerificationStatus }) =>
  <span className="badge" style={{ color: STYLE[s][1] }}>{STYLE[s][0]}</span>;
export const Err = ({ e }: { e: unknown }) =>
  e ? <p role="alert" className="err">{e instanceof ApiError ? e.message : "Something went wrong. Please retry."}</p> : null;
export const MockBanner = ({ on }: { on?: boolean }) => on
  ? <p className="banner" role="note">Mock mode: offline development providers are active. Answers are extracted from your documents, not written by an LLM.</p> : null;
export const Card = ({ title, children }: { title?: string; children: ReactNode }) =>
  <section className="card">{title && <h2>{title}</h2>}{children}</section>;
