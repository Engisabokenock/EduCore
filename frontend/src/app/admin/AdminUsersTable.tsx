"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/services/admin-api";
import { Users } from "lucide-react";
import Link from "next/link";

export function AdminUsersTable() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => adminApi.searchUsers({ page: 1, page_size: 5 }),
  });

  const users = data?.data ?? [];

  return (
    <div className="bg-white rounded-xl border border-gray-100">
      <div className="flex items-center justify-between p-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">Recent Users</h3>
        </div>
        <Link href="/admin/users" className="text-sm text-blue-600 hover:underline">
          View all
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
          {users.map((user) => (
            <div key={user.id} className="px-5 py-3 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">{user.full_name}</p>
                <p className="text-xs text-gray-500">{user.email}</p>
              </div>
              <span className="text-xs font-medium px-2 py-1 rounded-full bg-gray-100 text-gray-700">
                {user.role}
              </span>
            </div>
          ))}
          {users.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-gray-500">No users found.</div>
          )}
        </div>
      )}
    </div>
  );
}
