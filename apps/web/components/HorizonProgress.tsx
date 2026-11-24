/**
 * "Today's N": a thin horizon line with a sun dot that moves one step per video and warms toward dusk
 * near the end. Only finite feeds have one; it never resets or loops (docs/design.md).
 */
export default function HorizonProgress({ current, total }: { current: number; total: number }) {
  const frac = total > 0 ? Math.min(current / total, 1) : 0;
  const nearEnd = total - current < 3;
  return (
    <div
      role="progressbar"
      aria-label="Today's feed"
      aria-valuemin={0}
      aria-valuemax={total}
      aria-valuenow={current}
      aria-valuetext={`${current} of ${total}`}
      className="pointer-events-none absolute inset-x-4 top-3 z-10 flex items-center gap-3"
    >
      <div className="relative h-px flex-1 bg-paper/30">
        <div className="absolute inset-y-0 left-0 bg-paper/70 transition-[width] duration-500" style={{ width: `${frac * 100}%` }} />
        <div
          className={`absolute top-1/2 size-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full shadow-[0_0_10px] transition-[left,background-color] duration-500 ${nearEnd ? "bg-ember shadow-ember/70" : "bg-sun shadow-sun/60"}`}
          style={{ left: `${frac * 100}%` }}
        />
      </div>
      <span className="text-xs font-medium tabular-nums text-paper/80 [text-shadow:0_1px_2px_rgba(0,0,0,.5)]">
        {current}/{total}
      </span>
    </div>
  );
}
