"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/services/admin-api";
import { DollarSign } from "lucide-react";
import Link from "next/link";

export function AdminFinancialTable() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-transactions"],
    queryFn: () => adminApi.getTransactions({ page: 1, page_size: 5 }),
  });

  const transactions = data?.data ?? [];

  return (
    <div className="bg-white rounded-xl border border-gray-100">
      <div className="flex items-center justify-between p-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-green-600" />
          <h3 className="font-semibold text-gray-900">Recent Transactions</h3>
        </div>
        <Link href="/admin/financial" className="text-sm text-blue-600 hover:underline">
          View all
        </Link>
      </div>
      {isLoading ? (
        <div className="p-5 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="divide-y divide-gray-50">
          {transactions.map((tx) => (
            <div key={tx.id} className="px-5 py-3 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">{tx.phone_number}</p>
                <p className="text-xs text-gray-500">{tx.mpesa_receipt_number || "No receipt"}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">KES {tx.amount}</p>
                <p className="text-xs text-gray-500">{tx.status}</p>
              </div>
            </div>
          ))}
          {transactions.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-gray-500">No transactions found.</div>
          )}
        </div>
      )}
    </div>
  );
}
