"use client";

import Link from "next/link";
import { Users, BookOpen, Star, DollarSign, School, Settings, UserCheck } from "lucide-react";

const adminActions = [
  { href: "/admin/approvals", label: "Approve Teachers", desc: "Review teacher sign-ups waiting for approval.", icon: UserCheck },
  { href: "/admin/users", label: "Manage Users", desc: "Search, update, and manage user accounts.", icon: Users },
  { href: "/admin/resources", label: "Manage Resources", desc: "Bulk publish, archive, or delete resources.", icon: BookOpen },
  { href: "/admin/reviews", label: "Moderate Reviews", desc: "Approve or reject pending resource reviews.", icon: Star },
  { href: "/admin/financial", label: "Financial Overview", desc: "Transactions, subscriptions, and revenue.", icon: DollarSign },
  { href: "/admin/schools", label: "Institutions", desc: "View and manage registered schools.", icon: School },
  { href: "/admin/settings", label: "System Settings", desc: "Maintenance mode, limits, and upload extensions.", icon: Settings },
];

export function AdminQuickActions() {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {adminActions.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className="flex items-start gap-3 bg-gray-50 hover:bg-primary-50 hover:text-primary-700 rounded-lg px-4 py-3 text-sm font-medium text-gray-700 transition-colors"
          >
            <action.icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">{action.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{action.desc}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
