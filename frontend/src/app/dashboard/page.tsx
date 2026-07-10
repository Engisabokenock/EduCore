"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, Download, Star, Bell, ChevronRight, LogOut } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { contentService, notificationService, commerceService } from "@/services/api-service";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout, fetchMe } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    fetchMe();
  }, [isAuthenticated, router, fetchMe]);

  const { data: downloadsData } = useQuery({
    queryKey: ["my-downloads"],
    queryFn: () => contentService.getMyDownloads(),
    enabled: isAuthenticated,
  });

  const { data: notifData } = useQuery({
    queryKey: ["unread-count"],
    queryFn: () => notificationService.getUnreadCount(),
    enabled: isAuthenticated,
    refetchInterval: 30000,
  });

  const { data: subscriptionData } = useQuery({
    queryKey: ["subscription"],
    queryFn: () => commerceService.getSubscription(),
    enabled: isAuthenticated,
  });

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  if (!user) return null;

  const hasActiveSub = ["active", "grace_period"].includes(subscriptionData?.data?.status);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <BookOpen className="h-6 w-6 text-primary-600" />
              <span className="font-bold text-gray-900">EduCore</span>
            </Link>
            <div className="flex items-center gap-4">
              <button className="relative text-gray-500 hover:text-gray-900">
                <Bell className="h-5 w-5" />
                {!!notifData?.data?.unread_count && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                    {notifData.data.unread_count > 9 ? "9+" : notifData.data.unread_count}
                  </span>
                )}
              </button>
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-gray-900 flex items-center gap-1 text-sm"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden md:inline">Log out</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user.first_name}!
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            {hasActiveSub ? (
              <span className="text-green-600 font-medium">Premium Active</span>
            ) : (
              <>
                Free account &mdash;{" "}
                <Link href="/pricing" className="text-primary-600 hover:underline">
                  Upgrade to Premium
                </Link>
              </>
            )}
          </p>
        </div>

        {/* Stats cards */}
        <div className="grid sm:grid-cols-3 gap-4 mb-8">
          {[
            {
              icon: Download,
              label: "Downloads",
              value: (downloadsData?.data as { count?: number })?.count ?? 0,
              color: "bg-blue-50 text-blue-600",
            },
            {
              icon: Star,
              label: "Plan",
              value: subscriptionData?.data?.plan?.name ?? "Free",
              color: "bg-yellow-50 text-yellow-600",
            },
            {
              icon: Bell,
              label: "Unread",
              value: notifData?.data?.unread_count ?? 0,
              color: "bg-red-50 text-red-600",
            },
          ].map((card) => (
            <div key={card.label} className="bg-white rounded-xl border border-gray-100 p-5 flex items-center gap-4">
              <div className={`rounded-xl p-3 ${card.color}`}>
                <card.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                <p className="text-sm text-gray-500">{card.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Quick links */}
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Quick Access</h2>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
            {[
              { href: "/subjects", label: "Browse Subjects" },
              { href: "/resources", label: "All Resources" },
              { href: "/resources?type=past_paper", label: "Past Papers" },
              { href: "/resources?type=notes", label: "Notes" },
              { href: "/resources?type=worksheet", label: "Worksheets" },
              { href: "/pricing", label: "Upgrade Premium" },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="flex items-center justify-between bg-gray-50 hover:bg-primary-50 hover:text-primary-700 rounded-lg px-4 py-3 text-sm font-medium text-gray-700 transition-colors"
              >
                {link.label}
                <ChevronRight className="h-4 w-4" />
              </Link>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
