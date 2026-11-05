"use client";

import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, RefreshCw, Search, UserCheck, Users } from "lucide-react";
import AdminLayout from "@/components/admin/AdminLayout";
import { adminApi } from "@/services/admin-api";
import { getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ActivityCategory, ActivityEntry } from "@/types";

const CATEGORIES: { value: ActivityCategory | ""; label: string }[] = [
  { value: "", label: "All activity" },
  { value: "auth", label: "Sign-ins" },
  { value: "account", label: "Accounts" },
  { value: "approval", label: "Approvals" },
  { value: "admin", label: "Staff actions" },
  { value: "payment", label: "Payments" },
  { value: "download", label: "Downloads" },
  { value: "content", label: "Content" },
  { value: "request", label: "Other changes" },
];

const CATEGORY_STYLE: Record<string, string> = {
  auth: "bg-blue-50 text-blue-700",
  account: "bg-indigo-50 text-indigo-700",
  approval: "bg-amber-50 text-amber-700",
  admin: "bg-red-50 text-red-700",
  payment: "bg-green-50 text-green-700",
  download: "bg-teal-50 text-teal-700",
  content: "bg-purple-50 text-purple-700",
  request: "bg-gray-100 text-gray-700",
};

const PAGE_SIZE = 50;

export default function ActivityLogPage() {
  return (
    <AdminLayout title="Activity Log" roles={["super_admin"]}>
      <ActivityMonitor />
    </AdminLayout>
  );
}

function ActivityMonitor() {
  const [category, setCategory] = useState<ActivityCategory | "">("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<string | null>(null);

  // Debounce free-text search so typing does not fire a request per keystroke.
  useEffect(() => {
    const handle = setTimeout(() => {
      setSearch(searchInput.trim().length >= 2 ? searchInput.trim() : "");
      setPage(1);
    }, 350);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const summary = useQuery({
    queryKey: ["admin-activity-summary"],
    queryFn: () => adminApi.getActivitySummary(24).then((r) => r.data),
    refetchInterval: 60_000,
  });

  const activity = useQuery({
    queryKey: ["admin-activity", category, search, page],
    queryFn: () =>
      adminApi
        .getActivity({ category: category || undefined, search: search || undefined, page, page_size: PAGE_SIZE })
        .then((r) => r.data),
    placeholderData: keepPreviousData,
    refetchInterval: page === 1 ? 30_000 : false,
  });

  const totalPages = Math.max(1, Math.ceil((activity.data?.total ?? 0) / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Platform activity</h2>
          <p className="text-sm text-gray-500">
            Every sign-in, approval, staff action, payment, download and data change across EduCore.
          </p>
        </div>
        <button
          onClick={() => {
            summary.refetch();
            activity.refetch();
          }}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
        >
          <RefreshCw className={cn("h-4 w-4", activity.isFetching && "animate-spin")} />
          Refresh
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard icon={Activity} label="Events (24h)" value={summary.data?.total_events} />
        <SummaryCard icon={Users} label="Active users (24h)" value={summary.data?.active_users} />
        <SummaryCard
          icon={AlertTriangle}
          label="Failed sign-ins (24h)"
          value={summary.data?.failed_logins}
          tone={summary.data && summary.data.failed_logins > 0 ? "warn" : undefined}
        />
        <SummaryCard
          icon={UserCheck}
          label="Pending approvals"
          value={summary.data?.pending_approvals}
          tone={summary.data && summary.data.pending_approvals > 0 ? "warn" : undefined}
        />
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <select
          value={category}
          onChange={(e) => {
            setCategory(e.target.value as ActivityCategory | "");
            setPage(1);
          }}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm"
          aria-label="Filter by category"
        >
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
              {c.value && summary.data?.by_category[c.value] ? ` (${summary.data.by_category[c.value]})` : ""}
            </option>
          ))}
        </select>
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by e-mail, IP address or description"
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-100 bg-white">
        {activity.isLoading ? (
          <div className="space-y-3 p-5">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
            ))}
          </div>
        ) : activity.isError ? (
          <p className="p-8 text-center text-sm text-red-600">
            {getApiErrorMessage(activity.error, "Could not load activity.")}
          </p>
        ) : activity.data && activity.data.items.length > 0 ? (
          <ul className="divide-y divide-gray-50">
            {activity.data.items.map((entry) => (
              <ActivityRow
                key={entry.id}
                entry={entry}
                open={expanded === entry.id}
                onToggle={() => setExpanded(expanded === entry.id ? null : entry.id)}
              />
            ))}
          </ul>
        ) : (
          <p className="px-5 py-12 text-center text-sm text-gray-500">No activity matches these filters.</p>
        )}
      </div>

      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>{activity.data ? `${activity.data.total.toLocaleString()} events` : ""}</span>
        <div className="flex items-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 disabled:opacity-40"
          >
            Newer
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 disabled:opacity-40"
          >
            Older
          </button>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: React.ElementType;
  label: string;
  value?: number;
  tone?: "warn";
}) {
  return (
    <div className={cn("rounded-xl border bg-white p-5", tone === "warn" ? "border-amber-200" : "border-gray-100")}>
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Icon className="h-4 w-4" />
        {label}
      </div>
      <p className={cn("mt-1 text-2xl font-bold", tone === "warn" ? "text-amber-600" : "text-gray-900")}>
        {value?.toLocaleString() ?? "–"}
      </p>
    </div>
  );
}

