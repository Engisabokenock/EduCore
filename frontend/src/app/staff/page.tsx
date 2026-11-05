"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { homeFor, isStaffRole } from "@/lib/portal";

/** Staff landing: sends a signed-in staff member to their home, everyone else to sign in. */
export default function StaffHomeRedirect() {
  const router = useRouter();
  const { user, isAuthenticated, fetchMe } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/staff/login");
      return;
    }
    if (!user) {
      fetchMe();
      return;
    }
    router.replace(isStaffRole(user.role) ? homeFor(user.role) : "/dashboard");
  }, [isAuthenticated, user, router, fetchMe]);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
    </div>
  );
}
