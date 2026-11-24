"use client";

import { useEffect, useRef, useState } from "react";
import type { FeedItem, WatchEventIn } from "@/lib/api";

interface Props {
  item: FeedItem;
  active: boolean;
  muted: boolean;
  onToggleMute: () => void;
  // Called each time the user leaves this card, with what happened since they arrived.
  onLeave: (e: WatchEventIn) => void;
}

/** One full-height clip. Plays while active and reports watch time and actions when the user swipes away. */
export default function VideoCard({ item, active, muted, onToggleMute, onLeave }: Props) {
  const ref = useRef<HTMLVideoElement>(null);
  const watched = useRef(0);       // seconds played since this card became active (loops count)
  const lastTime = useRef(0);
  const [liked, setLiked] = useState(false);
  const [shared, setShared] = useState(false);
  const [showWhy, setShowWhy] = useState(false);
  const actions = useRef({ liked: false, shared: false });
  const reported = useRef({ liked: false, shared: false });
  const onLeaveRef = useRef(onLeave);
  useEffect(() => { onLeaveRef.current = onLeave; });

  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    const a = actions.current; // mutated in place by toggle(), never replaced
    if (active) {
      watched.current = 0;
      lastTime.current = v.currentTime;
      v.play().catch(() => {});
      return () => {
        v.pause();
        const r = reported.current;
        const acted = (a.liked && !r.liked) || (a.shared && !r.shared);
        // Below 0.3 s with no action is almost always React StrictMode's dev-only double effect, not a real view.
        if (watched.current < 0.3 && !acted) return;
        onLeaveRef.current({
          pid: item.pid,
          watch_seconds: Math.round(watched.current * 10) / 10,
          liked: a.liked && !r.liked,
          shared: a.shared && !r.shared,
        });
        reported.current = { ...a };
      };
    }
  }, [active, item.pid]);

  const onTimeUpdate = () => {
    const v = ref.current;
    if (!v || !active) return;
    const dt = v.currentTime - lastTime.current;
    if (dt > 0 && dt < 1.5) watched.current += dt; // ignore seeks and the jump back on loop
    lastTime.current = v.currentTime;
  };

  const toggle = (key: "liked" | "shared", set: (b: boolean) => void) => {
    actions.current[key] = !actions.current[key];
    set(actions.current[key]);
  };

  return (
    <div className="relative h-full w-full bg-black">
      <video
        ref={ref}
        src={item.clip_url}
        className="h-full w-full object-contain"
        loop
        playsInline
        muted={muted}
        preload={active ? "auto" : "metadata"}
        onTimeUpdate={onTimeUpdate}
        onClick={onToggleMute}
      />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-4 pr-20 text-white">
        <div className="text-xs uppercase tracking-wide text-white/70">{item.category}</div>
        <div className="font-medium leading-snug">{item.title}</div>
        {item.flagged && (
          <div className="mt-1 inline-block rounded bg-amber-500/90 px-2 py-0.5 text-xs text-black">
            Flagged: {Object.entries(item.harm).filter(([, s]) => s >= 0.5).map(([l]) => l).join(", ")}
          </div>
        )}
      </div>
      <div className="absolute bottom-6 right-3 flex flex-col items-center gap-4 text-white">
        <button aria-label="Like" onClick={() => toggle("liked", setLiked)} className="text-2xl">
          {liked ? "♥" : "♡"}
        </button>
        <button aria-label="Share" onClick={() => toggle("shared", setShared)} className={`text-xl ${shared ? "text-sky-400" : ""}`}>
          ↗
        </button>
        <button aria-label="Why am I seeing this" onClick={() => setShowWhy((s) => !s)} className="text-sm font-semibold">
          why?
        </button>
        <button aria-label={muted ? "Unmute" : "Mute"} onClick={onToggleMute} className="text-sm">
          {muted ? "🔇" : "🔊"}
        </button>
      </div>
      {showWhy && (
        <div className="absolute left-3 right-16 top-3 rounded bg-black/75 p-3 font-mono text-xs text-white">
          <div className="mb-1 text-white/60">score {item.score.toFixed(3)}</div>
          {Object.entries(item.reasons).map(([k, v]) => (
            <div key={k} className="flex justify-between gap-4">
              <span>{k}</span>
              <span>{v.toFixed(3)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
