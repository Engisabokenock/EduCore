import type { Metadata } from "next";
import Link from "next/link";
import { BookOpen, ChevronRight } from "lucide-react";
import { serverApi } from "@/lib/server-api";
import type { Subject } from "@/types";

export const metadata: Metadata = {
  title: "Subjects — EduCore",
  description: "Browse all CBC subjects and topics.",
  alternates: { canonical: "/subjects" },
};

export default async function SubjectsPage() {
  const subjects: Subject[] = (await serverApi.getSubjects()) ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-gray-900">
            <BookOpen className="h-7 w-7 text-primary-600" />
            EduCore
          </Link>
          <Link href="/search" className="text-sm text-gray-600 hover:text-gray-900">Search</Link>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <ol className="flex items-center gap-1.5 text-sm text-gray-500 flex-wrap">
            <li><Link href="/" className="hover:text-gray-700">Home</Link></li>
            <li><ChevronRight className="h-3.5 w-3.5" /></li>
            <li className="text-gray-900 font-medium">Subjects</li>
          </ol>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900 mb-2">All Subjects</h1>
          <p className="text-gray-500">Cover every area of the CBC curriculum</p>
        </div>

        {subjects.length === 0 ? (
          <div className="py-20 text-center">
            <BookOpen className="h-12 w-12 text-gray-200 mx-auto mb-4" />
            <p className="text-gray-400">No subjects available yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {subjects.map((subject) => (
              <Link
                key={subject.id}
                href={`/subjects/${subject.slug}`}
                className={`${subject.color || "bg-gray-50 text-gray-700 border-gray-100"} rounded-xl border p-4 hover:shadow-md transition-all`}
              >
                <span className="text-2xl block mb-2">{subject.icon || "📚"}</span>
                <h3 className="font-semibold text-sm">{subject.name}</h3>
                {subject.grade && (
                  <p className="text-xs text-gray-500 mt-1">{subject.grade.name}</p>
                )}
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
