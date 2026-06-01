import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BookOpen, ChevronRight } from "lucide-react";
import { serverApi } from "@/lib/server-api";

interface Props {
  params: { grade: string; subject: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const [grade, subject] = await Promise.all([
    serverApi.getGrade(params.grade),
    serverApi.getSubject(params.subject),
  ]);
  if (!grade || !subject) return { title: "Subject Not Found" };

  const title = `${subject.name} — ${grade.name} Notes & Past Papers`;
  const description = `Browse all ${subject.name} topics for ${grade.name}. Find notes, past papers, worksheets and revision materials.`;

  return {
    title,
    description,
    openGraph: {
      title: `${title} | EduCore`,
      description,
      url: `/grades/${params.grade}/${params.subject}`,
    },
    twitter: { card: "summary", title: `${title} | EduCore`, description },
    alternates: { canonical: `/grades/${params.grade}/${params.subject}` },
  };
}

export default async function SubjectPage({ params }: Props) {
  const [grade, subject, topics] = await Promise.all([
    serverApi.getGrade(params.grade),
    serverApi.getSubject(params.subject),
    serverApi.getTopics(params.subject),
  ]);

  if (!grade || !subject) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "/" },
      { "@type": "ListItem", position: 2, name: "Grades", item: "/grades" },
      { "@type": "ListItem", position: 3, name: grade.name, item: `/grades/${params.grade}` },
      { "@type": "ListItem", position: 4, name: subject.name, item: `/grades/${params.grade}/${params.subject}` },
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
              <li><Link href={`/grades/${params.grade}`} className="hover:text-gray-700">{grade.name}</Link></li>
              <li><ChevronRight className="h-3.5 w-3.5" /></li>
              <li className="text-gray-900 font-medium">{subject.name}</li>
            </ol>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <span
                className="h-10 w-10 rounded-xl flex items-center justify-center text-xl"
                style={{ background: subject.color ? `${subject.color}20` : "#eff6ff" }}
              >
                {subject.icon || "📚"}
              </span>
              <h1 className="text-3xl font-extrabold text-gray-900">{subject.name}</h1>
            </div>
            <p className="text-gray-500">
              {grade.name} · {subject.description || "Select a topic to view study materials."}
            </p>
          </div>

          {!topics || topics.length === 0 ? (
            <p className="text-gray-400 py-12 text-center">No topics available yet.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {topics.map((topic, index) => (
                <Link
                  key={topic.id}
                  href={`/grades/${params.grade}/${params.subject}/${topic.slug}`}
                  className="group bg-white rounded-2xl border border-gray-100 hover:border-primary-300 hover:shadow-md transition-all p-5"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-bold text-primary-500 bg-primary-50 rounded-lg px-2.5 py-1.5 shrink-0">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <div>
                      <h2 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors leading-snug">
                        {topic.name}
                      </h2>
                      {topic.description && (
                        <p className="text-sm text-gray-400 mt-1 line-clamp-2">{topic.description}</p>
                      )}
                    </div>
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
