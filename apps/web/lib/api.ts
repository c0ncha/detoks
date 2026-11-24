// Typed client for the ranker API (services/ranker/detoks/api.py). Keep these types in sync with
// the pydantic models there; FastAPI serves the schema at http://localhost:8000/docs.

export const RANKER_URL = process.env.NEXT_PUBLIC_RANKER_URL ?? "http://localhost:8000";

export type RankerName = "baseline" | "detoks";

export interface Persona {
  user_id: string;
  display_name: string;
  description: string;
  parent_controls: boolean;
}

export interface FeedItem {
  pid: number;
  clip_url: string;
  title: string;
  category: string;
  duration: number;
  score: number;
  reasons: Record<string, number>;
  harm: Record<string, number>;
  flagged: boolean;
}

export interface FeedStatus {
  state: "ok" | "break" | "ended";
  reason: string;
  message: string;
  minutes_watched: number;
  served: number;
  feed_size: number | null;
  cap_minutes: number | null;
}

export interface Recap {
  ranker: string;
  user: string;
  minutes_watched: number;
  videos_served: number;
  videos_watched: number;
  likes: number;
  shares: number;
  comments: number;
  topic_entropy_bits: number;
  top_category_share: number;
  flagged_served: number;
  flagged_rate: number;
  minutes_by_category: Record<string, number>;
}

export interface WatchEventIn {
  pid: number;
  watch_seconds: number;
  liked?: boolean;
  shared?: boolean;
  commented?: boolean;
  hated?: boolean;
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${RANKER_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) throw new Error(`${init?.method ?? "GET"} ${path} -> ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  personas: () => call<Persona[]>("/personas"),
  createSession: (body: { user_id: string; ranker: RankerName; daily_cap_minutes?: number; feed_size?: number }) =>
    call<{ session_id: string }>("/sessions", { method: "POST", body: JSON.stringify(body) }),
  next: (sessionId: string, n = 5) =>
    call<{ items: FeedItem[]; status: FeedStatus }>(`/sessions/${sessionId}/next?n=${n}`),
  event: (sessionId: string, e: WatchEventIn) =>
    call<FeedStatus>(`/sessions/${sessionId}/events`, { method: "POST", body: JSON.stringify(e) }),
  recap: (sessionId: string) => call<Recap>(`/sessions/${sessionId}/recap`),
};
