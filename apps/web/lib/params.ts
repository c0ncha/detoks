import type { RankerName } from "./api";

export function parseRanker(v: string | null): RankerName {
  return v === "baseline" ? "baseline" : "detoks";
}

export function parseNumber(v: string | null): number | undefined {
  const n = v === null ? NaN : Number(v);
  return Number.isFinite(n) && n > 0 ? n : undefined;
}
