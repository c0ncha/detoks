import type { Metadata, Viewport } from "next";
import { Fraunces, Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-fraunces" });

export const metadata: Metadata = {
  title: "Detoks",
  description: "A short-form video feed that ranks for well-being instead of watch time.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#0f1110" };

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable} h-full antialiased`}>
      <body className="min-h-full bg-ink text-paper">{children}</body>
    </html>
  );
}
