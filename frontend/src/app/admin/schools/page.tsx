"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, Plus } from "lucide-react";
import AdminLayout from "@/components/admin/AdminLayout";
import { Badge, Card, EmptyState, ErrorState, LoadingRows, PageHeader, Tabs, formatDate, inputClass } from "@/components/admin/ui";
import { adminApi } from "@/services/admin-api";
import { getApiErrorMessage } from "@/lib/api";

const schema = z.object({
  name: z.string().trim().min(3, "Enter the school's name"),
  registration_code: z.string().trim().min(3, "Enter the registration code"),
  address: z.string().trim().optional(),
});
type SchoolForm = z.infer<typeof schema>;

export default function AdminSchoolsPage() {
  return (
    <AdminLayout title="Schools">
      <SchoolsManager />
    </AdminLayout>
  );
}

function SchoolsManager() {
  const [filter, setFilter] = useState<"all" | "active" | "inactive">("all");
  const [showForm, setShowForm] = useState(false);

  const schools = useQuery({
    queryKey: ["admin-schools", filter],
    queryFn: () => adminApi.getSchools(filter === "all" ? undefined : filter === "active").then((r) => r.data),
  });

  const items = schools.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Schools"
        description="Institutions registered on EduCore."
        actions={
          <button
            onClick={() => setShowForm((v) => !v)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            <Plus className="h-4 w-4" /> Add school
          </button>
        }
      />

      {showForm && <CreateSchool onDone={() => setShowForm(false)} />}

      <Tabs
        value={filter}
        onChange={setFilter}
        options={[
          { value: "all", label: "All" },
          { value: "active", label: "Active" },
          { value: "inactive", label: "Inactive" },
        ]}
      />

      <Card className="overflow-x-auto">
        {schools.isLoading ? (
          <LoadingRows />
        ) : schools.isError ? (
          <ErrorState error={schools.error} fallback="Could not load schools." />
        ) : items.length === 0 ? (
          <EmptyState message="No schools registered yet." />
        ) : (
          <table className="w-full min-w-[640px] text-sm">
            <thead className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-5 py-3 font-medium">School</th>
                <th className="px-3 py-3 font-medium">Registration code</th>
                <th className="px-3 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Added</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {items.map((school) => (
                <tr key={school.id}>
                  <td className="px-5 py-3">
                    <p className="font-medium text-gray-900">{school.name}</p>
                    {school.address && <p className="text-xs text-gray-500">{school.address}</p>}
                  </td>
                  <td className="px-3 py-3 font-mono text-xs text-gray-600">{school.registration_code}</td>
                  <td className="px-3 py-3">
                    <Badge tone={school.is_active ? "green" : "gray"}>{school.is_active ? "Active" : "Inactive"}</Badge>
                  </td>
                  <td className="px-5 py-3 text-gray-500">{formatDate(school.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

function CreateSchool({ onDone }: { onDone: () => void }) {
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SchoolForm>({ resolver: zodResolver(schema) });

  const create = useMutation({
    mutationFn: (data: SchoolForm) =>
      adminApi.createSchool({ name: data.name, registration_code: data.registration_code, address: data.address || undefined }),
    onSuccess: (res) => {
      toast.success(`${res.data.name} added.`);
      reset();
      queryClient.invalidateQueries({ queryKey: ["admin-schools"] });
      onDone();
    },
    onError: (err) => toast.error(getApiErrorMessage(err, "Could not add the school.")),
  });

  return (
    <Card className="p-5">
      <form onSubmit={handleSubmit((d) => create.mutate(d))} className="grid gap-4 sm:grid-cols-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">School name</label>
          <input {...register("name")} className={`${inputClass} w-full`} />
          {errors.name && <p className="mt-1 text-xs text-red-500">{errors.name.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Registration code</label>
          <input {...register("registration_code")} className={`${inputClass} w-full`} />
          {errors.registration_code && <p className="mt-1 text-xs text-red-500">{errors.registration_code.message}</p>}
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Address (optional)</label>
          <input {...register("address")} className={`${inputClass} w-full`} />
        </div>
        <div className="flex gap-2 sm:col-span-3">
          <button
            type="submit"
            disabled={create.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-60"
          >
            {create.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Save school
          </button>
          <button type="button" onClick={onDone} className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">
            Cancel
          </button>
        </div>
      </form>
    </Card>
  );
}
