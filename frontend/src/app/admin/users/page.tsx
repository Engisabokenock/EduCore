"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Search } from "lucide-react";
import AdminLayout from "@/components/admin/AdminLayout";
import { Badge, Card, EmptyState, ErrorState, LoadingRows, PageHeader, Pager, formatDate, inputClass } from "@/components/admin/ui";
import { adminApi } from "@/services/admin-api";
import { getApiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import type { AdminUser, UserRole } from "@/types";

const PAGE_SIZE = 25;

const ROLE_OPTIONS: { value: "" | UserRole; label: string }[] = [
  { value: "", label: "All roles" },
  { value: "student", label: "Students" },
  { value: "parent", label: "Parents" },
  { value: "teacher", label: "Teachers" },
  { value: "admin", label: "Administrators" },
  { value: "super_admin", label: "Super Admin" },
];

// Roles the Super Admin can assign here. The Super Admin role itself is never assignable.
const ASSIGNABLE_ROLES: UserRole[] = ["student", "parent", "teacher", "admin"];

export default function AdminUsersPage() {
  return (
    <AdminLayout title="Users">
      <UsersManager />
    </AdminLayout>
  );
}

function UsersManager() {
  const [role, setRole] = useState<"" | UserRole>("");
  const [active, setActive] = useState<"" | "true" | "false">("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(searchInput.trim().length >= 2 ? searchInput.trim() : "");
      setPage(1);
    }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  const users = useQuery({
    queryKey: ["admin-users", role, active, search, page],
    queryFn: () =>
      adminApi
        .searchUsers({
          role: role || undefined,
          is_active: active === "" ? undefined : active === "true",
          search_term: search || undefined,
          page,
          page_size: PAGE_SIZE,
        })
        .then((r) => r.data),
  });

  const items = users.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="Users" description="Search accounts, deactivate access and manage roles." />

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by name or e-mail"
            className={`${inputClass} w-full pl-9`}
          />
        </div>
        <select
          value={role}
          onChange={(e) => {
            setRole(e.target.value as "" | UserRole);
            setPage(1);
          }}
          className={inputClass}
          aria-label="Filter by role"
        >
          {ROLE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          value={active}
          onChange={(e) => {
            setActive(e.target.value as "" | "true" | "false");
            setPage(1);
          }}
          className={inputClass}
          aria-label="Filter by status"
        >
          <option value="">Any status</option>
          <option value="true">Active</option>
          <option value="false">Deactivated</option>
        </select>
      </div>

      <Card className="overflow-x-auto">
        {users.isLoading ? (
          <LoadingRows />
        ) : users.isError ? (
          <ErrorState error={users.error} fallback="Could not load users." />
        ) : items.length === 0 ? (
          <EmptyState message="No users match these filters." />
        ) : (
          <table className="w-full min-w-[720px] text-sm">
            <thead className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-5 py-3 font-medium">User</th>
                <th className="px-5 py-3 font-medium">Role</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Joined</th>
                <th className="px-5 py-3 font-medium">Last sign-in</th>
                <th className="px-5 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {items.map((user) => (
                <UserRow key={user.id} user={user} />
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Pager page={page} pageSize={PAGE_SIZE} itemsOnPage={items.length} onChange={setPage} />
    </div>
  );
}

function UserRow({ user }: { user: AdminUser }) {
  const queryClient = useQueryClient();
  const me = useAuthStore((s) => s.user);
  const isSuperAdmin = me?.role === "super_admin";
  const isSelf = me?.id === user.id;
  // Mirrors the API: admins cannot manage administrators or the Super Admin.
  const canManage = !isSelf && user.role !== "super_admin" && (isSuperAdmin || user.role !== "admin");

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["admin-users"] });

  const toggleActive = useMutation({
    mutationFn: () => adminApi.updateUser(user.id, { is_active: !user.is_active }),
    onSuccess: () => {
      toast.success(user.is_active ? `${user.email} deactivated.` : `${user.email} reactivated.`);
      refresh();
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not update this account.")),
  });

  const changeRole = useMutation({
    mutationFn: (role: UserRole) => adminApi.overrideUserRole(user.id, { role }),
    onSuccess: (_, role) => {
      toast.success(`${user.email} is now ${role.replace("_", " ")}.`);
      refresh();
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not change the role.")),
  });

  return (
    <tr>
      <td className="px-5 py-3">
        <p className="font-medium text-gray-900">{user.full_name || "—"}</p>
        <p className="text-xs text-gray-500">{user.email}</p>
      </td>
      <td className="px-5 py-3">
        {isSuperAdmin && canManage ? (
          <select
            value={user.role}
            disabled={changeRole.isPending}
            onChange={(e) => changeRole.mutate(e.target.value as UserRole)}
            className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs"
            aria-label={`Role for ${user.email}`}
          >
            {ASSIGNABLE_ROLES.map((r) => (
              <option key={r} value={r}>
                {r.replace("_", " ")}
              </option>
            ))}
          </select>
        ) : (
          <Badge tone={user.role === "super_admin" || user.role === "admin" ? "red" : "gray"}>
            {user.role.replace("_", " ")}
          </Badge>
        )}
      </td>
      <td className="px-5 py-3">
        <div className="flex flex-wrap gap-1">
          <Badge tone={user.is_active ? "green" : "red"}>{user.is_active ? "Active" : "Deactivated"}</Badge>
          {user.approval_status && user.approval_status !== "approved" && (
            <Badge tone="amber">{user.approval_status}</Badge>
          )}
        </div>
      </td>
      <td className="px-5 py-3 text-gray-500">{formatDate(user.date_joined)}</td>
      <td className="px-5 py-3 text-gray-500">{formatDate(user.last_login_at)}</td>
      <td className="px-5 py-3 text-right">
        {canManage && (
          <button
            onClick={() => toggleActive.mutate()}
            disabled={toggleActive.isPending}
            className={
              user.is_active
                ? "rounded-lg border border-red-200 px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                : "rounded-lg border border-green-200 px-3 py-1 text-xs font-medium text-green-700 hover:bg-green-50 disabled:opacity-50"
            }
          >
            {user.is_active ? "Deactivate" : "Reactivate"}
          </button>
        )}
      </td>
    </tr>
  );
}
