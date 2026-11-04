"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

interface Props {
  years: number[];
}

/** Year filter for the topic page (event handlers must live in a client component). */
export default function YearFilter({ years }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  return (
    <select
      aria-label="Filter by year"
      value={searchParams.get("year") ?? ""}
      onChange={(e) => {
        const params = new URLSearchParams(searchParams.toString());
        if (e.target.value) params.set("year", e.target.value);
        else params.delete("year");
        const query = params.toString();
        router.push(query ? `${pathname}?${query}` : pathname);
      }}
      className="text-xs border border-gray-200 rounded-full px-3 py-1.5 bg-white text-gray-700 focus:outline-none focus:border-primary-400"
    >
      <option value="">All Years</option>
      {years.map((y) => (
        <option key={y} value={String(y)}>{y}</option>
      ))}
    </select>
  );
}
