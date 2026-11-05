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

/**
 * Shared secret identifying this server to the API. Server-side requests all come from
 * one address; without it every visitor would share a single rate-limit budget.
 */
const INTERNAL_TOKEN = process.env.INTERNAL_API_TOKEN;

/**
 * Thrown when the API could not answer (rate limited, down, timed out). Pages let it
 * reach the error boundary, which offers a retry, instead of showing a false 404.
 */
export class ApiUnavailableError extends Error {
  constructor(path: string, detail: string) {
    super(`The EduCore API is temporarily unavailable (${path}: ${detail}).`);
    this.name = "ApiUnavailableError";
  }
}

type GetOptions = {
  revalidate?: number;
  /** Return null only for a real 404 and throw ApiUnavailableError for anything else. */
  strict?: boolean;
};

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
  { revalidate = REVALIDATE_SECONDS, strict = false }: GetOptions = {},
): Promise<T | null> {
  const url = new URL(`${BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") url.searchParams.set(k, v);
    });
  }
  const headers: Record<string, string> = { Accept: "application/json" };
  if (INTERNAL_TOKEN) headers["X-Internal-Token"] = INTERNAL_TOKEN;

  let res: Response;
  try {
    res = await fetch(url.toString(), {
      next: { revalidate },
      headers,
      signal: AbortSignal.timeout(10_000),
    });
  } catch (error) {
    console.error(`[serverApi] request to ${url.pathname} failed:`, (error as Error).message);
    if (strict) throw new ApiUnavailableError(url.pathname, (error as Error).message);
    return null;
  }

  if (res.ok) return (await res.json()) as T;
  if (res.status === 404) return null;

  console.error(`[serverApi] ${res.status} from ${url.pathname}`);
  if (strict) throw new ApiUnavailableError(url.pathname, `HTTP ${res.status}`);
  return null;
}

/**
 * Pages that call notFound() on null must pass `{ strict: true }`, so an outage shows
 * the retry page rather than "Page not found". Pages with built-in fallback content
 * can use the lenient default (null on any failure).
 */
export const serverApi = {
  getGrades: (curriculum?: string, opts?: GetOptions) =>
    get<Grade[]>("/academic/grades/", { curriculum }, opts),

  getGrade: (slug: string, opts?: GetOptions) =>
    get<Grade>(`/academic/grades/${encodeURIComponent(slug)}/`, undefined, opts),

  getSubjects: (grade?: string) => get<Subject[]>("/academic/subjects/", { grade }),

  /** Subject slugs repeat across grades — always pass the grade slug when known. */
  getSubject: (slug: string, grade?: string, opts?: GetOptions) =>
    get<Subject>(`/academic/subjects/${encodeURIComponent(slug)}/`, { grade }, opts),

  getTopics: (subjectSlug: string, grade?: string, opts?: GetOptions) =>
    get<Topic[]>(`/academic/subjects/${encodeURIComponent(subjectSlug)}/topics/`, { grade }, opts),

  getResources: (params: Record<string, string>) =>
    get<PaginatedResponse<Resource>>("/resources/", params),

  getResource: (slug: string, opts?: GetOptions) =>
    get<Resource>(`/resources/${encodeURIComponent(slug)}/`, undefined, opts),

  getPlans: () => get<Plan[]>("/subscriptions/plans/"),

  search: (q: string, category?: string) =>
    get<SearchResults>("/search/", { q, ...(category ? { category } : {}) }, { revalidate: 60 }),
};
