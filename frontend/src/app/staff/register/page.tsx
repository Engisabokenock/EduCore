"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Clock, Loader2, ShieldCheck } from "lucide-react";
import { authService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";

const schema = z
  .object({
    first_name: z.string().min(2, "First name is required"),
    last_name: z.string().min(2, "Last name is required"),
    email: z.string().email("Enter a valid email"),
    phone: z.string().optional(),
    role: z.enum(["teacher", "admin"]),
    password: z.string().min(8, "Password must be at least 8 characters"),
    password_confirm: z.string(),
  })
  .refine((d) => d.password === d.password_confirm, {
    message: "Passwords do not match",
    path: ["password_confirm"],
  });

type FormData = z.infer<typeof schema>;

const ROLE_HINTS: Record<FormData["role"], string> = {
  teacher: "An administrator reviews teacher applications.",
  admin: "Only the Super Admin can approve administrator applications.",
};

const inputClass =
  "w-full border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent";

export default function StaffRegisterPage() {
  const [loading, setLoading] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: { role: "teacher" } });
  const role = watch("role");

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const res = await authService.staffRegister(data);
      setPendingMessage(res.data.message ?? "Your application is waiting for approval.");
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, "Could not submit your application. Please try again."));
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
          <h1 className="text-2xl font-bold text-white">Apply for a staff account</h1>
          <p className="text-slate-400 mt-1 text-sm">Your account is activated once it has been approved.</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {pendingMessage ? (
            <div className="text-center space-y-4">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-50">
                <Clock className="h-6 w-6 text-amber-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900">Application submitted</h2>
              <p className="text-sm text-gray-600">{pendingMessage}</p>
              <p className="text-xs text-gray-400">We will e-mail you as soon as it has been reviewed.</p>
              <Link href="/staff/login" className="inline-block text-sm font-medium text-emerald-700 hover:underline">
                Back to staff sign-in
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">First name</label>
                  <input {...register("first_name")} className={inputClass} />
                  {errors.first_name && <p className="text-red-500 text-xs mt-1">{errors.first_name.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Last name</label>
                  <input {...register("last_name")} className={inputClass} />
                  {errors.last_name && <p className="text-red-500 text-xs mt-1">{errors.last_name.message}</p>}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Work email</label>
                <input {...register("email")} type="email" className={inputClass} placeholder="you@school.ac.ke" />
                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Phone (optional)</label>
                <input {...register("phone")} className={inputClass} placeholder="07XX XXX XXX" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">I am applying as</label>
                <select {...register("role")} className={`${inputClass} bg-white`}>
                  <option value="teacher">Teacher</option>
                  <option value="admin">Administrator</option>
                </select>
                <p className="text-xs text-amber-700 mt-1.5">{ROLE_HINTS[role]}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
                <input {...register("password")} type="password" className={inputClass} placeholder="Min. 8 characters" />
                {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Confirm password</label>
                <input {...register("password_confirm")} type="password" className={inputClass} placeholder="••••••••" />
                {errors.password_confirm && (
                  <p className="text-red-500 text-xs mt-1">{errors.password_confirm.message}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-slate-900 hover:bg-slate-800 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 mt-2"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? "Submitting..." : "Submit application"}
              </button>
            </form>
          )}
        </div>

        <p className="text-center text-sm text-slate-400 mt-6">
          Already approved?{" "}
          <Link href="/staff/login" className="text-emerald-400 font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
