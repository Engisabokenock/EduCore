import type { Metadata } from "next";
import Link from "next/link";
import { BookOpen, Search, FileText, GraduationCap, BookMarked, Tag } from "lucide-react";
import { serverApi } from "@/lib/server-api";
import type { Resource, Grade, Subject, Topic } from "@/types";

interface Props {
  searchParams: { q?: string; category?: string };
}

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const q = searchParams.q?.trim() ?? "";
  if (!q) {
    return {
      title: "Search",
      description: "Search EduCore for CBC curriculum notes, past papers, worksheets, and study materials.",
      alternates: { canonical: "/search" },
    };
  }
  return {
    title: `Search: "${q}"`,
    description: `Search results for "${q}" — notes, past papers and worksheets on EduCore.`,
    robots: { index: false },
  };
}

const TYPE_LABELS: Record<string, string> = {
  notes: "Notes", past_paper: "Past Paper", worksheet: "Worksheet",
  revision: "Revision", video: "Video", ebook: "eBook",
};

function ResourceResult({ resource }: { resource: Resource }) {
  return (
    <Link
      href={`/resources/${resource.slug}`}
      className="group bg-white rounded-xl border border-gray-100 hover:border-primary-300 hover:shadow-sm transition-all p-4 flex items-start gap-3"
    >
      <FileText className="h-5 w-5 text-gray-300 shrink-0 mt-0.5" />
      <div className="min-w-0">
        <p className="text-xs text-primary-600 font-medium mb-0.5">
          {TYPE_LABELS[resource.resource_type] ?? resource.resource_type}
          {resource.grade && ` · ${resource.grade.name}`}
          {resource.subject && ` · ${resource.subject.name}`}
        </p>
        <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors truncate">
          {resource.title}
        </h3>
        {resource.description && (
          <p className="text-sm text-gray-400 mt-0.5 line-clamp-1">{resource.description}</p>
        )}
      </div>
    </Link>
  );
}

function GradeResult({ grade }: { grade: Grade }) {
  return (
    <Link
      href={`/grades/${grade.slug}`}
      className="group bg-white rounded-xl border border-gray-100 hover:border-primary-300 hover:shadow-sm transition-all p-4 flex items-center gap-3"
    >
      <GraduationCap className="h-5 w-5 text-primary-400 shrink-0" />
      <span className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
        {grade.name}
      </span>
      {grade.subject_count > 0 && (
        <span className="ml-auto text-xs text-gray-400">{grade.subject_count} subjects</span>
      )}
    </Link>
  );
}

function SubjectResult({ subject }: { subject: Subject }) {
  return (
    <Link
      href={`/search?q=${encodeURIComponent(subject.name)}&category=topics`}
      className="group bg-white rounded-xl border border-gray-100 hover:border-primary-300 hover:shadow-sm transition-all p-4 flex items-center gap-3"
    >
      <BookMarked className="h-5 w-5 text-gray-300 shrink-0" />
      <span className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
        {subject.name}
      </span>
      {subject.topic_count > 0 && (
        <span className="ml-auto text-xs text-gray-400">{subject.topic_count} topics</span>
      )}
    </Link>
  );
}

function TopicResult({ topic }: { topic: Topic }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 flex items-center gap-3">
      <Tag className="h-5 w-5 text-gray-300 shrink-0" />
      <span className="font-medium text-gray-800">{topic.name}</span>
    </div>
  );
}

export default async function SearchPage({ searchParams }: Props) {
  const q = searchParams.q?.trim() ?? "";
  const category = searchParams.category ?? "all";

  let results: Awaited<ReturnType<typeof serverApi.search>> = null;
  if (q.length >= 2) {
    results = await serverApi.search(q, category !== "all" ? category : undefined);
  }

  const total =
    (results?.resources?.length ?? 0) +
    (results?.grades?.length ?? 0) +
    (results?.subjects?.length ?? 0) +
    (results?.topics?.length ?? 0);

  const CATEGORIES = [
    { value: "all", label: "All" },
    { value: "resources", label: "Resources" },
    { value: "grades", label: "Grades" },
    { value: "subjects", label: "Subjects" },
    { value: "topics", label: "Topics" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-gray-900">
            <BookOpen className="h-7 w-7 text-primary-600" />
            EduCore
          </Link>
        </nav>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Search form — native form submission, works without JS */}
        <form action="/search" method="get" className="mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
            <input
              type="search"
              name="q"
              defaultValue={q}
              placeholder="Search for notes, past papers, topics…"
              autoFocus
              className="w-full pl-12 pr-4 py-3.5 rounded-2xl border border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none text-gray-900 bg-white shadow-sm text-base"
            />
          </div>
        </form>

        {/* Category tabs */}
        {q && (
          <div className="flex flex-wrap gap-2 mb-6">
            {CATEGORIES.map(({ value, label }) => (
              <Link
                key={value}
                href={`/search?q=${encodeURIComponent(q)}&category=${value}`}
                className={`text-sm font-medium px-4 py-1.5 rounded-full border transition-colors ${
                  (value === "all" && !searchParams.category) || searchParams.category === value
                    ? "bg-primary-600 text-white border-primary-600"
                    : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
                }`}
              >
                {label}
              </Link>
            ))}
          </div>
        )}

        {!q && (
          <div className="text-center py-16 text-gray-400">
            <Search className="h-12 w-12 mx-auto mb-4 text-gray-200" />
            <p>Start typing to search across grades, subjects, topics, and resources.</p>
          </div>
        )}

        {q && !results && (
          <p className="text-gray-400 text-center py-12">Query too short — please enter at least 2 characters.</p>
        )}

        {results && total === 0 && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg font-medium text-gray-700 mb-2">No results for &ldquo;{q}&rdquo;</p>
            <p>Try a different search term or browse by <Link href="/grades" className="text-primary-600 hover:underline">grade</Link>.</p>
          </div>
        )}

        {results && total > 0 && (
          <div className="space-y-8">
            {results.resources && results.resources.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">
                  Resources ({results.resources.length})
                </h2>
                <div className="space-y-2">
                  {results.resources.map((r) => <ResourceResult key={r.id} resource={r} />)}
                </div>
              </section>
            )}

            {results.grades && results.grades.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">
                  Grades ({results.grades.length})
                </h2>
                <div className="space-y-2">
                  {results.grades.map((g) => <GradeResult key={g.id} grade={g} />)}
                </div>
              </section>
            )}

            {results.subjects && results.subjects.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">
                  Subjects ({results.subjects.length})
                </h2>
                <div className="space-y-2">
                  {results.subjects.map((s) => <SubjectResult key={s.id} subject={s} />)}
                </div>
              </section>
            )}

            {results.topics && results.topics.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">
                  Topics ({results.topics.length})
                </h2>
                <div className="grid grid-cols-2 gap-2">
                  {results.topics.map((t) => <TopicResult key={t.id} topic={t} />)}
                </div>
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
