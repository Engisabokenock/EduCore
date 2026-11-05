"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { AdminHeader } from "@/components/admin/AdminHeader";
import { useAuthStore } from "@/store/auth";
import type { UserRole } from "@/types";

const STAFF_ROLES: UserRole[] = ["admin", "super_admin"];

/**
 * Admin shell: sidebar, header and a client-side role gate. The API enforces the same
 * rules; the gate only avoids rendering screens the user cannot use.
 */
export default function AdminLayout({
  children,
  title,
  roles = STAFF_ROLES,
}: {
  children: React.ReactNode;
  title: string;
  roles?: UserRole[];
}) {
  const router = useRouter();
  const { user, isAuthenticated, fetchMe } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login?redirect=/admin");
      return;
    }
    fetchMe();
  }, [isAuthenticated, router, fetchMe]);

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!roles.includes(user.role)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-500">You do not have permission to view this page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <AdminSidebar role={user.role} />
      <div className="flex-1 flex flex-col min-w-0">
        <AdminHeader title={title} />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
