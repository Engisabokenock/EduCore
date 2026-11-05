"use client";

import { useEffect } from "react";
import Link from "next/link";
import { RefreshCw } from "lucide-react";

/**
 * Error boundary for every route. Shown when a page cannot load its data (for example
 * the API is briefly unavailable), so visitors get a retry instead of a false 404.
 */
export default function RouteError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="max-w-md text-center">
        <p className="text-sm font-semibold uppercase tracking-widest text-primary-600">Temporarily unavailable</p>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">We couldn&apos;t load this page</h1>
        <p className="mt-2 text-gray-500">
          This is usually a brief connection problem on our side. Please try again in a moment.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-700"
          >
            <RefreshCw className="h-4 w-4" /> Try again
          </button>
          <Link href="/" className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
            Back to Home
          </Link>
        </div>
        {error.digest && <p className="mt-6 text-xs text-gray-400">Reference: {error.digest}</p>}
      </div>
    </div>
  );
}
