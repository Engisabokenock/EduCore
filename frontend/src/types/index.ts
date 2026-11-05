/**
 * All TypeScript interfaces for the EduCore API.
 */

export type UserRole = "super_admin" | "admin" | "school_admin" | "teacher" | "student" | "parent";

export type ApprovalStatus = "approved" | "pending" | "rejected";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  role: UserRole;
  is_verified: boolean;
  is_active?: boolean;
  approval_status?: ApprovalStatus;
  avatar_url?: string | null;
  date_joined: string;
  last_login_at?: string | null;
  profile: Profile | null;
}

export interface Profile {
  avatar: string | null;
  bio: string;
  school: string;
  grade_level: string;
  county: string;
  subjects_of_interest: string[];
  notification_preferences: Record<string, boolean>;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

/** Register/login response. `tokens` is null while a teacher/admin account awaits approval. */
export interface AuthResult {
  tokens: AuthTokens | null;
  user: User;
  requires_approval?: boolean;
  message?: string | null;
}

export interface Grade {
  id: string;
  name: string;
  slug: string;
  code: string;
  order: number;
  curriculum: string;
  is_active: boolean;
  subject_count: number;
  subjects?: Subject[];
}

export interface Subject {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon: string;
  color: string;
  order: number;
  is_active: boolean;
  topic_count: number;
  grade: { id: string; name: string; slug: string; code: string } | null;
  topics?: Topic[];
}

export interface Topic {
  id: string;
  name: string;
  slug: string;
  description?: string;
  order: number;
  ordering?: number;
  is_active: boolean;
  resource_count: number;
}

export interface Resource {
  id: string;
  title: string;
  slug: string;
  description: string;
  resource_type: "revision_paper" | "worksheet" | "exam" | "mock_exam" | "past_paper" | "lesson_note" | "marking_scheme" | "scheme_of_work" | "lesson_plan";
  is_premium: boolean;
  grade_id: string;
  subject_id: string;
  topic_id: string | null;
  grade: { id: string; name: string; slug: string } | null;
  subject: { id: string; name: string; slug: string } | null;
  topic: { id: string; name: string; slug: string } | null;
  thumbnail: string | null;
  thumbnail_url?: string | null;
  type_variant?: string;
  file_type: string;
  file_size: number;
  year: number;
  term: 1 | 2 | 3 | null;
  tags: string[];
  views_count: number;
  downloads_count: number;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
  can_access?: boolean | null;
}

export interface ResourceAccess {
  can_access: boolean;
  is_premium: boolean;
  requires_login: boolean;
  requires_subscription: boolean;
}

export interface DownloadLink {
  url: string;
  expires_in: number;
}

export interface Plan {
  id: string;
  name: string;
  tier: "weekly" | "monthly" | "quarterly" | "yearly";
  price: number;
  duration_days: number;
  is_available: boolean;
  features: string[];
  is_featured: boolean;
  sort_order: number;
  description?: string;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan: Plan;
  status: "active" | "expired" | "canceled" | "grace_period";
  auto_renew: boolean;
  current_period_start: string;
  current_period_end: string;
  grace_period_end: string | null;
  has_access: boolean;
}

export interface CheckoutResponse {
  success: boolean;
  message: string;
  checkout_request_id: string;
  merchant_request_id: string;
  amount: number;
}

export interface PaymentStatus {
  checkout_request_id: string;
  status: "pending" | "completed" | "failed" | "refunded";
  amount: number;
  mpesa_receipt_number: string | null;
  failure_reason: string | null;
}

export interface Payment {
  id: string;
  amount: string;
  currency: string;
  gateway: "mpesa" | "card" | "bank" | "free";
  status: "pending" | "success" | "failed" | "refunded" | "cancelled";
  reference: string;
  transaction_id: string;
  phone_number: string;
  paid_at: string | null;
  created_at: string;
}

export interface Review {
  id: string;
  user_name: string;
  resource: string;
  rating: 1 | 2 | 3 | 4 | 5;
  comment: string;
  is_approved: boolean;
  created_at: string;
}

export interface Notification {
  id: string;
  notification_type: string;
  channel: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  is_read: boolean;
  sent_at: string | null;
  read_at: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  total_pages: number;
  current_page: number;
  results: T[];
}

/** Backend error envelope. */
export interface ApiError {
  success: false;
  error: string;
  detail?: unknown;
}

// Admin types
export interface AdminUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  role: UserRole;
  is_verified: boolean;
  is_active: boolean;
  approval_status?: ApprovalStatus;
  last_login_at?: string | null;
  date_joined: string;
  profile: Profile | null;
}

