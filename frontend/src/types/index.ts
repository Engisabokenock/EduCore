/**
 * All TypeScript interfaces for the EduCore API.
 */

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  role: "admin" | "teacher" | "student" | "parent";
  is_verified: boolean;
  date_joined: string;
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
  topics?: Topic[];
}

export interface Topic {
  id: string;
  name: string;
  slug: string;
  description: string;
  order: number;
  is_active: boolean;
}

export interface Resource {
  id: string;
  title: string;
  slug: string;
  description: string;
  resource_type: "notes" | "past_paper" | "worksheet" | "revision" | "video" | "audio" | "ebook";
  is_premium: boolean;
  grade: Grade | null;
  subject: Subject | null;
  topic: Topic | null;
  thumbnail: string | null;
  file_type: string;
  file_size: number;
  year: number | null;
  term: 1 | 2 | 3 | null;
  tags: string[];
  view_count: number;
  download_count: number;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
  file?: string;
  external_url?: string;
  can_access?: boolean;
}

export interface Plan {
  id: string;
  name: string;
  slug: string;
  description: string;
  price: string;
  billing_cycle: "monthly" | "annual" | "lifetime";
  features: string[];
  is_featured: boolean;
  sort_order: number;
}

export interface Subscription {
  id: string;
  plan: Plan;
  status: "active" | "expired" | "cancelled" | "pending";
  started_at: string | null;
  expires_at: string | null;
  auto_renew: boolean;
  is_active: boolean;
  created_at: string;
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

export interface ApiError {
  error: boolean;
  status_code: number;
  detail: Record<string, string[]> | string;
  message: string;
}
