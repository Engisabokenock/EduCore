"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { PublicShell } from "@/components/layout/PublicShell";
import { authService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";

export default function VerifyEmailPage() {
  return (
    <PublicShell>
      <Suspense>
        <VerifyEmail />
      </Suspense>
    </PublicShell>
  );
}

function VerifyEmail() {
  const token = useSearchParams().get("token");
  const [state, setState] = useState<"verifying" | "done" | "failed">(token ? "verifying" : "failed");
  const [message, setMessage] = useState(token ? "" : "This verification link is incomplete.");
  const started = useRef(false);

  useEffect(() => {
    // Tokens are single-use: guard against React running the effect twice in development.
    if (!token || started.current) return;
    started.current = true;
    authService
      .verifyEmail(token)
      .then(() => setState("done"))
      .catch((err) => {
        setMessage(getApiErrorMessage(err, "This verification link is invalid or has already been used."));
        setState("failed");
      });
  }, [token]);

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <div className="space-y-4 rounded-2xl border border-gray-100 bg-white p-8 text-center shadow-sm">
        {state === "verifying" && (
          <>
            <Loader2 className="mx-auto h-10 w-10 animate-spin text-primary-600" />
            <h1 className="text-xl font-bold text-gray-900">Verifying your e-mail…</h1>
          </>
        )}
        {state === "done" && (
          <>
            <CheckCircle2 className="mx-auto h-10 w-10 text-green-600" />
            <h1 className="text-xl font-bold text-gray-900">E-mail verified</h1>
            <p className="text-sm text-gray-600">Thank you. Your e-mail address is confirmed.</p>
            <Link href="/dashboard" className="inline-block text-sm font-medium text-primary-600 hover:underline">
              Go to your dashboard
            </Link>
          </>
        )}
        {state === "failed" && (
          <>
            <XCircle className="mx-auto h-10 w-10 text-red-500" />
            <h1 className="text-xl font-bold text-gray-900">We could not verify this link</h1>
            <p className="text-sm text-gray-600">{message}</p>
            <Link href="/" className="inline-block text-sm font-medium text-primary-600 hover:underline">
              Back to the homepage
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
