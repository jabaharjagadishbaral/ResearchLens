import "./globals.css";
import "katex/dist/katex.min.css";
import type { ReactNode } from "react";
import Providers from "@/components/Providers";
export const metadata = { title: "ResearchMind AI", description: "Evidence-grounded research assistant" };
export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en"><body><Providers>{children}</Providers></body></html>;
}
