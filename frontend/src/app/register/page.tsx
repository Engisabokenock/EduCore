"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ArrowRight, GraduationCap, Heart, Loader2 } from "lucide-react";
import { authService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AuthShell, FieldError, authButton, authInput, authLabel } from "@/components/auth/AuthShell";
import { PasswordInput } from "@/components/auth/PasswordInput";

const schema = z
  .object({
    first_name: z.string().min(2, "First name is required"),
    last_name: z.string().min(2, "Last name is required"),
    email: z.string().email("Enter a valid email"),
    phone: z.string().optional(),
    role: z.enum(["student", "parent"]),
    password: z.string().min(8, "Password must be at least 8 characters"),
    password_confirm: z.string(),
  })
  .refine((d) => d.password === d.password_confirm, {
    message: "Passwords do not match",
    path: ["password_confirm"],
  });

type FormData = z.infer<typeof schema>;

const ROLES = [
  { value: "student", label: "Learner", hint: "I want to revise", icon: GraduationCap },
  { value: "parent", label: "Parent", hint: "I support my child", icon: Heart },
] as const;

export default function RegisterPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: "student" },
  });
  const role = watch("role");

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const res = await authService.register(data);
      if (!res.data.tokens) throw new Error(res.data.message ?? "Registration failed. Please try again.");
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
    <AuthShell
      title="Create your free account"
      subtitle="Takes less than a minute. No card needed."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="font-bold text-primary-700 hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        <fieldset>
          <legend className={authLabel}>I am a</legend>
          <div className="grid grid-cols-2 gap-3">
            {ROLES.map(({ value, label, hint, icon: Icon }) => {
              const active = role === value;
              return (
                <label
                  key={value}
                  className={`flex cursor-pointer items-center gap-3 rounded-xl border-2 p-3.5 transition ${
                    active ? "border-primary-600 bg-primary-50 shadow-sm" : "border-gray-200 bg-white hover:border-gray-300"
                  }`}
                >
                  <input type="radio" value={value} {...register("role")} className="sr-only" />
                  <span
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                      active ? "bg-primary-600 text-white" : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                  </span>
                  <span>
                    <span className={`block text-sm font-bold ${active ? "text-primary-800" : "text-gray-900"}`}>{label}</span>
                    <span className="block text-xs text-gray-500">{hint}</span>
                  </span>
                </label>
              );
            })}
          </div>
        </fieldset>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="first_name" className={authLabel}>
              First name
            </label>
            <input id="first_name" {...register("first_name")} autoComplete="given-name" className={authInput} placeholder="Amina" />
            <FieldError message={errors.first_name?.message} />
          </div>
          <div>
            <label htmlFor="last_name" className={authLabel}>
              Last name
            </label>
            <input id="last_name" {...register("last_name")} autoComplete="family-name" className={authInput} placeholder="Wanjiku" />
            <FieldError message={errors.last_name?.message} />
          </div>
        </div>

        <div>
          <label htmlFor="email" className={authLabel}>
            Email address
          </label>
          <input id="email" {...register("email")} type="email" autoComplete="email" className={authInput} placeholder="you@example.com" />
          <FieldError message={errors.email?.message} />
        </div>

        <div className="grid gap-5 sm:grid-cols-2 sm:gap-3">
          <div>
            <label htmlFor="password" className={authLabel}>
              Password
            </label>
            <PasswordInput id="password" {...register("password")} autoComplete="new-password" placeholder="Min. 8 characters" />
            <FieldError message={errors.password?.message} />
          </div>
          <div>
            <label htmlFor="password_confirm" className={authLabel}>
              Confirm password
            </label>
            <PasswordInput id="password_confirm" {...register("password_confirm")} autoComplete="new-password" placeholder="Repeat it" />
            <FieldError message={errors.password_confirm?.message} />
          </div>
        </div>

        <button type="submit" disabled={loading} className={authButton}>
          {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
          {loading ? "Creating account..." : "Create free account"}
          {!loading && <ArrowRight className="h-5 w-5" />}
        </button>

        <p className="text-center text-xs leading-relaxed text-gray-400">
          By signing up you agree to our{" "}
          <Link href="/terms" className="underline hover:text-gray-600">
            Terms
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="underline hover:text-gray-600">
            Privacy Policy
          </Link>
          .
        </p>
      </form>
    </AuthShell>
  );
}
