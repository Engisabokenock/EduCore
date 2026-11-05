import type { Metadata } from "next";
import Link from "next/link";
import { BookOpen, ChevronRight, GraduationCap } from "lucide-react";
import { serverApi } from "@/lib/server-api";

export const metadata: Metadata = {
  title: "Browse by Grade",
  description:
    "Access CBC curriculum notes, past papers, and worksheets for all Kenya grades — from PP1 to Grade 12.",
  openGraph: {
    title: "Browse by Grade | EduCore",
    description: "CBC curriculum resources for all grades in Kenya.",
    url: "/grades",
  },
  twitter: {
    card: "summary",
    title: "Browse by Grade | EduCore",
    description: "CBC curriculum resources for all grades in Kenya.",
  },
  alternates: { canonical: "/grades" },
};

const CURRICULUM_LABELS: Record<string, string> = {
  cbc: "CBC",
  "8-4-4": "8-4-4",
  igcse: "IGCSE",
};

export default async function GradesPage() {
  // This page is pre-rendered at build time and revalidated, so it must not throw when the
  // API is unreachable (that would fail the deploy). null means "unavailable right now".
  const result = await serverApi.getGrades();
  const unavailable = result === null;
  const grades = result ?? [];

  const grouped = grades.reduce<Record<string, typeof grades>>((acc, grade) => {
    const key = grade.curriculum ?? "cbc";
    if (!acc[key]) acc[key] = [];
    acc[key].push(grade);
    return acc;
  }, {});

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "/" },
      { "@type": "ListItem", position: 2, name: "Grades", item: "/grades" },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-100">
          <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-bold text-xl text-gray-900">
              <BookOpen className="h-7 w-7 text-primary-600" />
              EduCore
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/search" className="text-sm text-gray-600 hover:text-gray-900">Search</Link>
              <Link href="/login" className="text-sm font-medium text-primary-600 hover:text-primary-700">Log in</Link>
            </div>
          </nav>
          {/* Breadcrumb */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <ol className="flex items-center gap-1.5 text-sm text-gray-500">
              <li><Link href="/" className="hover:text-gray-700">Home</Link></li>
              <li><ChevronRight className="h-3.5 w-3.5" /></li>
              <li className="text-gray-900 font-medium">Grades</li>
            </ol>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="mb-8">
            <h1 className="text-3xl font-extrabold text-gray-900 mb-2">Browse by Grade</h1>
            <p className="text-gray-500 text-lg">
              Select your grade to access curriculum-aligned notes, past papers, and worksheets.
            </p>
          </div>

          {grades.length === 0 && (
            <p className="rounded-xl border border-gray-100 bg-white p-8 text-center text-gray-500">
              {unavailable
                ? "We couldn't load the grades just now. Please refresh in a moment."
                : "Grades are being prepared. Please check back soon."}
            </p>
          )}

          {Object.entries(grouped).map(([curriculum, curriculumGrades]) => (
            <section key={curriculum} className="mb-10">
              <h2 className="text-sm font-semibold text-primary-600 uppercase tracking-widest mb-4">
                {CURRICULUM_LABELS[curriculum] ?? curriculum} Curriculum
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {curriculumGrades.map((grade) => (
                  <Link
                    key={grade.id}
                    href={`/grades/${grade.slug}`}
                    className="group flex flex-col items-center justify-center bg-white rounded-2xl border border-gray-100 hover:border-primary-300 hover:shadow-md transition-all p-5 text-center"
                  >
                    <GraduationCap className="h-8 w-8 text-primary-500 group-hover:text-primary-600 mb-2 transition-colors" />
                    <span className="font-semibold text-gray-900 text-sm">{grade.name}</span>
                    {grade.subject_count > 0 && (
                      <span className="text-xs text-gray-400 mt-1">{grade.subject_count} subjects</span>
                    )}
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </main>
      </div>
    </>
  );
}
