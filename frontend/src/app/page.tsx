import type { Metadata } from "next";
import Link from "next/link";
import { BookOpen, Download, Star, Users, ChevronRight, Search } from "lucide-react";

export const metadata: Metadata = {
  title: "EduCore — Kenya's #1 CBC Education Platform",
  description:
    "Access CBC curriculum notes, past papers, worksheets and revision materials for all Kenya grades. Join thousands of students learning smarter.",
  openGraph: {
    title: "EduCore — Kenya's #1 CBC Education Platform",
    description: "Access CBC curriculum notes, past papers, worksheets and revision materials for all Kenya grades.",
    url: "/",
  },
  alternates: { canonical: "/" },
};

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="border-b border-gray-100 sticky top-0 bg-white/80 backdrop-blur-md z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <BookOpen className="h-7 w-7 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">EduCore</span>
            </Link>
            <div className="hidden md:flex items-center gap-6">
              <Link href="/subjects" className="text-gray-600 hover:text-gray-900 text-sm font-medium">Subjects</Link>
              <Link href="/resources" className="text-gray-600 hover:text-gray-900 text-sm font-medium">Resources</Link>
              <Link href="/pricing" className="text-gray-600 hover:text-gray-900 text-sm font-medium">Pricing</Link>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="text-sm font-medium text-gray-700 hover:text-primary-600"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-50 to-white py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <span className="inline-block bg-primary-100 text-primary-700 text-xs font-semibold px-3 py-1 rounded-full mb-4">
            CBC Curriculum Kenya
          </span>
          <h1 className="text-4xl md:text-6xl font-extrabold text-gray-900 mb-6 leading-tight">
            Learn Smarter.<br />
            <span className="text-primary-600">Score Higher.</span>
          </h1>
          <p className="text-lg text-gray-600 mb-10 max-w-2xl mx-auto">
            Access thousands of notes, past papers, worksheets and revision materials.
            For all grades from Grade 1 to Form 4.
          </p>
          {/* Search bar */}
          <div className="flex items-center max-w-xl mx-auto bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            <Search className="h-5 w-5 text-gray-400 ml-4 flex-shrink-0" />
            <input
              type="text"
              placeholder="Search subjects, topics, past papers..."
              className="flex-1 px-4 py-3 text-sm outline-none text-gray-900 placeholder-gray-400"
            />
            <Link
              href="/resources"
              className="bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold px-5 py-3 transition-colors"
            >
              Search
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 border-y border-gray-100">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { value: "10,000+", label: "Resources" },
            { value: "50,000+", label: "Students" },
            { value: "14", label: "Grade Levels" },
            { value: "20+", label: "Subjects" },
          ].map((stat) => (
            <div key={stat.label}>
              <p className="text-3xl font-extrabold text-primary-600">{stat.value}</p>
              <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Everything you need to excel
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: BookOpen,
                title: "Notes & Revision Guides",
                desc: "Comprehensive notes covering all CBC topics for every grade.",
              },
              {
                icon: Download,
                title: "Past Papers & Worksheets",
                desc: "Practice with real exam papers and targeted worksheets.",
              },
              {
                icon: Star,
                title: "Premium Resources",
                desc: "Unlock all premium content for less than the cost of a textbook.",
              },
            ].map((feat) => (
              <div key={feat.title} className="bg-gray-50 rounded-2xl p-6 hover:shadow-md transition-shadow">
                <div className="bg-primary-100 rounded-xl p-3 w-fit mb-4">
                  <feat.icon className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{feat.title}</h3>
                <p className="text-sm text-gray-500">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-primary-600 py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to start learning?
          </h2>
          <p className="text-primary-100 mb-8">
            Join 50,000+ students already learning on EduCore. Free to start.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-white text-primary-600 font-semibold px-8 py-3 rounded-xl hover:bg-primary-50 transition-colors"
          >
            Start for Free <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-12 px-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary-600" />
            <span className="font-bold text-gray-900">EduCore</span>
          </div>
          <p className="text-sm text-gray-400">
            &copy; {new Date().getFullYear()} EduCore. Built for Kenya.
          </p>
          <div className="flex gap-4">
            <Link href="/privacy" className="text-sm text-gray-400 hover:text-gray-600">Privacy</Link>
            <Link href="/terms" className="text-sm text-gray-400 hover:text-gray-600">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
