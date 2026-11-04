"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Download, Loader2, Lock } from "lucide-react";
import { contentService } from "@/services/api-service";
import { getApiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

interface Props {
  slug: string;
  isPremium: boolean;
}

/**
 * Download CTA. Access is decided by the API (subscription, role, quota). The page is
 * statically rendered for every visitor, so it can't know who is viewing it.
 */
export default function DownloadButton({ slug, isPremium }: Props) {
  const [loading, setLoading] = useState(false);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const { data: access, isLoading: checking } = useQuery({
    queryKey: ["resource-access", slug, isAuthenticated],
    queryFn: async () => (await contentService.checkAccess(slug)).data,
    enabled: isPremium,
    staleTime: 60_000,
  });

  const loginHref = `/login?redirect=${encodeURIComponent(`/resources/${slug}`)}`;

  if (isPremium && checking) {
    return <div className="h-12 w-full rounded-xl bg-gray-100 animate-pulse" aria-label="Checking access" />;
  }

  if (isPremium && access && !access.can_access) {
    return (
      <div className="flex flex-col items-start gap-3">
        <div className="flex items-center gap-2 text-sm text-amber-700 bg-amber-50 border border-amber-100 rounded-xl px-4 py-3">
          <Lock className="h-4 w-4 shrink-0" />
          This resource is part of EduCore Premium.
        </div>
        <a
          href={access.requires_login ? loginHref : "/pricing"}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold px-6 py-3 rounded-xl text-center transition-colors"
        >
          {access.requires_login ? "Log in to continue" : "Upgrade to Premium"}
        </a>
      </div>
    );
  }

  const handleDownload = async () => {
    setLoading(true);
    try {
      const { data } = await contentService.downloadResource(slug);
      if (!data?.url) throw new Error("No download URL");
      window.open(data.url, "_blank", "noopener,noreferrer");
      toast.success("Download started!");
    } catch (err) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) {
        window.location.href = loginHref;
        return;
      }
      toast.error(getApiErrorMessage(err, "Download failed. Please try again."), {
        action: status === 429 || status === 403
          ? { label: "See plans", onClick: () => (window.location.href = "/pricing") }
          : undefined,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className="flex items-center justify-center gap-2 w-full bg-primary-600 hover:bg-primary-700 disabled:opacity-60 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
    >
      {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Download className="h-5 w-5" />}
      {loading ? "Preparing…" : "Download"}
    </button>
  );
}
