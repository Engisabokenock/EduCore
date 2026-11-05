"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Search } from "lucide-react";
import AdminLayout from "@/components/admin/AdminLayout";
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  LoadingRows,
  PageHeader,
  Pager,
  Tabs,
  formatDate,
  formatKes,
  inputClass,
} from "@/components/admin/ui";
import { adminApi } from "@/services/admin-api";
import { getApiErrorMessage } from "@/lib/api";
import type { AdminSubscriptionRow, Transaction } from "@/types";

const PAGE_SIZE = 25;

const TX_TONE: Record<string, "green" | "amber" | "red" | "gray" | "blue"> = {
  completed: "green",
  pending: "amber",
  failed: "red",
  cancelled: "gray",
  refunded: "blue",
};

const SUB_TONE: Record<string, "green" | "amber" | "red" | "gray"> = {
  active: "green",
  canceled: "amber",
  grace_period: "amber",
  expired: "gray",
};

export default function AdminFinancialPage() {
  const [tab, setTab] = useState<"transactions" | "subscriptions">("transactions");
  return (
    <AdminLayout title="Financial">
      <div className="space-y-6">
        <PageHeader title="Financial" description="M-Pesa payments, refunds and premium subscriptions." />
        <Tabs
          value={tab}
          onChange={setTab}
          options={[
            { value: "transactions", label: "Transactions" },
            { value: "subscriptions", label: "Subscriptions" },
          ]}
        />
        {tab === "transactions" ? <Transactions /> : <Subscriptions />}
      </div>
    </AdminLayout>
  );
}

function useDebounced(value: string, delay = 350): string {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value.trim()), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

function Transactions() {
  const [status, setStatus] = useState("");
  const [phoneInput, setPhoneInput] = useState("");
  const [receiptInput, setReceiptInput] = useState("");
  const [page, setPage] = useState(1);
  const phone = useDebounced(phoneInput);
  const receipt = useDebounced(receiptInput);

  useEffect(() => setPage(1), [status, phone, receipt]);

  const transactions = useQuery({
    queryKey: ["admin-transactions", status, phone, receipt, page],
    queryFn: () =>
      adminApi
        .getTransactions({
          status: status || undefined,
          phone_number: phone || undefined,
          mpesa_receipt: receipt || undefined,
          page,
          page_size: PAGE_SIZE,
        })
        .then((r) => r.data),
  });

  const items = transactions.data ?? [];

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <select value={status} onChange={(e) => setStatus(e.target.value)} className={inputClass} aria-label="Status">
          <option value="">All statuses</option>
          <option value="completed">Completed</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
          <option value="refunded">Refunded</option>
        </select>
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={phoneInput}
            onChange={(e) => setPhoneInput(e.target.value)}
            placeholder="Phone number"
            className={`${inputClass} w-full pl-9`}
          />
        </div>
        <input
          value={receiptInput}
          onChange={(e) => setReceiptInput(e.target.value)}
          placeholder="M-Pesa receipt"
          className={`${inputClass} sm:w-48`}
        />
      </div>

      <Card className="overflow-x-auto">
        {transactions.isLoading ? (
          <LoadingRows />
        ) : transactions.isError ? (
          <ErrorState error={transactions.error} fallback="Could not load transactions." />
        ) : items.length === 0 ? (
          <EmptyState message="No transactions match these filters." />
        ) : (
          <table className="w-full min-w-[760px] text-sm">
            <thead className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-5 py-3 font-medium">Date</th>
                <th className="px-3 py-3 font-medium">Phone</th>
                <th className="px-3 py-3 font-medium text-right">Amount</th>
                <th className="px-3 py-3 font-medium">Status</th>
                <th className="px-3 py-3 font-medium">Receipt</th>
                <th className="px-5 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {items.map((tx) => (
                <TransactionRow key={tx.id} tx={tx} />
              ))}
            </tbody>
          </table>
        )}
      </Card>
      <Pager page={page} pageSize={PAGE_SIZE} itemsOnPage={items.length} onChange={setPage} />
    </div>
  );
}

