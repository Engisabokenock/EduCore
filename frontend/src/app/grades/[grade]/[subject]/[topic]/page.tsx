import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BookOpen, ChevronRight, Lock, Download, FileText } from "lucide-react";
import { serverApi } from "@/lib/server-api";
import type { Resource } from "@/types";

interface Props {
  params: { grade: string; subject: string; topic: string };
  searchParams: { type?: string; term?: string; year?: string };
}

const TYPE_LABELS: Record<string, string> = {
  notes: "Notes",
  past_paper: "Past Papers",
  worksheet: "Worksheets",
  revision: "Revision",
  video: "Videos",
  ebook: "eBooks",
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const [grade, subject] = await Promise.all([
    serverApi.getGrade(params.grade),
    serverApi.getSubject(params.subject),
  ]);
  // Fetch topic name from subject's topic list
  const topics = await serverApi.getTopics(params.subject);
  const topic = topics?.find((t) => t.slug === params.topic);

  if (!grade || !subject || !topic) return { title: "Topic Not Found" };

  const title = `${topic.name} — ${subject.name} ${grade.name} Resources`;
  const description = `Download ${topic.name} notes, past papers, and worksheets for ${subject.name} ${grade.name}. CBC curriculum aligned.`;

  return {
    title,
    description,
    openGraph: {
      title: `${title} | EduCore`,
      description,
      url: `/grades/${params.grade}/${params.subject}/${params.topic}`,
    },
    twitter: { card: "summary_large_image", title: `${title} | EduCore`, description },
    alternates: { canonical: `/grades/${params.grade}/${params.subject}/${params.topic}` },
  };
}

function ResourceCard({ resource, gradeSlug, subjectSlug, topicSlug }: {
  resource: Resource;
  gradeSlug: string;
  subjectSlug: string;
  topicSlug: string;
}) {
  const typeLabel = TYPE_LABELS[resource.resource_type] ?? resource.resource_type;
  const sizeKb = resource.file_size ? Math.round(resource.file_size / 1024) : null;

  return (
    <Link
      href={`/resources/${resource.slug}`}
      className="group bg-white rounded-2xl border border-gray-100 hover:border-primary-300 hover:shadow-md transition-all p-5 flex flex-col gap-3"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-semibold text-primary-600 bg-primary-50 rounded-full px-2.5 py-0.5">
          {typeLabel}
        </span>
        {resource.is_premium && (
          <span className="flex items-center gap-1 text-xs font-semibold text-amber-700 bg-amber-50 rounded-full px-2.5 py-0.5">
            <Lock className="h-3 w-3" />
            Premium
          </span>
        )}
      </div>

      <div>
        <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors leading-snug line-clamp-2">
          {resource.title}
        </h3>
        {resource.description && (
          <p className="text-sm text-gray-400 mt-1 line-clamp-2">{resource.description}</p>
        )}
      </div>

      <div className="flex items-center gap-3 text-xs text-gray-400 mt-auto pt-1 border-t border-gray-50">
        {resource.term && <span>Term {resource.term}</span>}
        {resource.year && <span>{resource.year}</span>}
        {sizeKb && (
          <span className="flex items-center gap-1">
            <FileText className="h-3 w-3" />
            {sizeKb > 1024 ? `${(sizeKb / 1024).toFixed(1)} MB` : `${sizeKb} KB`}
          </span>
        )}
        <span className="flex items-center gap-1 ml-auto">
          <Download className="h-3 w-3" />
          {resource.download_count ?? 0}
        </span>
      </div>
    </Link>
  );
}

export default async function TopicPage({ params, searchParams }: Props) {
  const [grade, subject, topics] = await Promise.all([
    serverApi.getGrade(params.grade),
    serverApi.getSubject(params.subject),
    serverApi.getTopics(params.subject),
  ]);

  if (!grade || !subject) notFound();

  const topic = topics?.find((t) => t.slug === params.topic);
  if (!topic) notFound();

  const apiParams: Record<string, string> = {
    grade: params.grade,
    subject: params.subject,
    topic: params.topic,
    page_size: "24",
  };
  if (searchParams.type) apiParams.resource_type = searchParams.type;
  if (searchParams.term) apiParams.term = searchParams.term;
  if (searchParams.year) apiParams.year = searchParams.year;

  const resourcesData = await serverApi.getResources(apiParams);
  const resources: Resource[] = resourcesData?.results ?? [];

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "/" },
      { "@type": "ListItem", position: 2, name: "Grades", item: "/grades" },
      { "@type": "ListItem", position: 3, name: grade.name, item: `/grades/${params.grade}` },
      { "@type": "ListItem", position: 4, name: subject.name, item: `/grades/${params.grade}/${params.subject}` },
      { "@type": "ListItem", position: 5, name: topic.name, item: `/grades/${params.grade}/${params.subject}/${params.topic}` },
    ],
  };

  const filterUrl = (extra: Record<string, string>) => {
    const p = new URLSearchParams({
      ...(searchParams.type ? { type: searchParams.type } : {}),
      ...(searchParams.term ? { term: searchParams.term } : {}),
      ...(searchParams.year ? { year: searchParams.year } : {}),
      ...extra,
    });
    const str = p.toString();
    return str ? `?${str}` : "";
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
              <li><Link href={`/grades/${params.grade}/${params.subject}`} className="hover:text-gray-700">{subject.name}</Link></li>
              <li><ChevronRight className="h-3.5 w-3.5" /></li>
              <li className="text-gray-900 font-medium">{topic.name}</li>
            </ol>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="mb-6">
            <h1 className="text-3xl font-extrabold text-gray-900 mb-1">{topic.name}</h1>
            <p className="text-gray-500">
              {subject.name} · {grade.name}
              {resourcesData?.count != null && (
                <span className="ml-2 text-sm">· {resourcesData.count} resource{resourcesData.count !== 1 ? "s" : ""}</span>
              )}
            </p>
          </div>

          {/* Filters — URL-param based, no JS required */}
          <div className="flex flex-wrap gap-2 mb-6">
            <Link
              href={`/grades/${params.grade}/${params.subject}/${params.topic}`}
              className={`text-xs font-medium px-3 py-1.5 rounded-full border transition-colors ${
                !searchParams.type
                  ? "bg-primary-600 text-white border-primary-600"
                  : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
              }`}
            >
              All
            </Link>
            {Object.entries(TYPE_LABELS).map(([value, label]) => (
              <Link
                key={value}
                href={`/grades/${params.grade}/${params.subject}/${params.topic}${filterUrl({ type: value })}`}
                className={`text-xs font-medium px-3 py-1.5 rounded-full border transition-colors ${
                  searchParams.type === value
                    ? "bg-primary-600 text-white border-primary-600"
                    : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
                }`}
              >
                {label}
              </Link>
            ))}
          </div>

          {resources.length === 0 ? (
            <div className="py-20 text-center">
              <FileText className="h-12 w-12 text-gray-200 mx-auto mb-4" />
              <p className="text-gray-400">No resources found for this topic yet.</p>
              <Link href={`/grades/${params.grade}/${params.subject}/${params.topic}`} className="text-sm text-primary-600 hover:underline mt-2 inline-block">
                Clear filters
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {resources.map((resource) => (
                <ResourceCard
                  key={resource.id}
                  resource={resource}
                  gradeSlug={params.grade}
                  subjectSlug={params.subject}
                  topicSlug={params.topic}
                />
              ))}
            </div>
          )}
        </main>
      </div>
    </>
  );
}
