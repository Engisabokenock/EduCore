import Link from "next/link";
import { BookOpen, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-4">
      <BookOpen className="h-12 w-12 text-primary-600 mb-4" />
      <h1 className="text-6xl font-extrabold text-gray-900 mb-2">404</h1>
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Page not found</h2>
      <p className="text-gray-500 text-center max-w-md mb-8">
        The page you&apos;re looking for doesn&apos;t exist. It may have been moved or deleted.
      </p>
      <div className="flex gap-4">
        <Link
          href="/"
          className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-5 py-2.5 rounded-lg font-medium text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>
        <Link
          href="/grades"
          className="flex items-center gap-2 border border-gray-200 hover:border-gray-300 text-gray-700 px-5 py-2.5 rounded-lg font-medium text-sm transition-colors"
        >
          Browse Grades
        </Link>
      </div>
    </div>
  );
}
