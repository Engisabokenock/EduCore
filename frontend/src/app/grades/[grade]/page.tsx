import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BookOpen, ChevronRight, FileText } from "lucide-react";
import { serverApi } from "@/lib/server-api";

interface Props {
  params: { grade: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const grade = await serverApi.getGrade(params.grade);
  const name = grade?.name ?? params.grade.replace(/^grade-/, "Grade ").toUpperCase();
  const description = grade?.name
    ? `Access CBC curriculum resources for ${grade.name} — notes, past papers, worksheets, and revision materials for all subjects.`
    : "Browse CBC curriculum resources for this grade.";

  if (!grade) {
    return {
      title: `${name} — EduCore`,
      description,
      openGraph: { title: `${name} | EduCore`, description, url: `/grades/${params.grade}`, type: "website" },
      twitter: { card: "summary", title: `${name} | EduCore`, description },
      alternates: { canonical: `/grades/${params.grade}` },
    };
  }

  const title = `${grade.name} — Notes, Past Papers & Worksheets`;

  return {
    title,
    description,
    openGraph: {
      title: `${title} | EduCore`,
      description,
      url: `/grades/${params.grade}`,
    },
    twitter: {
      card: "summary",
      title: `${title} | EduCore`,
      description,
    },
    alternates: { canonical: `/grades/${params.grade}` },
  };
}

export default async function GradePage({ params }: Props) {
  const [grade, subjectsData] = await Promise.all([
    serverApi.getGrade(params.grade),
    serverApi.getSubjects(),
  ]);

  const fallbackGrade = {
    id: params.grade,
    name: params.grade.replace(/^grade-/, "Grade ").toUpperCase(),
    slug: params.grade,
    code: params.grade.toUpperCase().replace("GRADE-", "G"),
    description: "CBC curriculum resources for this grade.",
    curriculum: "CBC",
    is_active: true,
    order: Number(params.grade.split("-")[1] ?? "1"),
    subject_count: 0,
  } as const;

  const gradeData = grade ?? fallbackGrade;

  const subjects = grade ? subjectsData ?? [] : [];

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "/" },
      { "@type": "ListItem", position: 2, name: "Grades", item: "/grades" },
      { "@type": "ListItem", position: 3, name: gradeData.name, item: `/grades/${params.grade}` },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
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
              <li><Link href="/grades" className="hover:text-gray-700">Grades</Link></li>
              <li><ChevronRight className="h-3.5 w-3.5" /></li>
              <li className="text-gray-900 font-medium">{gradeData.name}</li>
            </ol>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="mb-8">
            <h1 className="text-3xl font-extrabold text-gray-900 mb-2">{gradeData.name}</h1>
            <p className="text-gray-500 text-lg">
              Select a subject to browse study materials and past papers.
            </p>
          </div>

          {subjects.length === 0 ? (
            <p className="text-gray-400 py-12 text-center">No subjects available yet for {gradeData.name}.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {subjects.map((subject) => (
                <Link
                  key={subject.id}
                  href={`/grades/${params.grade}/${subject.slug}`}
                  className="group bg-white rounded-2xl border border-gray-100 hover:border-primary-300 hover:shadow-md transition-all p-6 flex items-start gap-4"
                >
                  <span
                    className="h-11 w-11 rounded-xl flex items-center justify-center text-xl shrink-0"
                    style={{ background: subject.color ? `${subject.color}20` : "#eff6ff" }}
                  >
                    {subject.icon || "📚"}
                  </span>
                  <div className="min-w-0">
                    <h2 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors truncate">
                      {subject.name}
                    </h2>
                    {subject.topic_count > 0 && (
                      <p className="text-sm text-gray-400 mt-1 flex items-center gap-1">
                        <FileText className="h-3.5 w-3.5" />
                        {subject.topic_count} topics
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </main>
      </div>
    </>
  );
}
