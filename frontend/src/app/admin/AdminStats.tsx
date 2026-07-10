"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/services/admin-api";
import { Users, BookOpen, DollarSign, Star, Shield, School } from "lucide-react";

export function AdminStats() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-dashboard-stats"],
    queryFn: () => adminApi.getStats(),
  });

  if (isLoading || !data?.data) {
    return (
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
            <div className="h-8 bg-gray-200 rounded w-1/3" />
          </div>
        ))}
      </div>
    );
  }

  const stats = data.data;
  const items = [
    { label: "Total Users", value: stats.total_users ?? 0, icon: Users, color: "bg-blue-50 text-blue-600" },
    { label: "Active Subscriptions", value: stats.active_subscriptions ?? 0, icon: Star, color: "bg-yellow-50 text-yellow-600" },
    { label: "Total Revenue", value: `KES ${(stats.total_revenue ?? 0).toLocaleString()}`, icon: DollarSign, color: "bg-green-50 text-green-600" },
    { label: "Pending Reviews", value: stats.pending_reviews ?? 0, icon: Shield, color: "bg-orange-50 text-orange-600" },
    { label: "Total Resources", value: stats.total_resources ?? 0, icon: BookOpen, color: "bg-purple-50 text-purple-600" },
    { label: "Schools", value: stats.total_schools ?? 0, icon: School, color: "bg-teal-50 text-teal-600" },
  ];

  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((item) => (
        <div key={item.label} className="bg-white rounded-xl border border-gray-100 p-5 flex items-center gap-4">
          <div className={`rounded-xl p-3 ${item.color}`}>
            <item.icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{item.value}</p>
            <p className="text-sm text-gray-500">{item.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
