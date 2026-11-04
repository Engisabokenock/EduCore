"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { BookOpen, Loader2 } from "lucide-react";
import { authService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

/** Only allow same-site relative redirects (prevents open-redirect phishing). */
function safeRedirect(target: string | null, role: string): string {
  if (target && target.startsWith("/") && !target.startsWith("//")) return target;
  return ["admin", "super_admin"].includes(role) ? "/admin" : "/dashboard";
}

export default function LoginPage() {
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
      const res = await authService.login(data.email, data.password);
      login(res.data.tokens, res.data.user);
      toast.success("Welcome back!");
      router.push(safeRedirect(new URLSearchParams(window.location.search).get("redirect"), res.data.user.role));
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, "Invalid email or password."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <BookOpen className="h-8 w-8 text-primary-600" />
            <span className="text-2xl font-bold text-gray-900">EduCore</span>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Welcome back</h1>
          <p className="text-gray-500 mt-1 text-sm">Log in to your account</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Email address
              </label>
              <input
                {...register("email")}
                type="email"
                autoComplete="email"
                className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="you@example.com"
              />
              {errors.email && (
                <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-gray-700">Password</label>
                <Link href="/forgot-password" className="text-xs text-primary-600 hover:underline">
                  Forgot password?
                </Link>
              </div>
              <input
                {...register("password")}
                type="password"
                autoComplete="current-password"
                className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="••••••••"
              />
              {errors.password && (
                <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-gray-500 mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-primary-600 font-medium hover:underline">
            Sign up free
          </Link>
        </p>
      </div>
    </div>
  );
}
