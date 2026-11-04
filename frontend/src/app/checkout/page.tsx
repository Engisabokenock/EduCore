"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { BookOpen, CheckCircle2, Loader2, Smartphone, XCircle } from "lucide-react";
import { commerceService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import type { Plan } from "@/types";

const schema = z.object({
  phone_number: z
    .string()
    .trim()
    .regex(/^(?:\+?254|0)?[17]\d{8}$/, "Enter a Safaricom number, e.g. 0712 345 678"),
});
type FormData = z.infer<typeof schema>;

type Stage = "form" | "waiting" | "success" | "failed";

const POLL_INTERVAL_MS = 4000;
const POLL_TIMEOUT_MS = 2 * 60 * 1000;

function CheckoutContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const planId = useSearchParams().get("plan");
  const { user, fetchMe } = useAuthStore();

  const [stage, setStage] = useState<Stage>("form");
  const [checkoutId, setCheckoutId] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState<number>(0);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const { data: plans, isLoading: plansLoading } = useQuery({
    queryKey: ["plans"],
    queryFn: async () => (await commerceService.getPlans()).data,
  });
  const plan: Plan | undefined = plans?.find((p) => p.id === planId);

  const { register, handleSubmit, setValue, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (user?.phone) setValue("phone_number", user.phone);
  }, [user?.phone, setValue]);

  // Poll the payment until M-Pesa confirms, fails, or we time out.
  const { data: status } = useQuery({
    queryKey: ["payment-status", checkoutId],
    queryFn: async () => (await commerceService.getPaymentStatus(checkoutId as string)).data,
    enabled: stage === "waiting" && !!checkoutId,
    refetchInterval: POLL_INTERVAL_MS,
    retry: false,
  });

  useEffect(() => {
    if (stage !== "waiting") return;
    if (status?.status === "completed") {
      setStage("success");
      queryClient.invalidateQueries({ queryKey: ["subscription"] });
      toast.success("Payment received. Premium is now active!");
    } else if (status?.status === "failed") {
      setFailure(status.failure_reason || "The payment was not completed.");
      setStage("failed");
    } else if (startedAt && Date.now() - startedAt > POLL_TIMEOUT_MS) {
      setFailure("We did not receive a confirmation from M-Pesa in time. If you were charged, access will activate automatically within a few minutes.");
      setStage("failed");
    }
  }, [status, stage, startedAt, queryClient]);

  const onSubmit = async ({ phone_number }: FormData) => {
    if (!plan) return;
    try {
      const { data } = await commerceService.initiatePayment(plan.id, phone_number);
      setCheckoutId(data.checkout_request_id);
      setStartedAt(Date.now());
      setFailure(null);
      setStage("waiting");
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not start the M-Pesa payment."));
    }
  };

  if (plansLoading) {
    return <div className="h-64 rounded-2xl bg-gray-100 animate-pulse" />;
  }

  if (!plan) {
    return (
      <div className="text-center bg-white rounded-2xl border border-gray-100 p-8">
        <h1 className="text-xl font-bold text-gray-900 mb-2">Choose a plan first</h1>
        <p className="text-gray-500 mb-6">The selected plan is unavailable.</p>
        <Link href="/pricing" className="text-primary-600 font-semibold hover:underline">View plans</Link>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="p-6 border-b border-gray-50">
        <p className="text-sm text-gray-500">You are buying</p>
        <div className="flex items-baseline justify-between gap-4 mt-1">
          <h1 className="text-xl font-bold text-gray-900">{plan.name}</h1>
          <p className="text-2xl font-extrabold text-gray-900">KES {Number(plan.price).toLocaleString("en-KE")}</p>
        </div>
        <p className="text-sm text-gray-500 mt-1">{plan.duration_days} days of unlimited premium access</p>
      </div>

      <div className="p-6">
        {stage === "form" && (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div>
              <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700 mb-1">
                M-Pesa phone number
              </label>
              <input
                id="phone_number"
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                placeholder="0712 345 678"
                {...register("phone_number")}
                className="w-full rounded-xl border border-gray-200 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {errors.phone_number && <p className="text-sm text-red-600 mt-1">{errors.phone_number.message}</p>}
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin" /> : <Smartphone className="h-5 w-5" />}
              Pay with M-Pesa
            </button>
            <p className="text-xs text-gray-400 text-center">
              You will receive a prompt on your phone. Enter your M-Pesa PIN to confirm.
            </p>
          </form>
        )}

        {stage === "waiting" && (
          <div className="text-center py-6" role="status" aria-live="polite">
            <Loader2 className="h-10 w-10 animate-spin text-green-600 mx-auto mb-4" />
            <h2 className="font-semibold text-gray-900">Check your phone</h2>
            <p className="text-sm text-gray-500 mt-1">Enter your M-Pesa PIN to complete the payment. This page updates automatically.</p>
          </div>
        )}

        {stage === "success" && (
          <div className="text-center py-6" role="status">
            <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <h2 className="font-semibold text-gray-900">Payment successful</h2>
            <p className="text-sm text-gray-500 mt-1">
              {status?.mpesa_receipt_number ? `Receipt ${status.mpesa_receipt_number}. ` : ""}Your premium access is active.
            </p>
            <button
              onClick={() => router.push("/dashboard")}
              className="mt-6 bg-primary-600 hover:bg-primary-700 text-white font-semibold px-6 py-3 rounded-xl"
            >
              Go to dashboard
            </button>
          </div>
        )}

        {stage === "failed" && (
          <div className="text-center py-6" role="alert">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="font-semibold text-gray-900">Payment not completed</h2>
            <p className="text-sm text-gray-500 mt-1">{failure}</p>
            <button
              onClick={() => setStage("form")}
              className="mt-6 bg-primary-600 hover:bg-primary-700 text-white font-semibold px-6 py-3 rounded-xl"
            >
              Try again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-100">
        <div className="max-w-3xl mx-auto px-4 h-16 flex items-center">
          <Link href="/" className="flex items-center gap-2 font-bold text-gray-900">
            <BookOpen className="h-6 w-6 text-primary-600" />
            EduCore
          </Link>
        </div>
      </nav>
      <main className="max-w-md mx-auto px-4 py-10">
        <Suspense fallback={<div className="h-64 rounded-2xl bg-gray-100 animate-pulse" />}>
          <CheckoutContent />
        </Suspense>
      </main>
    </div>
  );
}
