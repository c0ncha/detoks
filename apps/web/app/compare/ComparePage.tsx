"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import Feed from "@/components/Feed";
import { parseNumber } from "@/lib/params";

/** Same viewer, same catalog, two rankers, scrolled independently. */
export default function ComparePage() {
  const sp = useSearchParams();
  const user = sp.get("user") ?? "bob";
  return (
    <main className="flex h-dvh w-full flex-col px-4 pb-4">
      <div className="py-2 text-sm"><Link href="/" className="text-mist">‹ Back</Link></div>
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 md:grid-cols-2">
        <div className="min-h-[70dvh] md:min-h-0"><Feed key={`b-${sp}`} userId={user} ranker="baseline" label="Baseline · watch time" /></div>
        <div className="min-h-[70dvh] md:min-h-0">
          <Feed key={`d-${sp}`} userId={user} ranker="detoks" label="Detoks · well-being" dailyCapMinutes={parseNumber(sp.get("cap"))} />
        </div>
      </div>
    </main>
  );
}