function ActivityRow({ entry, open, onToggle }: { entry: ActivityEntry; open: boolean; onToggle: () => void }) {
  const actor = entry.actor_name || entry.actor_email || (entry.actor_id ? "Signed-in user" : "Guest / system");
  return (
    <li>
      <button onClick={onToggle} className="flex w-full items-start gap-3 px-5 py-3 text-left hover:bg-gray-50">
        <span
          className={cn(
            "mt-0.5 shrink-0 rounded-full px-2 py-0.5 text-xs font-medium",
            CATEGORY_STYLE[entry.category] ?? CATEGORY_STYLE.request
          )}
        >
          {entry.category}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-gray-900">{entry.summary}</p>
          <p className="truncate text-xs text-gray-500">
            {actor}
            {entry.actor_role ? ` · ${entry.actor_role}` : ""}
            {entry.ip_address ? ` · ${entry.ip_address}` : ""}
          </p>
        </div>
        <time className="shrink-0 text-xs text-gray-400" dateTime={entry.occurred_at}>
          {new Date(entry.occurred_at).toLocaleString()}
        </time>
      </button>
      {open && (
        <dl className="grid gap-x-6 gap-y-1 bg-gray-50 px-5 py-3 text-xs text-gray-600 sm:grid-cols-2">
          <Detail label="Action" value={entry.action} />
          <Detail label="Request" value={entry.http_method && entry.path ? `${entry.http_method} ${entry.path}` : null} />
          <Detail label="Status" value={entry.status_code?.toString()} />
          <Detail label="Target" value={entry.target_type ? `${entry.target_type} ${entry.target_id ?? ""}` : null} />
          <Detail label="Request ID" value={entry.request_id} />
          <Detail label="Device" value={entry.user_agent} />
          {Object.keys(entry.details).length > 0 && (
            <div className="sm:col-span-2">
              <dt className="font-medium text-gray-500">Details</dt>
              <dd>
                <pre className="mt-1 overflow-x-auto rounded bg-white p-2 text-[11px] text-gray-700">
                  {JSON.stringify(entry.details, null, 2)}
                </pre>
              </dd>
            </div>
          )}
        </dl>
      )}
    </li>
  );
}

function Detail({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex gap-2">
      <dt className="shrink-0 font-medium text-gray-500">{label}</dt>
      <dd className="truncate">{value}</dd>
    </div>
  );
}
