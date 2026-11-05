"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, Loader2, UserCheck, X } from "lucide-react";
import AdminLayout from "@/components/admin/AdminLayout";
import { adminApi } from "@/services/admin-api";
import { getApiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";
import type { AccountApplication, ApprovalStatus } from "@/types";

type RoleFilter = "all" | "teacher" | "admin";

const STATUS_TABS: { value: ApprovalStatus; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
];

const ROLE_LABEL: Record<string, string> = { teacher: "Teacher", admin: "Administrator" };

export default function ApprovalsPage() {
  return (
    <AdminLayout title="Account Approvals">
      <ApprovalsBoard />
    </AdminLayout>
  );
}

function ApprovalsBoard() {
  const isSuperAdmin = useAuthStore((s) => s.user?.role === "super_admin");
  const [status, setStatus] = useState<ApprovalStatus>("pending");
  const [role, setRole] = useState<RoleFilter>("all");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const counts = useQuery({
    queryKey: ["admin-approval-counts"],
    queryFn: () => adminApi.getApplicationCounts().then((r) => r.data),
  });

  const applications = useQuery({
    queryKey: ["admin-approvals", status, role, page],
    queryFn: () =>
      adminApi
        .getApplications({ status, role: role === "all" ? undefined : role, page, page_size: pageSize })
        .then((r) => r.data),
  });

  const totalPages = Math.max(1, Math.ceil((applications.data?.total ?? 0) / pageSize));

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-bold text-gray-900">Account approvals</h2>
        <p className="text-sm text-gray-500">
          {isSuperAdmin
            ? "Teachers and administrators wait here until reviewed. Only you can approve administrators."
            : "Teachers wait here until an administrator reviews them. Administrator applications go to the Super Admin."}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <CountCard label="Waiting for review" value={counts.data?.total} highlight />
        <CountCard label="Teacher applications" value={counts.data?.by_role.teacher} />
        {isSuperAdmin && <CountCard label="Administrator applications" value={counts.data?.by_role.admin} />}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex rounded-lg border border-gray-200 bg-white p-1">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => {
                setStatus(tab.value);
                setPage(1);
              }}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                status === tab.value ? "bg-gray-900 text-white" : "text-gray-600 hover:bg-gray-100"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
        {isSuperAdmin && (
          <select
            value={role}
            onChange={(e) => {
              setRole(e.target.value as RoleFilter);
              setPage(1);
            }}
            className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm"
            aria-label="Filter by requested role"
          >
            <option value="all">All roles</option>
            <option value="teacher">Teachers</option>
            <option value="admin">Administrators</option>
          </select>
        )}
      </div>

      <div className="rounded-xl border border-gray-100 bg-white">
        {applications.isLoading ? (
          <div className="space-y-3 p-5">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 animate-pulse rounded bg-gray-100" />
            ))}
          </div>
        ) : applications.isError ? (
          <p className="p-8 text-center text-sm text-red-600">
            {getApiErrorMessage(applications.error, "Could not load applications.")}
          </p>
        ) : applications.data && applications.data.items.length > 0 ? (
          <ul className="divide-y divide-gray-50">
            {applications.data.items.map((application) => (
              <ApplicationRow key={application.id} application={application} />
            ))}
          </ul>
        ) : (
          <div className="flex flex-col items-center gap-2 px-5 py-12 text-center">
            <UserCheck className="h-8 w-8 text-gray-300" />
            <p className="text-sm text-gray-500">No {status} applications.</p>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-gray-500">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function CountCard({ label, value, highlight }: { label: string; value?: number; highlight?: boolean }) {
  return (
    <div className={cn("rounded-xl border bg-white p-5", highlight ? "border-amber-200" : "border-gray-100")}>
      <p className="text-sm text-gray-500">{label}</p>
      <p className={cn("mt-1 text-2xl font-bold", highlight ? "text-amber-600" : "text-gray-900")}>
        {value ?? "–"}
      </p>
    </div>
  );
}

function ApplicationRow({ application }: { application: AccountApplication }) {
  const queryClient = useQueryClient();
  const [rejecting, setRejecting] = useState(false);
  const [note, setNote] = useState("");

  const onDone = (message: string) => {
    toast.success(message);
    setRejecting(false);
    setNote("");
    queryClient.invalidateQueries({ queryKey: ["admin-approvals"] });
    queryClient.invalidateQueries({ queryKey: ["admin-approval-counts"] });
  };

  const approve = useMutation({
    mutationFn: () => adminApi.approveApplication(application.id),
    onSuccess: () => onDone(`${application.email} approved.`),
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not approve this application.")),
  });

  const reject = useMutation({
    mutationFn: () => adminApi.rejectApplication(application.id, note.trim() || undefined),
    onSuccess: () => onDone(`${application.email} rejected.`),
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not reject this application.")),
  });

  const busy = approve.isPending || reject.isPending;
  const canApprove = application.approval_status !== "approved";
  const canReject = application.approval_status === "pending";

  return (
    <li className="px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium text-gray-900">{application.full_name || application.email}</p>
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
              {ROLE_LABEL[application.role] ?? application.role}
            </span>
          </div>
          <p className="text-sm text-gray-500">
            {application.email}
            {application.phone ? ` · ${application.phone}` : ""}
          </p>
          <p className="mt-0.5 text-xs text-gray-400">
            Applied {new Date(application.date_joined).toLocaleString()}
            {application.reviewed_at ? ` · Reviewed ${new Date(application.reviewed_at).toLocaleString()}` : ""}
          </p>
          {application.review_note && (
            <p className="mt-1 text-xs text-gray-600">Note: {application.review_note}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {canApprove && (
            <button
              onClick={() => approve.mutate()}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-60"
            >
              {approve.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
              Approve
            </button>
          )}
          {canReject && !rejecting && (
            <button
              onClick={() => setRejecting(true)}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-60"
            >
              <X className="h-4 w-4" />
              Reject
            </button>
          )}
        </div>
      </div>
      {rejecting && (
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={500}
            placeholder="Reason shown to the applicant (optional)"
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-red-200"
          />
          <div className="flex gap-2">
            <button
              onClick={() => reject.mutate()}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60"
            >
              {reject.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Confirm rejection
            </button>
            <button
              onClick={() => setRejecting(false)}
              disabled={busy}
              className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
