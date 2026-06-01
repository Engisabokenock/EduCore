"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Download, Loader2, Lock } from "lucide-react";
import { contentService } from "@/services/api-service";
import { useAuthStore } from "@/store/auth";

interface Props {
  slug: string;
  isPremium: boolean;
  canAccess: boolean;
}

export default function DownloadButton({ slug, isPremium, canAccess }: Props) {
  const [loading, setLoading] = useState(false);
  const { user } = useAuthStore();

  if (isPremium && !canAccess) {
    return (
      <div className="flex flex-col items-start gap-3">
        <div className="flex items-center gap-2 text-sm text-amber-700 bg-amber-50 border border-amber-100 rounded-xl px-4 py-3">
          <Lock className="h-4 w-4 shrink-0" />
          This resource requires a premium subscription.
        </div>
        <a
          href="/pricing"
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold px-6 py-3 rounded-xl text-center transition-colors"
        >
          Upgrade to Premium
        </a>
      </div>
    );
  }

  if (!user) {
    return (
      <a
        href={`/login?redirect=/resources/${slug}`}
        className="flex items-center justify-center gap-2 w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
      >
        <Download className="h-5 w-5" />
        Log in to Download
      </a>
    );
  }

  const handleDownload = async () => {
    setLoading(true);
    try {
      const res = await contentService.downloadResource(slug);
      const url: string = (res as { data: { url: string } }).data?.url ?? (res as unknown as { url: string }).url;
      if (!url) throw new Error("No download URL");
      window.open(url, "_blank", "noopener,noreferrer");
      toast.success("Download started!");
    } catch {
      toast.error("Download failed. Please try again.");
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
      {loading ? (
        <Loader2 className="h-5 w-5 animate-spin" />
      ) : (
        <Download className="h-5 w-5" />
      )}
      {loading ? "Preparing…" : "Download"}
    </button>
  );
}
