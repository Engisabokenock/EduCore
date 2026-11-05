"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, ShieldCheck } from "lucide-react";
import { authService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { safeRedirect } from "@/lib/portal";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

export default function StaffLoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const res = await authService.staffLogin(data.email, data.password);
      login(res.data.tokens, res.data.user);
      toast.success(`Welcome back, ${res.data.user.first_name || "there"}!`);
      router.push(safeRedirect(new URLSearchParams(window.location.search).get("redirect"), res.data.user.role));
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, "Invalid email or password."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-6">
            <ShieldCheck className="h-8 w-8 text-emerald-400" />
            <span className="text-2xl font-bold text-white">EduCore Staff</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Staff sign-in</h1>
          <p className="text-slate-400 mt-1 text-sm">For teachers, administrators and the platform owner</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
                Work email
              </label>
              <input
                id="email"
                {...register("email")}
                type="email"
                autoComplete="username"
                className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="you@school.ac.ke"
              />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
                Password
              </label>
              <input
                id="password"
                {...register("password")}
                type="password"
                autoComplete="current-password"
                className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="••••••••"
              />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-slate-900 hover:bg-slate-800 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-400 mt-6">
          New teacher or administrator?{" "}
          <Link href="/staff/register" className="text-emerald-400 font-medium hover:underline">
            Apply for a staff account
          </Link>
        </p>
      </div>
    </div>
  );
}
