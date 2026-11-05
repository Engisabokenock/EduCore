/**
 * Admin API service functions — protected admin endpoints.
 */
import api from "@/lib/api";
import type {
  AdminUser,
  SystemSettings,
  AccountApplication,
  ActivityCategory,
  ActivityEntry,
  ActivitySummary,
  ApplicationCounts,
  ApprovalStatus,
  Paginated,
  School,
  Transaction,
  UserSubscription,
  DashboardStats,
  BulkActionRequest,
} from "@/types";

export const adminApi = {
  // Dashboard
  getStats: () => api.get<DashboardStats>("/admin-control-plane/dashboard/stats/"),

  // User management
  searchUsers: (payload: {
    role?: string;
    is_active?: boolean;
    search_term?: string;
    page?: number;
    page_size?: number;
  }) => api.post<AdminUser[]>("/admin-control-plane/users/search/", payload),

  updateUser: (userId: string, payload: { email?: string; role?: string; is_active?: boolean; full_name?: string }) =>
    api.patch<AdminUser>(`/admin-control-plane/users/${userId}/`, payload),

  // Resource management
  bulkResourceAction: (payload: BulkActionRequest) =>
    api.post<{ status: string; processed_records_count: number }>("/admin-control-plane/resources/bulk-action/", payload),

  // Reviews moderation
  bulkReviewAction: (payload: BulkActionRequest) =>
    api.post<{ status: string; affected_nodes_count: number }>("/admin-control-plane/moderation/reviews/bulk/", payload),

  // Financial
  getTransactions: (payload: {
    status?: string;
    phone_number?: string;
    mpesa_receipt?: string;
    page?: number;
    page_size?: number;
  }) => api.post<Transaction[]>("/admin-control-plane/financial/transactions/", payload),

  forceExpireSubscription: (subscriptionId: string) =>
    api.post(`/admin-control-plane/financial/subscriptions/${subscriptionId}/force-expire/`),

  // Schools
  getSchools: (isActive?: boolean) =>
    api.get<School[]>("/admin-control-plane/institutions/audit-list/", { params: isActive !== undefined ? { is_active: isActive } : {} }),

  // System settings
  getSystemSettings: () => api.get<SystemSettings>("/admin-control-plane/system-settings/"),

  updateSystemSettings: (payload: Partial<SystemSettings>) =>
    api.put<{ status: string; message: string }>("/admin-control-plane/system-settings/", payload),

  // Security / Super Admin
  overrideUserRole: (userId: string, payload: { email?: string; role?: string; is_active?: boolean; full_name?: string }) =>
    api.patch<AdminUser>(`/security-control-plane/users/${userId}/override/`, payload),

  // Account applications (teachers: admins review; admins: Super Admin reviews)
  getApplications: (params: { status?: ApprovalStatus; role?: "teacher" | "admin"; page?: number; page_size?: number }) =>
    api.get<Paginated<AccountApplication>>("/admin-control-plane/approvals/", { params }),

  getApplicationCounts: () => api.get<ApplicationCounts>("/admin-control-plane/approvals/summary/"),

  approveApplication: (userId: string, note?: string) =>
    api.post<AccountApplication>(`/admin-control-plane/approvals/${userId}/approve/`, { note: note || null }),

  rejectApplication: (userId: string, note?: string) =>
    api.post<AccountApplication>(`/admin-control-plane/approvals/${userId}/reject/`, { note: note || null }),

  // Platform activity (Super Admin only)
  getActivity: (params: {
    category?: ActivityCategory;
    action?: string;
    actor_id?: string;
    search?: string;
    since?: string;
    until?: string;
    page?: number;
    page_size?: number;
  }) => api.get<Paginated<ActivityEntry>>("/security-control-plane/activity/", { params }),

  getActivitySummary: (hours = 24) =>
    api.get<ActivitySummary>("/security-control-plane/activity/summary/", { params: { hours } }),
};
