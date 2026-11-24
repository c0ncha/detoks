"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, rankerUrl, type Persona } from "@/lib/api";

export default function Picker() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [user, setUser] = useState("bob");
  const [cap, setCap] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.personas().then(setPersonas).catch(() => setError(`Can't reach the ranker at ${rankerUrl()}. Is \`make ranker\` running?`));
  }, []);

  const q = (ranker?: string) => {
    const p = new URLSearchParams({ user });
    if (ranker) p.set("ranker", ranker);
    if (cap) p.set("cap", cap);
    return p.toString();
  };

  return (
    <div className="space-y-6">
      {error && <div className="rounded bg-red-900/60 p-3 text-sm">{error}</div>}
      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-white/60">Who is watching</h2>
        {personas.map((p) => (
          <label key={p.user_id} className={`block cursor-pointer rounded-lg border p-3 ${user === p.user_id ? "border-sky-400 bg-sky-950/40" : "border-white/10"}`}>
            <input type="radio" name="user" className="sr-only" checked={user === p.user_id} onChange={() => setUser(p.user_id)} />
            <div className="font-medium">{p.display_name}{p.parent_controls && <span className="ml-2 text-xs text-amber-300">parent controls</span>}</div>
            <div className="text-sm text-white/60">{p.description}</div>
          </label>
        ))}
      </section>
      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-white/60">Daily limit (Detoks only)</h2>
        <input type="number" min={1} placeholder="minutes, optional" value={cap} onChange={(e) => setCap(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-transparent p-2" />
      </section>
      <section className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <Link href={`/feed?${q("baseline")}`} className="rounded-lg bg-neutral-700 p-3 text-center font-medium">Baseline feed</Link>
        <Link href={`/feed?${q("detoks")}`} className="rounded-lg bg-emerald-700 p-3 text-center font-medium">Detoks feed</Link>
        <Link href={`/compare?${q()}`} className="rounded-lg bg-sky-700 p-3 text-center font-medium">Compare side by side</Link>
      </section>
    </div>
  );
}
