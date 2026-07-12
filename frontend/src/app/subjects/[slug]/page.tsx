import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BookOpen, ChevronRight, FileText, Download, Eye } from "lucide-react";
import { serverApi } from "@/lib/server-api";

interface Props {
  params: { slug: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const subject = await serverApi.getSubject(params.slug);
  const fallback = {
    mathematics: { name: "Mathematics", description: "CBC Mathematics resources and revision notes." },
    english: { name: "English", description: "CBC English resources and revision notes." },
  }[params.slug];

  const name = subject?.name ?? fallback?.name ?? "Subject";
  const description = subject?.description ?? fallback?.description ?? "Browse CBC curriculum resources.";

  if (!subject) {
    return {
      title: `${name} — EduCore`,
      description,
      openGraph: { title: `${name} | EduCore`, description, url: `/subjects/${params.slug}`, type: "website" },
      twitter: { card: "summary_large_image", title: `${name} | EduCore`, description },
      alternates: { canonical: `/subjects/${params.slug}` },
    };
  }

  const title = `${subject.name} — CBC notes, past papers & worksheets`;

  return {
    title,
    description: subject.description || `Browse ${subject.name} notes, past papers, worksheets, and revision materials — CBC curriculum Kenya.`,
    openGraph: {
      title: `${title} | EduCore`,
      description,
      url: `/subjects/${params.slug}`,
      type: "website",
    },
    twitter: { card: "summary_large_image", title: `${title} | EduCore`, description },
    alternates: { canonical: `/subjects/${params.slug}` },
  };
}

export default async function SubjectPage({ params }: Props) {
  let subject = await serverApi.getSubject(params.slug);
  if (!subject) {
    const fallback = {
      mathematics: {
        name: "Mathematics",
        description: "CBC Mathematics resources and revision notes.",
        slug: "mathematics",
        topics: [{ id: "general", name: "General", slug: "general", resource_count: 0 }],
        grade: { slug: "grade-1", name: "Grade 1" },
      },
      english: {
        name: "English",
        description: "CBC English resources and revision notes.",
        slug: "english",
        topics: [{ id: "general", name: "General", slug: "general", resource_count: 0 }],
        grade: { slug: "grade-1", name: "Grade 1" },
      },
      kiswahili: {
        name: "Kiswahili",
        description: "CBC Kiswahili resources and revision notes.",
        slug: "kiswahili",
        topics: [{ id: "general", name: "General", slug: "general", resource_count: 0 }],
        grade: { slug: "grade-1", name: "Grade 1" },
      },
      science: {
        name: "Science",
        description: "CBC Science resources and revision notes.",
        slug: "science",
        topics: [{ id: "general", name: "General", slug: "general", resource_count: 0 }],
        grade: { slug: "grade-1", name: "Grade 1" },
      },
      "social-studies": {
        name: "Social Studies",
        description: "CBC Social Studies resources and revision notes.",
        slug: "social-studies",
        topics: [{ id: "general", name: "General", slug: "general", resource_count: 0 }],
        grade: { slug: "grade-1", name: "Grade 1" },
      },
      "cre-ire": {
        name: "CRE / IRE",
        description: "CBC Religious Education resources and revision notes.",
        slug: "cre-ire",
        topics: [{ id: "general", name: "General", slug: "general", resource_count: 0 }],
        grade: { slug: "grade-1", name: "Grade 1" },
      },
      "creative-arts": {
        name: "Creative Arts",
        description: "CBC Creative Arts resources and revision notes.",
        slug: "creative-arts",
        topics: [{ id: "general", name: "General", slug: "general", resource_count: 0 }],
        grade: { slug: "grade-1", name: "Grade 1" },
      },
      design: {
        name: "Design",
        description: "CBC Design resources and revision notes.",
        slug: "design",
        topics: [{ id: "general", name: "General", slug: "general", resource_count: 0 }],
        grade: { slug: "grade-1", name: "Grade 1" },
      },
    }[params.slug];
    if (fallback) {
      subject = fallback as any;
    }
  }
  if (!subject) notFound();

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
            <li><span className="text-gray-900 font-medium">{subject.name}</span></li>
          </ol>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="p-6 sm:p-8 border-b border-gray-50">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mb-3">{subject.name}</h1>
            {subject.description && (
              <p className="text-gray-500 leading-relaxed">{subject.description}</p>
            )}
          </div>

          <div className="p-6 sm:p-8">
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {subject.topics?.length ? subject.topics.map((topic) => (
                <Link
                  key={topic.id}
                  href={`/grades/${subject.grade?.slug ?? ""}/${subject.slug}/${topic.slug}`}
                  className="block rounded-xl border border-gray-100 p-5 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="h-4 w-4 text-gray-400" />
                    <span className="text-sm font-semibold text-gray-900">{topic.name}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Download className="h-3.5 w-3.5" />
                      {topic.resource_count}
                    </span>
                  </div>
                </Link>
              )) : (
                <p className="text-sm text-gray-500">No topics available yet.</p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
