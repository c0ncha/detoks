// Detoks's own line icons (24px grid, 1.75 stroke). Not taken from any other app.
type P = { className?: string; filled?: boolean };
const base = { width: 28, height: 28, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.75,
  strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };

export const Heart = ({ className, filled }: P) => (
  <svg {...base} className={className} fill={filled ? "currentColor" : "none"}>
    <path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" />
  </svg>
);
export const Send = ({ className, filled }: P) => (
  <svg {...base} className={className} fill={filled ? "currentColor" : "none"}>
    <path d="M4 12 20 4l-5 16-3.5-6.5z" /><path d="m11.5 13.5 3-3" />
  </svg>
);
export const Info = ({ className }: P) => (
  <svg {...base} className={className}>
    <circle cx="12" cy="12" r="8.5" /><path d="M12 11v5" /><circle cx="12" cy="8" r=".6" fill="currentColor" />
  </svg>
);
export const Sound = ({ className, filled: on }: P) => (
  <svg {...base} width={22} height={22} className={className}>
    <path d="M4 9.5h3l4-3.5v12l-4-3.5H4z" />
    {on ? <path d="M15 9a4 4 0 0 1 0 6M17.5 6.5a7.5 7.5 0 0 1 0 11" /> : <path d="m15.5 9.5 5 5m0-5-5 5" />}
  </svg>
);
