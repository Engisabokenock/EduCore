"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ArrowRight, Loader2 } from "lucide-react";
import { authService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { safeRedirect } from "@/lib/portal";
import { AuthShell, FieldError, authButton, authInput, authLabel } from "@/components/auth/AuthShell";
import { PasswordInput } from "@/components/auth/PasswordInput";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

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
    <AuthShell
      title="Welcome back"
      subtitle="Log in to your learner or parent account."
      panelTitle="Good to see you again."
      footer={
        <>
          New to EduCore?{" "}
          <Link href="/register" className="font-bold text-primary-700 hover:underline">
            Create a free account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        <div>
          <label htmlFor="email" className={authLabel}>
            Email address
          </label>
          <input
            id="email"
            {...register("email")}
            type="email"
            autoComplete="email"
            className={authInput}
            placeholder="you@example.com"
          />
          <FieldError message={errors.email?.message} />
        </div>

        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label htmlFor="password" className="text-sm font-semibold text-gray-700">
              Password
            </label>
            <Link href="/forgot-password" className="text-xs font-semibold text-primary-700 hover:underline">
              Forgot password?
            </Link>
          </div>
          <PasswordInput id="password" {...register("password")} autoComplete="current-password" placeholder="Your password" />
          <FieldError message={errors.password?.message} />
        </div>

        <button type="submit" disabled={loading} className={authButton}>
          {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
          {loading ? "Signing in..." : "Log in"}
          {!loading && <ArrowRight className="h-5 w-5" />}
        </button>
      </form>
    </AuthShell>
  );
}
