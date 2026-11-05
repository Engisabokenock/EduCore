"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Info, XCircle } from "lucide-react";
import AdminLayout from "@/components/admin/AdminLayout";
import { Card, ErrorState, LoadingRows, PageHeader } from "@/components/admin/ui";
import { adminApi } from "@/services/admin-api";

export default function AdminSettingsPage() {
  const settings = useQuery({
    queryKey: ["admin-settings"],
    queryFn: () => adminApi.getSystemSettings().then((r) => r.data),
  });
  const s = settings.data;

  return (
    <AdminLayout title="Settings">
      <div className="space-y-6">
        <PageHeader title="System settings" description="Current platform configuration and integration status." />

        <div className="flex gap-3 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
          <Info className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            These values come from the server&apos;s environment variables, so they apply to every server consistently.
            To change one, update the variable in your hosting dashboard (for example Railway) and redeploy.
          </p>
        </div>

        <Card>
          {settings.isLoading ? (
            <LoadingRows rows={5} />
          ) : settings.isError || !s ? (
            <ErrorState error={settings.error} fallback="Could not load settings." />
          ) : (
            <dl className="divide-y divide-gray-50">
              <Row label="Free downloads per day" hint="DAILY_FREE_DOWNLOAD_LIMIT" value={String(s.daily_free_download_limit)} />
              <Row label="Grace period after a subscription lapses" hint="SUBSCRIPTION_GRACE_PERIOD_DAYS" value={`${s.grace_period_duration_days} days`} />
              <Row label="Allowed upload types" value={s.allowed_upload_extensions.map((e) => e.toUpperCase()).join(", ")} />
              <Row label="Maintenance mode" value={<Status ok={!s.maintenance_mode} okText="Off" badText="On" />} />
              <Row
                label="M-Pesa payments"
                hint="MPESA_CONSUMER_KEY, MPESA_SHORTCODE, MPESA_PASSKEY"
                value={<Status ok={!!s.mpesa_configured} okText="Configured" badText="Not configured" />}
              />
              <Row
                label="File storage"
                hint="CLOUDFLARE_ENDPOINT, CLOUDFLARE_ACCESS_KEY, CLOUDFLARE_SECRET_KEY"
                value={<Status ok={!!s.storage_configured} okText="Configured" badText="Not configured" />}
              />
            </dl>
          )}
        </Card>
      </div>
    </AdminLayout>
  );
}

function Row({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 px-5 py-4">
      <div>
        <dt className="text-sm font-medium text-gray-900">{label}</dt>
        {hint && <p className="font-mono text-[11px] text-gray-400">{hint}</p>}
      </div>
      <dd className="text-sm text-gray-700">{value}</dd>
    </div>
  );
}

function Status({ ok, okText, badText }: { ok: boolean; okText: string; badText: string }) {
  return ok ? (
    <span className="inline-flex items-center gap-1 text-green-700">
      <CheckCircle2 className="h-4 w-4" /> {okText}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-red-600">
      <XCircle className="h-4 w-4" /> {badText}
    </span>
  );
}
