"use client";

import AdminLayout from "@/components/admin/AdminLayout";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/services/admin-api";
import { Shield, Users, BookOpen, DollarSign, Star, School, Activity, UserCheck } from "lucide-react";
import Link from "next/link";

const superAdminActions = [
  { href: "/admin/super", label: "Super Dashboard", desc: "Platform-wide metrics and controls.", icon: Shield },
  { href: "/admin/approvals", label: "Approvals", desc: "Approve administrator and teacher sign-ups.", icon: UserCheck },
  { href: "/admin/users", label: "All Users", desc: "Search, update, and manage all user accounts.", icon: Users },
  { href: "/admin/resources", label: "All Resources", desc: "Bulk publish, archive, or delete resources.", icon: BookOpen },
  { href: "/admin/reviews", label: "Moderate Reviews", desc: "Approve or reject pending resource reviews.", icon: Star },
  { href: "/admin/financial", label: "Financial Ledger", desc: "Transactions, subscriptions, and revenue.", icon: DollarSign },
  { href: "/admin/schools", label: "Institutions", desc: "View and manage registered schools.", icon: School },
  { href: "/admin/settings", label: "System Settings", desc: "Maintenance mode, limits, and upload extensions.", icon: Activity },
  { href: "/admin/audit", label: "Activity Log", desc: "Every sign-in, approval, payment and change on the platform.", icon: Activity },
];

export default function SuperAdminPage() {
  return (
    <AdminLayout title="Super Admin Control Plane" roles={["super_admin"]}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Super Admin Control Plane</h2>
          <p className="text-gray-500 text-sm">Full platform oversight, security logs, and privileged operations.</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {superAdminActions.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className={`flex items-start gap-3 bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md transition-shadow ${action.href === "/admin/super" ? "ring-2 ring-red-500" : ""}`}
            >
              <div className="rounded-xl p-2 bg-gray-50 text-gray-700">
                <action.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium text-gray-900">{action.label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{action.desc}</p>
              </div>
            </Link>
          ))}
        </div>
        <SuperAdminLogs />
      </div>
    </AdminLayout>
  );
}

function SuperAdminLogs() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-activity", "", "", 1, "recent"],
    queryFn: () => adminApi.getActivity({ page: 1, page_size: 10 }).then((r) => r.data),
    refetchInterval: 30_000,
  });

  const logs = data?.items ?? [];

  return (
    <div className="bg-white rounded-xl border border-gray-100">
      <div className="flex items-center justify-between p-5 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900">Recent Activity</h3>
        <Link href="/admin/audit" className="text-sm text-blue-600 hover:underline">
          View full activity log
        </Link>
      </div>
      {isLoading ? (
        <div className="p-5 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="divide-y divide-gray-50">
          {logs.map((log) => (
            <div key={log.id} className="px-5 py-3 flex items-center justify-between">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-gray-900">{log.summary}</p>
                <p className="truncate text-xs text-gray-500">
                  {log.actor_email ?? "Guest / system"}
                  {log.ip_address ? ` · ${log.ip_address}` : ""}
                </p>
              </div>
              <span className="ml-3 shrink-0 text-xs text-gray-400">
                {new Date(log.occurred_at).toLocaleString()}
              </span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-gray-500">No activity recorded yet.</div>
          )}
        </div>
      )}
    </div>
  );
}
