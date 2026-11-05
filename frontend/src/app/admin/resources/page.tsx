"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Archive, Loader2, Search, Upload } from "lucide-react";
import AdminLayout from "@/components/admin/AdminLayout";
import { Badge, Card, EmptyState, ErrorState, LoadingRows, PageHeader, Pager, Tabs, formatDate, inputClass } from "@/components/admin/ui";
import { adminApi } from "@/services/admin-api";
import { getApiErrorMessage } from "@/lib/api";
import type { AdminResourceRow } from "@/types";

type Status = "all" | "published" | "draft" | "archived";

const PAGE_SIZE = 25;
const STATUS_TONE = { published: "green", draft: "amber", archived: "gray" } as const;

export default function AdminResourcesPage() {
  return (
    <AdminLayout title="Resources">
      <ResourcesManager />
    </AdminLayout>
  );
}

function ResourcesManager() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<Status>("all");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(searchInput.trim().length >= 2 ? searchInput.trim() : "");
      setPage(1);
    }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  useEffect(() => setSelected(new Set()), [status, search, page]);

  const resources = useQuery({
    queryKey: ["admin-resources", status, search, page],
    queryFn: () =>
      adminApi.listResources({ status, search: search || undefined, page, page_size: PAGE_SIZE }).then((r) => r.data),
  });

  const bulk = useMutation({
    mutationFn: (action: "publish" | "archive") =>
      adminApi.bulkResourceAction({ target_ids: Array.from(selected), action }),
    onSuccess: (res, action) => {
      toast.success(`${res.data.processed_records_count} resource(s) ${action === "publish" ? "published" : "archived"}.`);
      setSelected(new Set());
      queryClient.invalidateQueries({ queryKey: ["admin-resources"] });
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not update the selected resources.")),
  });

  const items = resources.data?.items ?? [];
  const allSelected = items.length > 0 && items.every((r) => selected.has(r.id));

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resources"
        description="All worksheets, exams and notes, including drafts and archived items."
      />

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <Tabs
          value={status}
          onChange={(v) => {
            setStatus(v);
            setPage(1);
          }}
          options={[
            { value: "all", label: "All" },
            { value: "published", label: "Published" },
            { value: "draft", label: "Drafts" },
            { value: "archived", label: "Archived" },
          ]}
        />
        <div className="relative lg:w-80">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by title"
            className={`${inputClass} w-full pl-9`}
          />
        </div>
      </div>

      {selected.size > 0 && (
        <div className="flex flex-wrap items-center gap-3 rounded-lg border border-blue-100 bg-blue-50 px-4 py-2 text-sm">
          <span className="font-medium text-blue-900">{selected.size} selected</span>
          <button
            onClick={() => bulk.mutate("publish")}
            disabled={bulk.isPending}
            className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1 text-white hover:bg-green-700 disabled:opacity-60"
          >
            {bulk.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
            Publish
          </button>
          <button
            onClick={() => bulk.mutate("archive")}
            disabled={bulk.isPending}
            className="inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1 text-gray-700 hover:bg-gray-50 disabled:opacity-60"
          >
            <Archive className="h-3.5 w-3.5" />
            Archive
          </button>
          <button onClick={() => setSelected(new Set())} className="ml-auto text-blue-700 hover:underline">
            Clear selection
          </button>
        </div>
      )}

      <Card className="overflow-x-auto">
        {resources.isLoading ? (
          <LoadingRows />
        ) : resources.isError ? (
          <ErrorState error={resources.error} fallback="Could not load resources." />
        ) : items.length === 0 ? (
          <EmptyState message="No resources match these filters." />
        ) : (
          <table className="w-full min-w-[820px] text-sm">
            <thead className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-500">
              <tr>
                <th className="w-10 px-5 py-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={() => setSelected(allSelected ? new Set() : new Set(items.map((r) => r.id)))}
                    aria-label="Select all on this page"
                  />
                </th>
                <th className="px-3 py-3 font-medium">Resource</th>
                <th className="px-3 py-3 font-medium">Grade / subject</th>
                <th className="px-3 py-3 font-medium">Status</th>
                <th className="px-3 py-3 font-medium text-right">Downloads</th>
                <th className="px-5 py-3 font-medium">Added</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {items.map((r) => (
                <ResourceRow key={r.id} resource={r} checked={selected.has(r.id)} onToggle={() => toggle(r.id)} />
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Pager
        page={page}
        pageSize={PAGE_SIZE}
        total={resources.data?.total}
        itemsOnPage={items.length}
        onChange={setPage}
      />
    </div>
  );
}

function ResourceRow({ resource, checked, onToggle }: { resource: AdminResourceRow; checked: boolean; onToggle: () => void }) {
  return (
    <tr className={checked ? "bg-blue-50/40" : undefined}>
      <td className="px-5 py-3">
        <input type="checkbox" checked={checked} onChange={onToggle} aria-label={`Select ${resource.title}`} />
      </td>
      <td className="px-3 py-3">
        {resource.status === "published" ? (
          <Link href={`/resources/${resource.slug}`} target="_blank" className="font-medium text-gray-900 hover:underline">
            {resource.title}
          </Link>
        ) : (
          <p className="font-medium text-gray-900">{resource.title}</p>
        )}
        <p className="text-xs text-gray-500">
          {resource.type_variant.replace(/_/g, " ")} · Term {resource.term} · {resource.year}
          {resource.is_premium && " · Premium"}
        </p>
      </td>
      <td className="px-3 py-3 text-gray-600">
        {resource.grade} · {resource.subject}
      </td>
      <td className="px-3 py-3">
        <Badge tone={STATUS_TONE[resource.status]}>{resource.status}</Badge>
      </td>
      <td className="px-3 py-3 text-right text-gray-600">{resource.downloads_count.toLocaleString()}</td>
      <td className="px-5 py-3 text-gray-500">{formatDate(resource.created_at)}</td>
    </tr>
  );
}
