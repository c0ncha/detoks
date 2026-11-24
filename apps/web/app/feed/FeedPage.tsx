"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import Feed from "@/components/Feed";
import { parseNumber, parseRanker } from "@/lib/params";

export default function FeedPage() {
  const sp = useSearchParams();
  const ranker = parseRanker(sp.get("ranker"));
  return (
    <main className="mx-auto flex h-dvh w-full max-w-md flex-col">
      <div className="flex items-center justify-between px-3 py-2 text-sm">
        <Link href="/" className="text-white/60">← back</Link>
        <span className={ranker === "detoks" ? "text-emerald-400" : "text-white/80"}>{ranker}</span>
      </div>
      <div className="min-h-0 flex-1">
        <Feed key={sp.toString()} userId={sp.get("user") ?? "bob"} ranker={ranker}
          dailyCapMinutes={ranker === "detoks" ? parseNumber(sp.get("cap")) : undefined} />
      </div>
    </main>
  );
}
