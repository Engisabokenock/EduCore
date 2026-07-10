"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  BookOpen,
  DollarSign,
  Settings,
  Shield,
  School,
  Star,
  ChevronLeft,
  Menu,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { UserRole } from "@/types";
import { useState } from "react";

const adminNavItems = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/resources", label: "Resources", icon: BookOpen },
  { href: "/admin/reviews", label: "Reviews", icon: Star },
  { href: "/admin/financial", label: "Financial", icon: DollarSign },
  { href: "/admin/schools", label: "Schools", icon: School },
  { href: "/admin/settings", label: "Settings", icon: Settings },
];

const superAdminNavItems = [
  ...adminNavItems,
  { href: "/admin/super", label: "Super Admin", icon: Shield, exact: true },
  { href: "/admin/audit", label: "Audit Logs", icon: Shield },
];

export function AdminSidebar({ role }: { role: UserRole }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const isSuperAdmin = role === "super_admin";
  const navItems = isSuperAdmin ? superAdminNavItems : adminNavItems;

  const isActive = (href: string, exact?: boolean) => {
    if (exact) return pathname === href;
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={cn(
        "bg-gray-900 text-white transition-all duration-200 flex flex-col",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
        {!collapsed && (
          <Link href="/admin" className="flex items-center gap-2 font-bold text-lg">
            <Shield className="h-5 w-5 text-red-400" />
            <span>{isSuperAdmin ? "Super Admin" : "Admin"}</span>
          </Link>
        )}
        {collapsed && (
          <Link href="/admin" className="mx-auto">
            <Shield className="h-5 w-5 text-red-400" />
          </Link>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-gray-400 hover:text-white hidden md:block"
        >
          {collapsed ? <Menu className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              isActive(item.href, item.exact)
                ? "bg-gray-800 text-white"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            )}
          >
            <item.icon className="h-4 w-4 flex-shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </Link>
        ))}
      </nav>
      <div className="p-2 border-t border-gray-800">
        <Link
          href="/dashboard"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        >
          <ChevronLeft className="h-4 w-4 flex-shrink-0" />
          {!collapsed && <span>Back to Dashboard</span>}
        </Link>
      </div>
    </aside>
  );
}