function TransactionRow({ tx }: { tx: Transaction }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const refund = useMutation({
    mutationFn: () => adminApi.refundTransaction(tx.id),
    onSuccess: () => {
      toast.success("Payment marked refunded and premium access removed.");
      setConfirming(false);
      queryClient.invalidateQueries({ queryKey: ["admin-transactions"] });
      queryClient.invalidateQueries({ queryKey: ["admin-subscriptions"] });
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not refund this payment.")),
  });

  return (
    <tr>
      <td className="px-5 py-3 text-gray-600">{new Date(tx.created_at).toLocaleString()}</td>
      <td className="px-3 py-3 text-gray-900">{tx.phone_number}</td>
      <td className="px-3 py-3 text-right font-medium text-gray-900">{formatKes(tx.amount)}</td>
      <td className="px-3 py-3">
        <Badge tone={TX_TONE[tx.status] ?? "gray"}>{tx.status}</Badge>
        {tx.failure_reason && <p className="mt-0.5 max-w-[16rem] truncate text-xs text-gray-400">{tx.failure_reason}</p>}
      </td>
      <td className="px-3 py-3 font-mono text-xs text-gray-600">{tx.mpesa_receipt_number ?? "–"}</td>
      <td className="px-5 py-3 text-right">
        {tx.status === "completed" &&
          (confirming ? (
            <span className="inline-flex gap-2">
              <button
                onClick={() => refund.mutate()}
                disabled={refund.isPending}
                className="rounded-lg bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-60"
              >
                Confirm refund
              </button>
              <button onClick={() => setConfirming(false)} className="text-xs text-gray-500 hover:underline">
                Cancel
              </button>
            </span>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              className="rounded-lg border border-gray-200 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              Refund
            </button>
          ))}
      </td>
    </tr>
  );
}

function Subscriptions() {
  const [status, setStatus] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [page, setPage] = useState(1);
  const search = useDebounced(searchInput);

  useEffect(() => setPage(1), [status, search]);

  const subscriptions = useQuery({
    queryKey: ["admin-subscriptions", status, search, page],
    queryFn: () =>
      adminApi
        .listSubscriptions({
          status: status || undefined,
          search: search.length >= 2 ? search : undefined,
          page,
          page_size: PAGE_SIZE,
        })
        .then((r) => r.data),
  });

  const items = subscriptions.data?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <select value={status} onChange={(e) => setStatus(e.target.value)} className={inputClass} aria-label="Status">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="canceled">Cancelled (paid period running)</option>
          <option value="grace_period">Grace period</option>
          <option value="expired">Expired</option>
        </select>
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by name or e-mail"
            className={`${inputClass} w-full pl-9`}
          />
        </div>
      </div>

      <Card className="overflow-x-auto">
        {subscriptions.isLoading ? (
          <LoadingRows />
        ) : subscriptions.isError ? (
          <ErrorState error={subscriptions.error} fallback="Could not load subscriptions." />
        ) : items.length === 0 ? (
          <EmptyState message="No subscriptions match these filters." />
        ) : (
          <table className="w-full min-w-[720px] text-sm">
            <thead className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-5 py-3 font-medium">Subscriber</th>
                <th className="px-3 py-3 font-medium">Plan</th>
                <th className="px-3 py-3 font-medium">Status</th>
                <th className="px-3 py-3 font-medium">Access until</th>
                <th className="px-5 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {items.map((sub) => (
                <SubscriptionRow key={sub.id} sub={sub} />
              ))}
            </tbody>
          </table>
        )}
      </Card>
      <Pager
        page={page}
        pageSize={PAGE_SIZE}
        total={subscriptions.data?.total}
        itemsOnPage={items.length}
        onChange={setPage}
      />
    </div>
  );
}

function SubscriptionRow({ sub }: { sub: AdminSubscriptionRow }) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const expire = useMutation({
    mutationFn: () => adminApi.forceExpireSubscription(sub.id),
    onSuccess: () => {
      toast.success(`Premium access ended for ${sub.user_email}.`);
      setConfirming(false);
      queryClient.invalidateQueries({ queryKey: ["admin-subscriptions"] });
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not end this subscription.")),
  });

  return (
    <tr>
      <td className="px-5 py-3">
        <p className="font-medium text-gray-900">{sub.user_name || "—"}</p>
        <p className="text-xs text-gray-500">{sub.user_email}</p>
      </td>
      <td className="px-3 py-3 text-gray-700">{sub.plan_name}</td>
      <td className="px-3 py-3">
        <Badge tone={SUB_TONE[sub.status] ?? "gray"}>{sub.status.replace("_", " ")}</Badge>
        {!sub.auto_renew && sub.status !== "expired" && <p className="mt-0.5 text-xs text-gray-400">Auto-renew off</p>}
      </td>
      <td className="px-3 py-3 text-gray-600">{formatDate(sub.current_period_end)}</td>
      <td className="px-5 py-3 text-right">
        {sub.status !== "expired" &&
          (confirming ? (
            <span className="inline-flex gap-2">
              <button
                onClick={() => expire.mutate()}
                disabled={expire.isPending}
                className="rounded-lg bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-60"
              >
                Confirm end access
              </button>
              <button onClick={() => setConfirming(false)} className="text-xs text-gray-500 hover:underline">
                Cancel
              </button>
            </span>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              className="rounded-lg border border-gray-200 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              End access
            </button>
          ))}
      </td>
    </tr>
  );
}
