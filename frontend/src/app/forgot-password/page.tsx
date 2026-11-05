"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, MailCheck } from "lucide-react";
import { PublicShell } from "@/components/layout/PublicShell";
import { authService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";

const schema = z.object({ email: z.string().email("Enter a valid email") });
type FormData = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  return (
    <PublicShell>
      <Suspense>
        <ForgotPasswordForm />
      </Suspense>
    </PublicShell>
  );
}

function ForgotPasswordForm() {
  const params = useSearchParams();
  const backTo = params.get("portal") === "staff" ? "/staff/login" : "/login";
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async ({ email }: FormData) => {
    setLoading(true);
    try {
      await authService.forgotPassword(email);
      setSentTo(email);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not send the reset link. Please try again."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
        {sentTo ? (
          <div className="space-y-4 text-center">
            <MailCheck className="mx-auto h-10 w-10 text-green-600" />
            <h1 className="text-xl font-bold text-gray-900">Check your e-mail</h1>
            <p className="text-sm text-gray-600">
              If an account exists for <span className="font-medium">{sentTo}</span>, we have sent a link to reset your
              password. It expires soon, so use it shortly.
            </p>
            <Link href={backTo} className="inline-block text-sm font-medium text-primary-600 hover:underline">
              Back to sign in
            </Link>
          </div>
        ) : (
          <>
            <h1 className="text-xl font-bold text-gray-900">Reset your password</h1>
            <p className="mt-1 text-sm text-gray-500">Enter your account e-mail and we will send you a reset link.</p>
            <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-gray-700">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register("email")}
                  className="w-full rounded-lg border border-gray-200 px-3.5 py-2.5 text-sm outline-none focus:border-transparent focus:ring-2 focus:ring-primary-500"
                />
                {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
              </div>
              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 py-2.5 font-semibold text-white hover:bg-primary-700 disabled:opacity-60"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                Send reset link
              </button>
            </form>
            <p className="mt-6 text-center text-sm text-gray-500">
              Remembered it?{" "}
              <Link href={backTo} className="font-medium text-primary-600 hover:underline">
                Sign in
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
