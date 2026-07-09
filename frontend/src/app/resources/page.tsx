import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BookOpen, ChevronRight, Download, Eye, FileText } from "lucide-react";
import { serverApi } from "@/lib/server-api";

interface Props {
  searchParams: { type?: string };
}

const TYPE_LABELS: Record<string, string> = {
  notes: "Notes",
  past_paper: "Past Paper",
  worksheet: "Worksheet",
  revision: "Revision Notes",
  video: "Video",
  audio: "Audio",
  ebook: "eBook",
};

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const type = searchParams.type;
  const title = type ? `${TYPE_LABELS[type] ?? "Resources"} — EduCore` : "All Resources — EduCore";
  const description = type
    ? `Browse ${TYPE_LABELS[type] ?? "resources"} on EduCore.`
    : "Browse all EduCore resources: notes, past papers, worksheets, and revision materials.";

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url: type ? `/resources?type=${type}` : "/resources",
    },
    alternates: { canonical: type ? `/resources?type=${type}` : "/resources" },
  };
}

export default async function ResourcesPage({ searchParams }: Props) {
  const type = searchParams.type;
  const resources = type ? await serverApi.getResources({ type }) : await serverApi.getResources({});

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-gray-900">
            <BookOpen className="h-7 w-7 text-primary-600" />
            EduCore
          </Link>
          <Link href="/search" className="text-sm text-gray-600 hover:text-gray-900">Search</Link>
        </nav>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <ol className="flex items-center gap-1.5 text-sm text-gray-500 flex-wrap">
            <li><Link href="/" className="hover:text-gray-700">Home</Link></li>
            <li><ChevronRight className="h-3.5 w-3.5" /></li>
            <li className="text-gray-900 font-medium">{type ? TYPE_LABELS[type] ?? "Resources" : "All Resources"}</li>
          </ol>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900 mb-2">
            {type ? TYPE_LABELS[type] ?? "Resources" : "All Resources"}
          </h1>
          <p className="text-gray-500 text-lg">
            Browse and download CBC curriculum notes, past papers, worksheets, and more.
          </p>
        </div>

        {!resources || resources.results.length === 0 ? (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-10 text-center text-gray-500">
            No resources found{type ? ` for ${TYPE_LABELS[type] ?? type}` : ""}.
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {resources.results.map((r) => (
              <Link
                key={r.id}
                href={`/resources/${r.slug}`}
                className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-all p-4 flex flex-col"
              >
                <div className="flex items-start gap-3 mb-3">
                  <FileText className="h-5 w-5 text-gray-300 shrink-0 mt-0.5" />
                  <div className="min-w-0">
                    <h3 className="font-semibold text-gray-900 truncate">{r.title}</h3>
                    <p className="text-xs text-gray-400 line-clamp-2">{r.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-500 mt-auto">
                  <span className="flex items-center gap-1">
                    <Eye className="h-3.5 w-3.5" />
                    {r.view_count ?? 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <Download className="h-3.5 w-3.5" />
                    {r.download_count ?? 0}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
