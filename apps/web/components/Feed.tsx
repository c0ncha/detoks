"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, type FeedItem, type FeedStatus, type RankerName, type Recap, type WatchEventIn } from "@/lib/api";
import VideoCard from "./VideoCard";

type Row =
  | { kind: "video"; key: string; item: FeedItem }
  | { kind: "break"; key: string; message: string }
  | { kind: "end"; key: string; status: FeedStatus; recap: Recap | null };

interface Props {
  userId: string;
  ranker: RankerName;
  label?: string;
  dailyCapMinutes?: number;
  feedSize?: number;
}

const BATCH = 5;

/**
 * A vertical swipe feed bound to one ranker session. The server decides what comes next and whether the feed
 * continues (ok), pauses for a break card (break) or stops (ended); this component only renders that and reports
 * watch events. New card types (e.g. a challenge prompt) go in `Row` and the render switch below.
 */
export default function Feed({ userId, ranker, label, dailyCapMinutes, feedSize }: Props) {
  // Parents remount Feed (via `key`) to start a new session; see FeedPage/ComparePage.
  const [rows, setRows] = useState<Row[]>([]);
  const [active, setActive] = useState(0);
  const [muted, setMuted] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const session = useRef<string | null>(null);
  const rowCount = useRef(0);
  const loading = useRef(false);
  const ended = useRef(false);
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => { rowCount.current = rows.length; }, [rows.length]);

  const endFeed = useCallback(async (sid: string, status: FeedStatus, afterIndex?: number) => {
    ended.current = true;
    const recap = await api.recap(sid).catch(() => null);
    setRows((prev) => {
      const kept = afterIndex === undefined ? prev : prev.slice(0, afterIndex + 1);
      return [...kept.filter((r) => r.kind !== "end"), { kind: "end", key: `end-${sid}`, status, recap }];
    });
  }, []);

  const loadMore = useCallback(async () => {
    const sid = session.current;
    if (!sid || loading.current || ended.current) return;
    loading.current = true;
    try {
      const { items, status } = await api.next(sid, BATCH);
      if (status.state === "ended" || items.length === 0) {
        await endFeed(sid, status);
        return;
      }
      setRows((prev) => [
        ...prev,
        ...(status.state === "break" ? [{ kind: "break" as const, key: `break-${prev.length}`, message: status.message }] : []),
        ...items.map((item) => ({ kind: "video" as const, key: `v-${item.pid}-${prev.length}`, item })),
      ]);
    } catch (e) {
      setError(String(e));
    } finally {
      loading.current = false;
    }
  }, [endFeed]);

  useEffect(() => {
    let cancelled = false;
    api.createSession({ user_id: userId, ranker, daily_cap_minutes: dailyCapMinutes, feed_size: feedSize })
      .then((r) => {
        if (cancelled) return;
        session.current = r.session_id;
        return loadMore();
      })
      .catch((e) => setError(String(e)));
    return () => { cancelled = true; };
  }, [userId, ranker, dailyCapMinutes, feedSize, loadMore]);

  // Track which card is on screen, and prefetch when the user is two cards from the end.
  useEffect(() => {
    const root = container.current;
    if (!root) return;
    const obs = new IntersectionObserver(
      (entries) => entries.forEach((e) => {
        if (!e.isIntersecting) return;
        const i = Number((e.target as HTMLElement).dataset.index);
        setActive(i);
        if (i >= rowCount.current - 2) loadMore();
      }),
      { root, threshold: 0.6 },
    );
    root.querySelectorAll("[data-index]").forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, [rows, loadMore]);

  const onLeave = useCallback(async (index: number, e: WatchEventIn) => {
    const sid = session.current;
    if (!sid) return;
    const status = await api.event(sid, e).catch(() => null);
    // A user-set time cap can end the feed mid-batch: drop the unwatched cards that were already loaded.
    if (status?.state === "ended" && !ended.current) endFeed(sid, status, index);
  }, [endFeed]);

  return (
    <div className="flex h-full flex-col">
      {label && <div className="px-3 py-2 text-center text-sm font-semibold text-white/80">{label}</div>}
      {error && <div className="m-3 rounded bg-red-900/60 p-3 text-sm text-red-100">{error}</div>}
      <div ref={container} className="no-scrollbar relative flex-1 snap-y snap-mandatory overflow-y-scroll rounded-xl bg-neutral-900">
        {rows.map((row, i) => (
          <div key={row.key} data-index={i} className="h-full w-full snap-start snap-always">
            {row.kind === "video" && (
              <VideoCard item={row.item} active={i === active} muted={muted}
                onToggleMute={() => setMuted((m) => !m)} onLeave={(e) => onLeave(i, e)} />
            )}
            {row.kind === "break" && <BreakCard message={row.message} />}
            {row.kind === "end" && <EndCard status={row.status} recap={row.recap} />}
          </div>
        ))}
        {rows.length === 0 && !error && <div className="p-6 text-center text-white/60">Loading…</div>}
      </div>
    </div>
  );
}

function BreakCard({ message }: { message: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 bg-emerald-950 p-8 text-center text-white">
      <div className="text-4xl">🌿</div>
      <div className="text-xl font-semibold">Time for a break?</div>
      <p className="text-white/80">{message}</p>
      <p className="text-sm text-white/50">Swipe up to keep watching.</p>
    </div>
  );
}

function EndCard({ status, recap }: { status: FeedStatus; recap: Recap | null }) {
  return (
    <div className="flex h-full flex-col justify-center gap-4 bg-indigo-950 p-8 text-white">
      <div className="text-2xl font-semibold">That&apos;s it for today</div>
      <p className="text-white/80">{status.message}</p>
      {recap && (
        <div className="space-y-1 text-sm">
          <div>{recap.minutes_watched.toFixed(1)} min · {recap.videos_watched} videos · {recap.shares} shared</div>
          <div className="text-white/60">Topics</div>
          {Object.entries(recap.minutes_by_category).slice(0, 6).map(([cat, min]) => (
            <div key={cat} className="flex justify-between"><span>{cat}</span><span>{min.toFixed(1)} min</span></div>
          ))}
        </div>
      )}
    </div>
  );
}
