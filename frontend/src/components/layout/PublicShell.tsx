import Link from "next/link";
import type { ReactNode } from "react";
import { BookOpen } from "lucide-react";
import { site } from "@/lib/site";

/** Header and footer for the public information pages (about, help, legal, account recovery). */
export function PublicShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <header className="border-b border-gray-100 bg-white">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-primary-600" />
            <span className="font-bold text-gray-900">{site.name}</span>
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/grades" className="hidden text-gray-600 hover:text-gray-900 sm:inline">
              Grades
            </Link>
            <Link href="/pricing" className="hidden text-gray-600 hover:text-gray-900 sm:inline">
              Pricing
            </Link>
            <Link href="/login" className="font-medium text-primary-600 hover:text-primary-700">
              Log in
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-gray-100 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-gray-500 sm:px-6">
          <p>
            © {new Date().getFullYear()} {site.name}
          </p>
          <nav className="flex flex-wrap gap-4">
            <Link href="/about" className="hover:text-gray-900">About</Link>
            <Link href="/help" className="hover:text-gray-900">Help</Link>
            <Link href="/contact" className="hover:text-gray-900">Contact</Link>
            <Link href="/privacy" className="hover:text-gray-900">Privacy</Link>
            <Link href="/terms" className="hover:text-gray-900">Terms</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}

/** Readable long-form layout for policy and information pages. */
export function Prose({ title, intro, children }: { title: string; intro?: string; children: ReactNode }) {
  return (
    <article className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
      {intro && <p className="mt-3 text-gray-600">{intro}</p>}
      <div className="mt-8 space-y-8 text-[15px] leading-relaxed text-gray-700 [&_h2]:mb-2 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-gray-900 [&_li]:ml-5 [&_li]:list-disc [&_ul]:space-y-1">
        {children}
      </div>
    </article>
  );
}
