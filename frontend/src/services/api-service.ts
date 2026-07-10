/**
 * API service functions — thin wrappers around the api client.
 * Components use React Query with these functions.
 */
import api from "@/lib/api";
import type {
  User, AuthTokens, Grade, Subject, Topic,
  Resource, Plan, Subscription, PaginatedResponse,
} from "@/types";

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authService = {
  register: (data: {
    email: string; first_name: string; last_name: string;
    password: string; password_confirm: string; role?: string;
  }) => api.post<{ tokens: AuthTokens; user: User }>("/auth/register/", data),

  login: (email: string, password: string) =>
    api.post<{ tokens: AuthTokens; user: User }>("/auth/login/", { email, password }),

  me: () => api.get<User>("/auth/me/"),

  changePassword: (old_password: string, new_password: string, new_password_confirm: string) =>
    api.post("/users/me/change-password/", { old_password, new_password, new_password_confirm }),

  forgotPassword: (email: string) => api.post("/users/forgot-password/", { email }),

  resetPassword: (token: string, new_password: string, new_password_confirm: string) =>
    api.post("/users/reset-password/", { token, new_password, new_password_confirm }),

  verifyEmail: (token: string) => api.get(`/users/verify-email/?token=${token}`),
};

// ── Academic ──────────────────────────────────────────────────────────────────

export const academicService = {
  getGrades: (curriculum?: string) =>
    api.get<Grade[]>("/academic/grades/", { params: { curriculum } }),

  getGrade: (slug: string) => api.get<Grade>(`/academic/grades/${slug}/`),

  getSubjects: () =>
    api.get<Subject[]>("/academic/subjects/"),

  getSubject: (slug: string) => api.get<Subject>(`/academic/subjects/${slug}/`),

  getTopics: (subjectSlug: string) =>
    api.get<Topic[]>(`/academic/subjects/${subjectSlug}/topics/`),
};

// ── Content ───────────────────────────────────────────────────────────────────

export const contentService = {
  getResources: (params?: {
    grade?: string; subject?: string; topic?: string;
    type?: string; access?: string; year?: number;
    search?: string; page?: number;
  }) => api.get<PaginatedResponse<Resource>>("/resources/", { params }),

  getResource: (slug: string) => api.get<Resource>(`/resources/${slug}/`),

  downloadResource: (slug: string) =>
    api.post<{ url: string }>(`/resources/${slug}/download/`),

  getMyDownloads: (page?: number) =>
    api.get("/downloads/history/", { params: { page } }),
};

// ── Commerce ─────────────────────────────────────────────────────────────────

export const commerceService = {
  getPlans: () => api.get<Plan[]>("/subscriptions/plans/"),

  getSubscription: () => api.get<Subscription>("/subscriptions/me/"),

  initiatePayment: (plan_id: string, phone_number: string) =>
    api.post("/payments/buy-premium/", { plan_id, phone_number }),

  getMyPayments: () => api.get("/payments/history/"),
};

// ── Community ─────────────────────────────────────────────────────────────────

export const communityService = {
  getReviews: (resourceId: string) =>
    api.get(`/reviews/resource/${resourceId}/`),

  createReview: (data: { resource: string; rating: number; comment?: string }) =>
    api.post("/reviews/", data),
};

// ── Notifications ─────────────────────────────────────────────────────────────

export const notificationService = {
  getAll: (unread?: boolean) =>
    api.get("/notifications/", { params: unread ? { unread: "true" } : undefined }),

  getUnreadCount: () => api.get<{ unread_count: number }>("/notifications/unread-count/"),

  markRead: (id: string) => api.post(`/notifications/${id}/read/`),

  markAllRead: () => api.post("/notifications/mark-all-read/"),
};

// ── Search ────────────────────────────────────────────────────────────────────

export const searchService = {
  search: (q: string, category?: string) =>
    api.get("/search/", { params: { q, category } }),
};
