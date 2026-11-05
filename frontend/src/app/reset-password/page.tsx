"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { PublicShell } from "@/components/layout/PublicShell";
import { authService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";

const schema = z
  .object({
    password: z.string().min(8, "Password must be at least 8 characters"),
    password_confirm: z.string(),
  })
  .refine((d) => d.password === d.password_confirm, { message: "Passwords do not match", path: ["password_confirm"] });
type FormData = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  return (
    <PublicShell>
      <Suspense>
        <ResetPasswordForm />
      </Suspense>
    </PublicShell>
  );
}

function ResetPasswordForm() {
  const token = useSearchParams().get("token");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      await authService.resetPassword(token, data.password, data.password_confirm);
      setDone(true);
    } catch (err) {
      setError(getApiErrorMessage(err, "This reset link is invalid or has expired."));
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-lg border border-gray-200 px-3.5 py-2.5 text-sm outline-none focus:border-transparent focus:ring-2 focus:ring-primary-500";

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
        {!token ? (
          <Result
            ok={false}
            title="Reset link missing"
            body="Open the link from your e-mail again, or request a new one."
            action={{ href: "/forgot-password", label: "Request a new link" }}
          />
        ) : done ? (
          <Result
            ok
            title="Password updated"
            body="Your password has been changed and you have been signed out everywhere else. Sign in with your new password."
            action={{ href: "/login", label: "Go to sign in" }}
          />
        ) : (
          <>
            <h1 className="text-xl font-bold text-gray-900">Choose a new password</h1>
            <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">New password</label>
                <input type="password" autoComplete="new-password" {...register("password")} className={inputClass} />
                {errors.password && <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>}
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">Confirm new password</label>
                <input type="password" autoComplete="new-password" {...register("password_confirm")} className={inputClass} />
                {errors.password_confirm && <p className="mt-1 text-xs text-red-500">{errors.password_confirm.message}</p>}
              </div>
              {error && (
                <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
                  {error}{" "}
                  <Link href="/forgot-password" className="font-medium underline">
                    Request a new link
                  </Link>
                </p>
              )}
              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 py-2.5 font-semibold text-white hover:bg-primary-700 disabled:opacity-60"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                Update password
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

function Result({ ok, title, body, action }: { ok: boolean; title: string; body: string; action: { href: string; label: string } }) {
  return (
    <div className="space-y-4 text-center">
      {ok ? <CheckCircle2 className="mx-auto h-10 w-10 text-green-600" /> : <XCircle className="mx-auto h-10 w-10 text-red-500" />}
      <h1 className="text-xl font-bold text-gray-900">{title}</h1>
      <p className="text-sm text-gray-600">{body}</p>
      <Link href={action.href} className="inline-block text-sm font-medium text-primary-600 hover:underline">
        {action.label}
      </Link>
    </div>
  );
}
