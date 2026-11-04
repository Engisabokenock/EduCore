/**
 * Server-side API helpers for server components, generateMetadata() and sitemap.
 * Uses native fetch (not axios) — import only in server components.
 * Client components use services/api-service.ts.
 *
 * URL resolution (server side has no browser origin, so the URL must be absolute):
 *   1. API_INTERNAL_URL  — private network address of the backend (e.g. http://api:8000
 *      in Docker, or the Railway/Render private URL). Not exposed to the browser.
 *   2. NEXT_PUBLIC_API_URL — public backend URL.
 *   3. http://localhost:8000 — local development default.
 *
 * Previously a relative "/api/v1" was resolved against http://localhost (port 80), so
 * every server-side request failed and pages silently fell back to placeholder data.
 */
import type { Grade, Subject, Topic, Resource, Plan, PaginatedResponse } from "@/types";

const API_ORIGIN = (
  process.env.API_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000"
).replace(/\/+$/, "");

const BASE = `${API_ORIGIN}/api/v1`;

/** Seconds cached pages keep catalogue data before revalidating. */
const REVALIDATE_SECONDS = 300;

export type SearchResults = {
  query: string;
  category: string | null;
  resources?: Resource[];
  grades?: Grade[];
  subjects?: Subject[];
  topics?: Topic[];
};

async function get<T>(
  path: string,
  params?: Record<string, string | undefined>,
  revalidate: number = REVALIDATE_SECONDS,
): Promise<T | null> {
  const url = new URL(`${BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") url.searchParams.set(k, v);
    });
  }
  try {
    const res = await fetch(url.toString(), {
      next: { revalidate },
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(10_000),
    });
    if (!res.ok) {
      if (res.status >= 500) {
        console.error(`[serverApi] ${res.status} from ${url.pathname}`);
      }
      return null;
    }
    return (await res.json()) as T;
  } catch (error) {
    console.error(`[serverApi] request to ${url.pathname} failed:`, (error as Error).message);
    return null;
  }
}

export const serverApi = {
  getGrades: (curriculum?: string) => get<Grade[]>("/academic/grades/", { curriculum }),

  getGrade: (slug: string) => get<Grade>(`/academic/grades/${encodeURIComponent(slug)}/`),

  getSubjects: (grade?: string) => get<Subject[]>("/academic/subjects/", { grade }),

  /** Subject slugs repeat across grades — always pass the grade slug when known. */
  getSubject: (slug: string, grade?: string) =>
    get<Subject>(`/academic/subjects/${encodeURIComponent(slug)}/`, { grade }),

  getTopics: (subjectSlug: string, grade?: string) =>
    get<Topic[]>(`/academic/subjects/${encodeURIComponent(subjectSlug)}/topics/`, { grade }),

  getResources: (params: Record<string, string>) =>
    get<PaginatedResponse<Resource>>("/resources/", params),

  getResource: (slug: string) => get<Resource>(`/resources/${encodeURIComponent(slug)}/`),

  getPlans: () => get<Plan[]>("/subscriptions/plans/"),

  search: (q: string, category?: string) =>
    get<SearchResults>("/search/", { q, ...(category ? { category } : {}) }, 60),
};
