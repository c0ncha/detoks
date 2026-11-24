"use client";

import { useEffect, useRef, useState } from "react";
import type { FeedItem, WatchEventIn } from "@/lib/api";
import { Heart, Info, Send, Sound } from "./icons";

const DOUBLE_TAP_MS = 250;

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

  // Single tap pauses/plays; a second tap within DOUBLE_TAP_MS turns it into a like instead.
  const tapTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [paused, setPaused] = useState(false);
  const [burst, setBurst] = useState(0);
  const onVideoClick = () => {
    if (tapTimer.current) return;
    tapTimer.current = setTimeout(() => {
      tapTimer.current = null;
      const v = ref.current;
      if (!v) return;
      if (v.paused) { v.play().catch(() => {}); setPaused(false); } else { v.pause(); setPaused(true); }
    }, DOUBLE_TAP_MS);
  };
  const onVideoDoubleClick = () => {
    if (tapTimer.current) { clearTimeout(tapTimer.current); tapTimer.current = null; }
    actions.current.liked = true;
    setLiked(true);
    setBurst((b) => b + 1);
  };

  const toggle = (key: "liked" | "shared", set: (b: boolean) => void) => {
    actions.current[key] = !actions.current[key];
    set(actions.current[key]);
  };

  return (
    <div className="relative h-full w-full overflow-hidden bg-ink">
      <video
        ref={ref}
        src={item.clip_url}
        className="h-full w-full object-cover"
        loop
        playsInline
        muted={muted}
        preload={active ? "auto" : "metadata"}
        onTimeUpdate={onTimeUpdate}
        onClick={onVideoClick}
        onDoubleClick={onVideoDoubleClick}
      />

      {burst > 0 && (
        <Heart key={burst} filled className="pointer-events-none absolute left-1/2 top-1/2 size-24 -translate-x-1/2 -translate-y-1/2 animate-[like-burst_700ms_ease-out_forwards] text-ember [filter:drop-shadow(0_2px_8px_rgba(15,17,16,.55))]" />
      )}
      {paused && (
        <div className="pointer-events-none absolute inset-0 grid place-items-center">
          <div className="size-16 rounded-full bg-paper/20 backdrop-blur-sm" aria-label="Paused" />
        </div>
      )}

      {/* Caption: bottom-left, two lines max */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink/85 via-ink/40 to-transparent px-4 pb-6 pr-20 pt-16 text-paper [text-shadow:0_1px_2px_rgba(0,0,0,.5)]">
        <div className="mb-1 text-xs font-medium uppercase tracking-wider text-mist">{item.category}</div>
        <p className="line-clamp-2 text-[15px] font-medium leading-snug">{item.title}</p>
        {item.flagged && (
          <div className="mt-2 inline-block rounded-full bg-ochre/90 px-2.5 py-0.5 text-xs font-medium text-ink">
            Sensitive: {Object.entries(item.harm).filter(([, s]) => s >= 0.5).map(([l]) => l.replace("_", " ")).join(", ")}
          </div>
        )}
      </div>

      {/* Right rail: no public counts */}
      <div className="absolute bottom-24 right-2 flex flex-col items-center gap-5 text-paper [filter:drop-shadow(0_1px_2px_rgba(0,0,0,.5))]">
        <RailButton label="Like" pressed={liked} onClick={() => toggle("liked", setLiked)}>
          <Heart filled={liked} className={liked ? "text-ember" : ""} />
        </RailButton>
        <RailButton label="Send to a friend" pressed={shared} onClick={() => toggle("shared", setShared)}>
          <Send filled={shared} className={shared ? "text-sage" : ""} />
        </RailButton>
        <RailButton label="Why this" onClick={() => setShowWhy(true)}>
          <Info />
        </RailButton>
      </div>
      <button aria-label={muted ? "Unmute" : "Mute"} onClick={onToggleMute}
        className="absolute right-3 top-14 rounded-full bg-ink/30 p-1.5 text-paper backdrop-blur-sm">
        <Sound filled={!muted} />
      </button>

      {showWhy && <WhySheet item={item} onClose={() => setShowWhy(false)} />}
    </div>
  );
}

function RailButton({ label, pressed, onClick, children }: {
  label: string; pressed?: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button aria-label={label} aria-pressed={pressed} onClick={onClick}
      className="grid size-11 place-items-center rounded-full transition-transform active:scale-90">
      {children}
    </button>
  );
}

const TERM_LABELS: Record<string, string> = {
  predicted_watch_seconds: "Predicted seconds you'll watch",
  relevance: "Matches what you're into",
  quality: "People share and discuss it",
  harm_penalty: "Sensitive-content penalty",
  passive_fatigue: "You've been on autopilot with this topic",
};

/** Placeholder for design step 4 (plain-language reasons + controls). Shows the ranker's score terms. */
function WhySheet({ item, onClose }: { item: FeedItem; onClose: () => void }) {
  const terms = Object.entries(item.reasons).filter(([k]) => !k.startsWith("rerank."));
  const max = Math.max(...terms.map(([, v]) => Math.abs(v)), 1e-6);
  return (
    <div className="absolute inset-0 z-20 flex items-end bg-ink/40" onClick={onClose}>
      <div role="dialog" aria-label="Why this video" onClick={(e) => e.stopPropagation()}
        className="w-full rounded-t-3xl bg-night px-5 pb-8 pt-3 text-paper">
        <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-mist/40" />
        <h2 className="font-serif text-2xl">Why this video</h2>
        <p className="mb-4 mt-1 text-sm text-mist">What the ranker weighed for this pick.</p>
        <ul className="space-y-3">
          {terms.map(([k, v]) => (
            <li key={k}>
              <div className="flex justify-between text-sm">
                <span>{TERM_LABELS[k] ?? k}<span className="block font-mono text-[11px] text-mist/60">{k}</span></span>
                <span className="tabular-nums text-mist">{v >= 0 ? "+" : ""}{v.toFixed(2)}</span>
              </div>
              <div className="mt-1 h-1.5 rounded-full bg-ink">
                <div className={`h-full rounded-full ${v >= 0 ? "bg-sage" : "bg-ember"}`} style={{ width: `${(Math.abs(v) / max) * 100}%` }} />
              </div>
            </li>
          ))}
        </ul>
        <button onClick={onClose} className="mt-6 w-full rounded-full bg-paper/10 py-3 text-sm font-medium">Close</button>
      </div>
    </div>
  );
}
