"use client";

/** Small building blocks shared by the admin pages so they look and behave the same. */
import type { ReactNode } from "react";
import { Inbox } from "lucide-react";
import { getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
        {description && <p className="text-sm text-gray-500">{description}</p>}
      </div>
      {actions}
    </div>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("rounded-xl border border-gray-100 bg-white", className)}>{children}</div>;
}

export function LoadingRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-5">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
      ))}
    </div>
  );
}

export function ErrorState({ error, fallback }: { error: unknown; fallback: string }) {
  return <p className="p-8 text-center text-sm text-red-600">{getApiErrorMessage(error, fallback)}</p>;
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-2 px-5 py-12 text-center">
      <Inbox className="h-8 w-8 text-gray-300" />
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  );
}

const BADGE_TONES = {
  green: "bg-green-50 text-green-700",
  amber: "bg-amber-50 text-amber-700",
  red: "bg-red-50 text-red-700",
  blue: "bg-blue-50 text-blue-700",
  gray: "bg-gray-100 text-gray-700",
} as const;

export function Badge({ tone = "gray", children }: { tone?: keyof typeof BADGE_TONES; children: ReactNode }) {
  return (
    <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", BADGE_TONES[tone])}>{children}</span>
  );
}

export function Tabs<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <div className="inline-flex flex-wrap rounded-lg border border-gray-200 bg-white p-1">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            value === option.value ? "bg-gray-900 text-white" : "text-gray-600 hover:bg-gray-100"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

/**
 * Pagination for endpoints that return a total, or (when `total` is unknown) for
 * endpoints that only return a page: "Next" is enabled while the page is full.
 */
export function Pager({
  page,
  pageSize,
  total,
  itemsOnPage,
  onChange,
}: {
  page: number;
  pageSize: number;
  total?: number;
  itemsOnPage: number;
  onChange: (page: number) => void;
}) {
  const totalPages = total !== undefined ? Math.max(1, Math.ceil(total / pageSize)) : undefined;
  const hasNext = totalPages !== undefined ? page < totalPages : itemsOnPage === pageSize;
  if (page === 1 && !hasNext) return null;
  return (
    <div className="flex items-center justify-end gap-2 text-sm text-gray-500">
      <button
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 disabled:opacity-40"
      >
        Previous
      </button>
      <span>{totalPages ? `Page ${page} of ${totalPages}` : `Page ${page}`}</span>
      <button
        disabled={!hasNext}
        onClick={() => onChange(page + 1)}
        className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 disabled:opacity-40"
      >
        Next
      </button>
    </div>
  );
}

export const inputClass =
  "rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary-500";

export function formatDate(value?: string | null): string {
  return value ? new Date(value).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "–";
}

export function formatKes(amount: number | string): string {
  return `KES ${Number(amount).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}
