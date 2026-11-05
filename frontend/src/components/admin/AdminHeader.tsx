"use client";

import { useRouter } from "next/navigation";
import { BookOpen, LogOut } from "lucide-react";
import { useAuthStore } from "@/store/auth";

export function AdminHeader({ title }: { title: string }) {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    router.push("/staff/login");
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <BookOpen className="h-6 w-6 text-red-600" />
        <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">
          {user?.full_name} <span className="text-gray-400">({user?.role})</span>
        </span>
        <button
          onClick={handleLogout}
          className="text-gray-500 hover:text-red-600 flex items-center gap-1 text-sm"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden md:inline">Log out</span>
        </button>
      </div>
    </header>
  );
}
