import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  BookOpen, ChevronRight, Download, Eye, Lock,
  FileText, Calendar, Tag,
} from "lucide-react";
import { serverApi } from "@/lib/server-api";
import DownloadButton from "./DownloadButton";

interface Props {
  params: { slug: string };
}

const TYPE_LABELS: Record<string, string> = {
  notes: "Notes", past_paper: "Past Paper", worksheet: "Worksheet",
  revision: "Revision", video: "Video", audio: "Audio", ebook: "eBook",
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const resource = await serverApi.getResource(params.slug);
  if (!resource) return { title: "Resource Not Found" };

  const grade = resource.grade?.name ?? "";
  const subject = resource.subject?.name ?? "";
  const type = TYPE_LABELS[resource.resource_type] ?? resource.resource_type;
  const title = `${resource.title} — ${type}${grade ? ` · ${grade}` : ""}${subject ? ` ${subject}` : ""}`;
  const description = resource.description || `Download ${resource.title}. ${type} for ${subject} ${grade} — CBC curriculum Kenya.`;

  return {
    title,
    description,
    openGraph: {
      title: `${title} | EduCore`,
      description,
      url: `/resources/${params.slug}`,
      type: "article",
    },
    twitter: { card: "summary_large_image", title: `${title} | EduCore`, description },
    alternates: { canonical: `/resources/${params.slug}` },
  };
}

export default async function ResourceDetailPage({ params }: Props) {
  const resource = await serverApi.getResource(params.slug);
  if (!resource) notFound();

  const grade = resource.grade;
  const subject = resource.subject;
  const topic = resource.topic;
  const type = TYPE_LABELS[resource.resource_type] ?? resource.resource_type;
  const sizeKb = resource.file_size ? Math.round(resource.file_size / 1024) : null;

  const gradeHref = grade ? `/grades/${grade.slug}` : "/grades";
  const subjectHref = grade && subject ? `/grades/${grade.slug}/${subject.slug}` : gradeHref;
  const topicHref = grade && subject && topic
    ? `/grades/${grade.slug}/${subject.slug}/${topic.slug}`
    : subjectHref;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: resource.title,
    description: resource.description,
    datePublished: resource.published_at ?? resource.created_at,
    publisher: {
      "@type": "Organization",
      name: "EduCore",
      url: process.env.NEXT_PUBLIC_SITE_URL ?? "https://educore.co.ke",
    },
    breadcrumb: {
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "Home", item: "/" },
        ...(grade ? [{ "@type": "ListItem", position: 2, name: grade.name, item: gradeHref }] : []),
        ...(subject ? [{ "@type": "ListItem", position: 3, name: subject.name, item: subjectHref }] : []),
        ...(topic ? [{ "@type": "ListItem", position: 4, name: topic.name, item: topicHref }] : []),
        { "@type": "ListItem", position: 5, name: resource.title, item: `/resources/${params.slug}` },
      ],
    },
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
              {grade && (
                <>
                  <li><ChevronRight className="h-3.5 w-3.5" /></li>
                  <li><Link href={gradeHref} className="hover:text-gray-700">{grade.name}</Link></li>
                </>
              )}
              {subject && (
                <>
                  <li><ChevronRight className="h-3.5 w-3.5" /></li>
                  <li><Link href={subjectHref} className="hover:text-gray-700">{subject.name}</Link></li>
                </>
              )}
              {topic && (
                <>
                  <li><ChevronRight className="h-3.5 w-3.5" /></li>
                  <li><Link href={topicHref} className="hover:text-gray-700">{topic.name}</Link></li>
                </>
              )}
              <li><ChevronRight className="h-3.5 w-3.5" /></li>
              <li className="text-gray-900 font-medium truncate max-w-[200px]">{resource.title}</li>
            </ol>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            {/* Resource header */}
            <div className="p-6 sm:p-8 border-b border-gray-50">
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <span className="text-xs font-semibold text-primary-600 bg-primary-50 rounded-full px-3 py-1">
                  {type}
                </span>
                {resource.is_premium && (
                  <span className="flex items-center gap-1 text-xs font-semibold text-amber-700 bg-amber-50 rounded-full px-3 py-1">
                    <Lock className="h-3 w-3" />
                    Premium
                  </span>
                )}
                {resource.term && (
                  <span className="text-xs text-gray-500 bg-gray-50 rounded-full px-3 py-1">
                    Term {resource.term}
                  </span>
                )}
                {resource.year && (
                  <span className="text-xs text-gray-500 bg-gray-50 rounded-full px-3 py-1">
                    {resource.year}
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mb-3 leading-tight">
                {resource.title}
              </h1>

              {resource.description && (
                <p className="text-gray-500 leading-relaxed">{resource.description}</p>
              )}
            </div>

            {/* Meta grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-y sm:divide-y-0 divide-gray-50 border-b border-gray-50">
              {grade && (
                <div className="p-4">
                  <p className="text-xs text-gray-400 mb-1">Grade</p>
                  <p className="font-medium text-gray-800 text-sm">{grade.name}</p>
                </div>
              )}
              {subject && (
                <div className="p-4">
                  <p className="text-xs text-gray-400 mb-1">Subject</p>
                  <p className="font-medium text-gray-800 text-sm">{subject.name}</p>
                </div>
              )}
              <div className="p-4">
                <p className="text-xs text-gray-400 mb-1">Downloads</p>
                <p className="font-medium text-gray-800 text-sm flex items-center gap-1">
                  <Download className="h-3.5 w-3.5 text-gray-400" />
                  {resource.downloads_count ?? 0}
                </p>
              </div>
              <div className="p-4">
                <p className="text-xs text-gray-400 mb-1">Views</p>
                <p className="font-medium text-gray-800 text-sm flex items-center gap-1">
                  <Eye className="h-3.5 w-3.5 text-gray-400" />
                  {resource.views_count ?? 0}
                </p>
              </div>
              {sizeKb && (
                <div className="p-4">
                  <p className="text-xs text-gray-400 mb-1">File size</p>
                  <p className="font-medium text-gray-800 text-sm flex items-center gap-1">
                    <FileText className="h-3.5 w-3.5 text-gray-400" />
                    {sizeKb > 1024 ? `${(sizeKb / 1024).toFixed(1)} MB` : `${sizeKb} KB`}
                  </p>
                </div>
              )}
              {resource.published_at && (
                <div className="p-4">
                  <p className="text-xs text-gray-400 mb-1">Published</p>
                  <p className="font-medium text-gray-800 text-sm flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5 text-gray-400" />
                    {new Date(resource.published_at).toLocaleDateString("en-KE", {
                      year: "numeric", month: "short", day: "numeric",
                    })}
                  </p>
                </div>
              )}
            </div>

            {/* Tags */}
            {resource.tags && resource.tags.length > 0 && (
              <div className="px-6 sm:px-8 py-4 border-b border-gray-50 flex flex-wrap gap-2">
                <Tag className="h-4 w-4 text-gray-300 shrink-0 mt-0.5" />
                {resource.tags.map((tag) => (
                  <Link
                    key={tag}
                    href={`/search?q=${encodeURIComponent(tag)}`}
                    className="text-xs text-gray-500 bg-gray-50 hover:bg-primary-50 hover:text-primary-600 rounded-full px-2.5 py-1 transition-colors"
                  >
                    {tag}
                  </Link>
                ))}
              </div>
            )}

            {/* Download CTA */}
            <div className="p-6 sm:p-8">
              <DownloadButton slug={params.slug} isPremium={resource.is_premium} />
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
