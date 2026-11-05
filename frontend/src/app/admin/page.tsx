import AdminLayout from "@/components/admin/AdminLayout";
import { Suspense } from "react";
import { AdminStats } from "./AdminStats";
import { AdminUsersTable } from "./AdminUsersTable";
import { AdminResourcesTable } from "./AdminResourcesTable";
import { AdminFinancialTable } from "./AdminFinancialTable";
import { AdminQuickActions } from "./AdminQuickActions";

export const metadata = {
  title: "Admin Panel — EduCore",
  description: "Administrative management dashboard.",
};

export default function AdminDashboardPage() {
  return (
    <AdminLayout title="Dashboard Overview">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
          <p className="text-gray-500 text-sm">Platform health, user activity, and resource metrics.</p>
        </div>
        <Suspense fallback={<div className="text-gray-500">Loading stats...</div>}>
          <AdminStats />
        </Suspense>
        <div className="grid lg:grid-cols-2 gap-6">
          <Suspense fallback={<div className="text-gray-500">Loading users...</div>}>
            <AdminUsersTable />
          </Suspense>
          <Suspense fallback={<div className="text-gray-500">Loading resources...</div>}>
            <AdminResourcesTable />
          </Suspense>
        </div>
        <Suspense fallback={<div className="text-gray-500">Loading financials...</div>}>
          <AdminFinancialTable />
        </Suspense>
        <AdminQuickActions />
      </div>
    </AdminLayout>
  );
}
