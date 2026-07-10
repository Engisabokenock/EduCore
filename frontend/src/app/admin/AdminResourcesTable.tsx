"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/services/admin-api";
import { BookOpen } from "lucide-react";
import Link from "next/link";

export function AdminResourcesTable() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-resources-summary"],
    queryFn: () => adminApi.bulkResourceAction({ target_ids: [], action: "publish" }),
  });

  const result = data?.data;

  return (
    <div className="bg-white rounded-xl border border-gray-100">
      <div className="flex items-center justify-between p-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-purple-600" />
          <h3 className="font-semibold text-gray-900">Resources</h3>
        </div>
        <Link href="/admin/resources" className="text-sm text-blue-600 hover:underline">
          Manage
        </Link>
      </div>
      {isLoading ? (
        <div className="p-5 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="p-5">
          <p className="text-sm text-gray-600">
            Use the <span className="font-medium">Manage</span> link to bulk-archive, publish, or purge resources.
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Last action status: {result?.status ?? "N/A"}
          </p>
        </div>
      )}
    </div>
  );
}
