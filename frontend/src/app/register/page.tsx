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
  first_name: z.string().min(2, "First name is required"),
  last_name: z.string().min(2, "Last name is required"),
  email: z.string().email("Enter a valid email"),
  phone: z.string().optional(),
  role: z.enum(["student", "teacher", "parent"]),
  password: z.string().min(8, "Password must be at least 8 characters"),
  password_confirm: z.string(),
}).refine((d) => d.password === d.password_confirm, {
  message: "Passwords do not match",
  path: ["password_confirm"],
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: "student" },
  });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const res = await authService.register(data);
      login(res.data.tokens, res.data.user);
      toast.success("Account created! Check your email to verify.");
      const redirect = new URLSearchParams(window.location.search).get("redirect");
      router.push(redirect && redirect.startsWith("/") && !redirect.startsWith("//") ? redirect : "/dashboard");
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, "Registration failed. Please try again."));
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
          <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
          <p className="text-gray-500 mt-1 text-sm">Free to start. No credit card required.</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">First name</label>
                <input
                  {...register("first_name")}
                  className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="John"
                />
                {errors.first_name && <p className="text-red-500 text-xs mt-1">{errors.first_name.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Last name</label>
                <input
                  {...register("last_name")}
                  className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Doe"
                />
                {errors.last_name && <p className="text-red-500 text-xs mt-1">{errors.last_name.message}</p>}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
              <input
                {...register("email")}
                type="email"
                className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="you@example.com"
              />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">I am a</label>
              <select
                {...register("role")}
                className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white"
              >
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
                <option value="parent">Parent</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
              <input
                {...register("password")}
                type="password"
                className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Min. 8 characters"
              />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Confirm password</label>
              <input
                {...register("password_confirm")}
                type="password"
                className="w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="••••••••"
              />
              {errors.password_confirm && <p className="text-red-500 text-xs mt-1">{errors.password_confirm.message}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 mt-2"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-gray-500 mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-primary-600 font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
