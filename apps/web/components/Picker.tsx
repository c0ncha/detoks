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
      {error && <div className="rounded-xl bg-ember/15 p-3 text-sm text-ember">{error}</div>}
      <section className="space-y-2">
        <h2 className="text-xs font-medium uppercase tracking-wider text-mist">Who is watching</h2>
        {personas.map((p) => (
          <label key={p.user_id} className={`block cursor-pointer rounded-2xl border p-4 transition-colors ${user === p.user_id ? "border-sage bg-sage/10" : "border-paper/10 hover:border-paper/25"}`}>
            <input type="radio" name="user" className="sr-only" checked={user === p.user_id} onChange={() => setUser(p.user_id)} />
            <div className="font-medium">{p.display_name}{p.parent_controls && <span className="ml-2 rounded-full bg-ochre/15 px-2 py-0.5 text-xs text-ochre">parent controls</span>}</div>
            <div className="mt-0.5 text-sm text-mist">{p.description}</div>
          </label>
        ))}
      </section>
      <section className="space-y-2">
        <h2 className="text-xs font-medium uppercase tracking-wider text-mist">Daily limit (Detoks only)</h2>
        <input type="number" min={1} placeholder="minutes, optional" value={cap} onChange={(e) => setCap(e.target.value)}
          className="w-full rounded-2xl border border-paper/10 bg-transparent p-3 tabular-nums placeholder:text-stone focus:border-sage focus:outline-none" />
      </section>
      <section className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <Link href={`/feed?${q("baseline")}`} className="rounded-full border border-paper/20 p-3 text-center font-medium">Baseline feed</Link>
        <Link href={`/feed?${q("detoks")}`} className="rounded-full bg-sage p-3 text-center font-medium text-ink">Detoks feed</Link>
        <Link href={`/compare?${q()}`} className="rounded-full border border-sage/50 p-3 text-center font-medium text-sage">Compare side by side</Link>
      </section>
    </div>
  );
}
