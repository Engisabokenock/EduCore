"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Bell, FileText, Loader2, LogOut, ShieldCheck } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { notificationService, teacherService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";
import { homeFor } from "@/lib/portal";
import { cn } from "@/lib/utils";
import type { TeacherSubmission } from "@/types";

const TEACHER_ROLES = ["teacher", "school_admin"];

const STATE_STYLE: Record<string, { label: string; className: string }> = {
  draft: { label: "Draft", className: "bg-gray-100 text-gray-700" },
  pending_review: { label: "Awaiting review", className: "bg-amber-50 text-amber-700" },
  approved: { label: "Approved", className: "bg-blue-50 text-blue-700" },
  published: { label: "Published", className: "bg-green-50 text-green-700" },
  rejected: { label: "Rejected", className: "bg-red-50 text-red-700" },
};

export default function TeacherWorkspacePage() {
  const router = useRouter();
  const { user, isAuthenticated, fetchMe, logout } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/staff/login?redirect=/teacher");
      return;
    }
    fetchMe();
  }, [isAuthenticated, router, fetchMe]);

  const isTeacher = !!user && TEACHER_ROLES.includes(user.role);
  useEffect(() => {
    if (user && !isTeacher) router.replace(homeFor(user.role));
  }, [user, isTeacher, router]);

  const submissions = useQuery({
    queryKey: ["teacher-submissions"],
    queryFn: () => teacherService.getMySubmissions().then((r) => r.data),
    enabled: isTeacher,
  });

  const unread = useQuery({
    queryKey: ["unread-count"],
    queryFn: () => notificationService.getUnreadCount(),
    enabled: isTeacher,
    refetchInterval: 60_000,
  });

  if (!isTeacher) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  const items = submissions.data ?? [];
  const count = (state: string) => items.filter((s) => s.approval_state === state).length;
  const unreadCount = unread.data?.data.unread_count ?? 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-slate-950 text-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2 font-bold">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            EduCore Staff
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="hidden text-slate-300 sm:inline">{user.full_name || user.email}</span>
            <span className="relative inline-flex items-center text-slate-300" title="Unread notifications">
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute -right-2 -top-2 rounded-full bg-emerald-500 px-1.5 text-[10px] font-semibold text-white">
                  {unreadCount}
                </span>
              )}
            </span>
            <button
              onClick={async () => {
                await logout();
                router.push("/staff/login");
              }}
              className="inline-flex items-center gap-1 text-slate-300 hover:text-white"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome, {user.first_name || "teacher"}
          </h1>
          <p className="text-sm text-gray-500">
            Track the resources you have submitted and their review status.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-4">
          <Stat label="Submitted" value={items.length} />
          <Stat label="Awaiting review" value={count("pending_review")} />
          <Stat label="Published" value={count("published") + count("approved")} />
          <Stat label="Rejected" value={count("rejected")} />
        </div>

        <section className="rounded-xl border border-gray-100 bg-white">
          <div className="border-b border-gray-100 p-5">
            <h2 className="font-semibold text-gray-900">My submissions</h2>
          </div>
          {submissions.isLoading ? (
            <div className="space-y-3 p-5">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 animate-pulse rounded bg-gray-100" />
              ))}
            </div>
          ) : submissions.isError ? (
            <p className="p-8 text-center text-sm text-red-600">
              {getApiErrorMessage(submissions.error, "Could not load your submissions.")}
            </p>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-5 py-12 text-center">
              <FileText className="h-8 w-8 text-gray-300" />
              <p className="text-sm text-gray-500">You have not submitted any resources yet.</p>
            </div>
          ) : (
            <ul className="divide-y divide-gray-50">
              {items.map((item) => (
                <SubmissionRow key={item.id} item={item} />
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-white p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function SubmissionRow({ item }: { item: TeacherSubmission }) {
  const state = STATE_STYLE[item.approval_state] ?? { label: item.approval_state, className: "bg-gray-100 text-gray-700" };
  return (
    <li className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
      <div className="min-w-0">
        <p className="truncate font-medium text-gray-900">{item.title}</p>
        <p className="text-xs text-gray-500">
          {item.category.replace(/_/g, " ")} · {item.file_extension.toUpperCase()} · Submitted{" "}
          {new Date(item.created_at).toLocaleDateString()}
        </p>
      </div>
      <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", state.className)}>{state.label}</span>
    </li>
  );
}
