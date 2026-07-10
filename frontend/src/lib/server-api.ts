/**
 * Server-side API helpers for server components and generateMetadata().
 * Uses native fetch (not axios) — safe to import only in server components.
 * Do NOT import in client components; use services/api-service.ts for those.
 *
 * URL behavior:
 * - If NEXT_PUBLIC_API_URL is set at build time, uses that absolute URL.
 * - Otherwise falls back to /api/v1 so requests go through Next.js rewrites.
 * - The dummy base URL avoids Node.js URL parsing issues in SSR.
 */
import type { Grade, Subject, Topic, Resource, Plan, PaginatedResponse } from "@/types";

const API_BASE = (
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
    : ""
);
const BASE = API_BASE ? `${API_BASE}/api/v1` : "/api/v1";

type SearchResults = {
  query: string;
  category: string;
  resources?: Resource[];
  grades?: Grade[];
  subjects?: Subject[];
  topics?: Topic[];
};

async function get<T>(path: string, params?: Record<string, string>): Promise<T | null> {
  const url = new URL(`${BASE}${path}`, "http://localhost");
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") url.searchParams.set(k, v);
    });
  }
  try {
    const res = await fetch(url.toString(), {
      next: { revalidate: 3600 },
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    const json = await res.json();
    // EduCore API wraps all responses in { success, data, ... }
    return (json.data ?? json) as T;
  } catch {
    return null;
  }
}

export const serverApi = {
  getGrades: (curriculum?: string) =>
    get<Grade[]>("/academic/grades/", curriculum ? { curriculum } : undefined),

  getGrade: (slug: string) => get<Grade>(`/academic/grades/${slug}/`),

  getSubjects: (gradeSlug?: string) =>
    get<Subject[]>("/academic/subjects/", gradeSlug ? { grade__slug: gradeSlug } : undefined),

  getSubject: (slug: string) => get<Subject>(`/academic/subjects/${slug}/`),

  getTopics: (subjectSlug: string) =>
    get<Topic[]>(`/academic/subjects/${subjectSlug}/topics/`),

  getResources: (params: Record<string, string>) =>
    get<PaginatedResponse<Resource>>("/resources/", params),

  getResource: (slug: string) => get<Resource>(`/resources/${slug}/`),

  getPlans: () => get<Plan[]>("/subscriptions/plans/"),

  search: (q: string, category?: string) =>
    get<SearchResults>("/search/", { q, ...(category ? { category } : {}) }),
};
