"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import Feed from "@/components/Feed";
import { parseNumber, parseRanker } from "@/lib/params";

export default function FeedPage() {
  const sp = useSearchParams();
  const ranker = parseRanker(sp.get("ranker"));
  const detoks = ranker === "detoks";
  return (
    <main className="mx-auto h-dvh w-full max-w-md">
      <Feed
        key={sp.toString()}
        userId={sp.get("user") ?? "bob"}
        ranker={ranker}
        dailyCapMinutes={detoks ? parseNumber(sp.get("cap")) : undefined}
        feedSize={detoks ? parseNumber(sp.get("size")) : undefined}
        header={
          <Link href="/" aria-label="Back" className="flex items-center gap-1.5 text-sm font-medium text-paper [text-shadow:0_1px_2px_rgba(0,0,0,.5)]">
            <span aria-hidden className="text-lg leading-none">‹</span>
            <span className={detoks ? "text-sage" : "text-mist"}>{detoks ? "Detoks" : "Baseline"}</span>
          </Link>
        }
      />
    </main>
  );
}
