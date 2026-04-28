import type { Metadata } from "next";
import { Inter, Inter_Tight, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// next/font self-hosts these — no Google Fonts CDN request, no FOUT,
// automatic preload + font-display: swap.
const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});

const interTight = Inter_Tight({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-display",
  display: "swap",
});

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
  style: ["italic", "normal"],
  variable: "--font-serif",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SafetyRouter — Safety-Aware LLM Routing",
  description:
    "Safety-Aware LLM Routing Framework. Bias Detection + Bias Rephrasing + Mental Health Risk Detection + Human Escalation. Classifies locally at zero API cost.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${interTight.variable} ${instrumentSerif.variable} ${jetbrains.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}
