"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, Flag, Star, X } from "lucide-react";
import AdminLayout from "@/components/admin/AdminLayout";
import { Badge, Card, EmptyState, ErrorState, LoadingRows, PageHeader, Tabs, formatDate } from "@/components/admin/ui";
import { adminApi } from "@/services/admin-api";
import { getApiErrorMessage } from "@/lib/api";
import type { ModerationReview } from "@/types";

type Queue = "pending" | "reported";

export default function AdminReviewsPage() {
  return (
    <AdminLayout title="Reviews">
      <ReviewModeration />
    </AdminLayout>
  );
}

function ReviewModeration() {
  const [queue, setQueue] = useState<Queue>("pending");

  const reviews = useQuery({
    queryKey: ["admin-reviews", queue],
    queryFn: () => adminApi.getModerationQueue({ reported_only: queue === "reported", limit: 100 }).then((r) => r.data),
  });

  const items = reviews.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Review moderation"
        description="New reviews stay hidden until approved. Reported reviews need a second look."
      />
      <Tabs
        value={queue}
        onChange={setQueue}
        options={[
          { value: "pending", label: "Awaiting approval" },
          { value: "reported", label: "Reported" },
        ]}
      />
      <Card>
        {reviews.isLoading ? (
          <LoadingRows />
        ) : reviews.isError ? (
          <ErrorState error={reviews.error} fallback="Could not load reviews." />
        ) : items.length === 0 ? (
          <EmptyState message={queue === "pending" ? "No reviews are waiting for approval." : "No reported reviews."} />
        ) : (
          <ul className="divide-y divide-gray-50">
            {items.map((review) => (
              <ReviewRow key={review.id} review={review} />
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function ReviewRow({ review }: { review: ModerationReview }) {
  const queryClient = useQueryClient();
  const done = (message: string) => {
    toast.success(message);
    queryClient.invalidateQueries({ queryKey: ["admin-reviews"] });
    queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
  };

  const approve = useMutation({
    mutationFn: () => adminApi.approveReview(review.id),
    onSuccess: () => done("Review approved and published."),
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not approve this review.")),
  });
  const reject = useMutation({
    mutationFn: () => adminApi.rejectReview(review.id),
    onSuccess: () => done("Review rejected."),
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not reject this review.")),
  });
  const busy = approve.isPending || reject.isPending;

  return (
    <li className="flex flex-wrap items-start justify-between gap-4 px-5 py-4">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-0.5 text-amber-500" aria-label={`${review.rating} out of 5 stars`}>
            {Array.from({ length: 5 }, (_, i) => (
              <Star key={i} className={`h-4 w-4 ${i < review.rating ? "fill-current" : "text-gray-200"}`} />
            ))}
          </span>
          <span className="text-sm font-medium text-gray-900">{review.user.full_name}</span>
          {review.is_reported && (
            <Badge tone="red">
              <Flag className="mr-1 h-3 w-3" /> Reported
            </Badge>
          )}
          <Badge tone={review.moderation_status === "approved" ? "green" : review.moderation_status === "rejected" ? "red" : "amber"}>
            {review.moderation_status}
          </Badge>
        </div>
        <p className="mt-1 text-sm text-gray-700">{review.comment || <span className="italic text-gray-400">No comment</span>}</p>
        <p className="mt-1 text-xs text-gray-400">{formatDate(review.created_at)}</p>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => approve.mutate()}
          disabled={busy}
          className="inline-flex items-center gap-1 rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-60"
        >
          <Check className="h-4 w-4" /> Approve
        </button>
        <button
          onClick={() => reject.mutate()}
          disabled={busy}
          className="inline-flex items-center gap-1 rounded-lg border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-60"
        >
          <X className="h-4 w-4" /> Reject
        </button>
      </div>
    </li>
  );
}