export interface SystemSettings {
  maintenance_mode: boolean;
  daily_free_download_limit: number;
  allowed_upload_extensions: string[];
  grace_period_duration_days: number;
  mpesa_fallback_routing_active: boolean;
  mpesa_configured?: boolean;
  storage_configured?: boolean;
  last_recalculation_timestamp: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface AccountApplication extends User {
  approval_status: ApprovalStatus;
  reviewed_at: string | null;
  reviewed_by_id: string | null;
  review_note: string | null;
}

export interface ApplicationCounts {
  total: number;
  by_role: Partial<Record<UserRole, number>>;
}

export type ActivityCategory =
  | "auth"
  | "account"
  | "approval"
  | "admin"
  | "payment"
  | "download"
  | "content"
  | "request";

export interface ActivityEntry {
  id: string;
  occurred_at: string;
  actor_id: string | null;
  actor_email: string | null;
  actor_name: string | null;
  actor_role: string | null;
  category: ActivityCategory;
  action: string;
  summary: string;
  target_type: string | null;
  target_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string | null;
  request_id: string | null;
  http_method: string | null;
  path: string | null;
  status_code: number | null;
}

export interface ActivitySummary {
  window_hours: number;
  total_events: number;
  by_category: Partial<Record<ActivityCategory, number>>;
  failed_logins: number;
  active_users: number;
  pending_approvals: number;
}

export interface School {
  id: string;
  name: string;
  registration_code: string;
  address: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Transaction {
  id: string;
  amount: number;
  phone_number: string;
  status: string;
  checkout_request_id: string;
  mpesa_receipt_number: string | null;
  failure_reason?: string | null;
  plan_id?: string | null;
  created_at: string;
}

export interface AdminResourceRow {
  id: string;
  title: string;
  slug: string;
  type_variant: string;
  grade: string;
  subject: string;
  term: number;
  year: number;
  is_premium: boolean;
  status: "published" | "draft" | "archived";
  views_count: number;
  downloads_count: number;
  created_at: string;
  published_at: string | null;
}

export interface AdminSubscriptionRow {
  id: string;
  user_id: string;
  user_email: string;
  user_name: string | null;
  plan_name: string;
  status: "active" | "canceled" | "grace_period" | "expired";
  auto_renew: boolean;
  current_period_start: string;
  current_period_end: string;
  is_current: boolean;
}

export interface ModerationReview {
  id: string;
  resource_id: string;
  rating: number;
  comment: string | null;
  moderation_status: "pending" | "approved" | "rejected";
  is_reported: boolean;
  created_at: string;
  updated_at: string;
  user: { id: string; full_name: string; avatar_url: string | null };
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  tier: string;
  price: number;
  duration_days: number;
  is_available: boolean;
  description?: string;
  features?: string[];
  is_featured: boolean;
  sort_order: number;
}

export interface UserSubscription {
  id: string;
  user_id: string;
  plan: SubscriptionPlan;
  status: string;
  auto_renew: boolean;
  current_period_start: string;
  current_period_end: string;
  grace_period_end: string | null;
  created_at: string;
}

export interface BulkActionRequest {
  target_ids: string[];
  action: "archive" | "publish" | "purge" | "approve" | "reject";
}

export interface DashboardStats {
  total_users: number;
  active_subscriptions: number;
  total_revenue: number;
  pending_reviews: number;
  total_resources: number;
  total_schools: number;
}

/** A resource a teacher submitted through the staff workspace. */
export interface TeacherSubmission {
  id: string;
  title: string;
  description: string | null;
  category: string;
  file_extension: string;
  is_free: boolean;
  price: number;
  requires_subscription: boolean;
  visibility: string;
  approval_state: "draft" | "pending_review" | "approved" | "rejected" | "published" | string;
  owner_id: string;
  created_at: string;
}
