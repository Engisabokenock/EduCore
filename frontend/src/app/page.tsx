import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import {
  BookOpen,
  Search,
  ChevronRight,
  Star,
  Download,
  CheckCircle2,
  Lock,
  Award,
  Users,
  Clock,
  Smartphone,
  BarChart3,
  MessageCircle,
  ChevronDown,
  Menu,
  X,
} from "lucide-react";
import { serverApi } from "@/lib/server-api";
import type { Grade, Subject, Resource, Plan } from "@/types";

export const metadata: Metadata = {
  title: "EduCore — CBC Revision Made Simple for Kenyan Learners",
  description:
    "Download CBC exams, worksheets, notes & quizzes for Grades 1–7. Free resources + premium marking schemes. Trusted by 50,000+ Kenyan students and teachers.",
  openGraph: {
    title: "EduCore — CBC Revision Made Simple for Kenyan Learners",
    description:
      "Download CBC exams, worksheets, notes & quizzes for Grades 1–7. Free resources + premium marking schemes.",
    url: "/",
    type: "website",
  },
  alternates: { canonical: "/" },
};

/* ──────────────────────────────────────────────────────────────────────────────
   Types for inline data not worth separate serializer endpoints
   ────────────────────────────────────────────────────────────────────────────── */

const SUBJECTS: { name: string; icon: string; color: string; slug: string }[] = [
  { name: "Mathematics", icon: "🔢", color: "bg-blue-50 text-blue-700 border-blue-100", slug: "mathematics" },
  { name: "English", icon: "📖", color: "bg-purple-50 text-purple-700 border-purple-100", slug: "english" },
  { name: "Kiswahili", icon: "🗣️", color: "bg-green-50 text-green-700 border-green-100", slug: "kiswahili" },
  { name: "Science", icon: "🔬", color: "bg-cyan-50 text-cyan-700 border-cyan-100", slug: "science" },
  { name: "Social Studies", icon: "🌍", color: "bg-amber-50 text-amber-700 border-amber-100", slug: "social-studies" },
  { name: "CRE / IRE", icon: "🕌", color: "bg-teal-50 text-teal-700 border-teal-100", slug: "cre-ire" },
  { name: "Creative Arts", icon: "🎨", color: "bg-pink-50 text-pink-700 border-pink-100", slug: "creative-arts" },
  { name: "Design", icon: "✏️", color: "bg-orange-50 text-orange-700 border-orange-100", slug: "design" },
];

async function getPopularSubjects(): Promise<{ name: string; icon: string; color: string; slug: string }[]> {
  const data = await serverApi.getSubjects();
  if (Array.isArray(data) && data.length > 0) {
    return data.slice(0, 8).map((subject) => ({
      name: subject.name,
      icon: "📚",
      color: "bg-blue-50 text-blue-700 border-blue-100",
      slug: subject.slug,
    }));
  }
  return SUBJECTS;
}

const HOW_IT_WORKS = [
  { step: 1, title: "Select Grade", desc: "Choose from Grade 1 to Grade 7", icon: Award },
  { step: 2, title: "Choose Subject", desc: "Browse CBC subjects and topics", icon: BookOpen },
  { step: 3, title: "Download PDF", desc: "Get exams, notes and worksheets", icon: Download },
  { step: 4, title: "Start Learning", desc: "Practice and track progress", icon: BarChart3 },
];

const TESTIMONIALS = [
  {
    quote: "My child improved in Maths within 2 weeks. The worksheets are exactly what the teacher recommends.",
    name: "Grace W.",
    role: "Parent, Grade 4",
    initials: "GW",
  },
  {
    quote: "Best CBC resource platform I've used. The past papers save me hours of prep every term.",
    name: "Mr. Ochieng",
    role: "Teacher, Grade 5",
    initials: "MO",
  },
  {
    quote: "I love the quizzes! They make revision fun and I can see my marks go up.",
    name: "Amina K.",
    role: "Student, Grade 6",
    initials: "AK",
  },
];

function SkeletonCard() {
  return <div className="bg-gray-100 rounded-xl h-24 animate-pulse" />;
}

/* ──────────────────────────────────────────────────────────────────────────────
   Server components — data is fetched here, never hardcoded in the client
   ────────────────────────────────────────────────────────────────────────────── */

async function getGrades(): Promise<Grade[]> {
  const data = await serverApi.getGrades();
  if (!data || !Array.isArray(data)) return [];
  return data.slice(0, 7).map((g) => ({ ...g, subject_count: g.subject_count ?? 0 }));
}

async function getFeaturedResources(): Promise<Resource[]> {
  const data = await serverApi.getResources({
    is_published: "true",
    ordering: "-downloads_count",
    page_size: "6",
  });
  if (!data || !Array.isArray(data.results)) return [];
  return data.results.slice(0, 6);
}

async function getPlans(): Promise<Plan[]> {
  return (await serverApi.getPlans()) ?? [];
}

function GradeCard({ grade }: { grade: Grade }) {
  return (
    <Link
      href={`/grades/${grade.slug}`}
      className="group bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all p-5 text-center"
    >
      <div className="w-12 h-12 rounded-full bg-primary-50 text-primary-700 flex items-center justify-center text-lg font-bold mx-auto mb-3 group-hover:bg-primary-100">
        {grade.name.replace(/[^0-9]/g, "") || "?"}
      </div>
      <h3 className="font-semibold text-gray-900 text-sm">{grade.name}</h3>
      <p className="text-xs text-gray-400 mt-1">{grade.curriculum}</p>
    </Link>
  );
}

function SubjectCard({ subject }: { subject: { name: string; icon: string; color: string; slug: string } }) {
  return (
    <Link
      href={`/subjects/${subject.slug}`}
      className={`${subject.color} rounded-xl border p-4 hover:shadow-md transition-all group`}
    >
      <span className="text-2xl block mb-2">{subject.icon}</span>
      <h3 className="font-semibold text-sm group-hover:underline">{subject.name}</h3>
    </Link>
  );
}

function ResourceCard({ resource }: { resource: Resource }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-all p-4 flex flex-col">
      {resource.thumbnail && (
        <div className="relative w-full h-32 bg-gray-50 rounded-lg mb-3 overflow-hidden">
          <img
            src={resource.thumbnail}
            alt={resource.title}
            className="w-full h-full object-cover"
            loading="lazy"
          />
          {resource.is_premium && (
            <span className="absolute top-2 right-2 bg-accent-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
              PREMIUM
            </span>
          )}
        </div>
      )}
        <h4 className="font-semibold text-gray-900 text-sm line-clamp-2 leading-snug">{resource.title}</h4>
      <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
        <span className="flex items-center gap-1"><Download className="h-3 w-3" /> {resource.downloads_count ?? 0}</span>
        <span className="flex items-center gap-1"><Star className="h-3 w-3" /> 4.8</span>
      </div>

    </div>
  );
}

function PlanCard({ plan }: { plan: Plan }) {
  const tierLabel = plan.tier === "monthly" ? "mo" : plan.tier === "yearly" ? "yr" : plan.tier === "quarterly" ? "qr" : "wk";
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-lg transition-all p-6 flex flex-col">
      <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
      {plan.is_featured && (
        <span className="inline-block mt-1 text-[10px] font-bold bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full">
          MOST POPULAR
        </span>
      )}
      <p className="text-sm text-gray-500 mt-2 flex-1">{plan.name}</p>
      <div className="mt-4">
        <span className="text-2xl font-extrabold text-gray-900">KES {plan.price}</span>
        <span className="text-sm text-gray-400">/{tierLabel}</span>
      </div>
      <ul className="mt-4 space-y-2">
        {(plan.features ?? []).slice(0, 5).map((f) => (
          <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
            <CheckCircle2 className="h-4 w-4 text-success-600 mt-0.5 flex-shrink-0" />
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <Link
        href={`/checkout?plan=${plan.id}`}
        className={`mt-6 text-center block w-full py-2.5 rounded-lg text-sm font-semibold transition-colors ${
          plan.is_featured
            ? "bg-primary-800 text-white hover:bg-primary-900"
            : "bg-primary-50 text-primary-800 hover:bg-primary-100"
        }`}
      >
        Get Started
      </Link>
    </div>
  );
}

export default async function HomePage() {
  const [grades, popularSubjects, resources, plans] = await Promise.all([
    getGrades(),
    getPopularSubjects(),
    getFeaturedResources(),
    getPlans(),
  ]);

  const sortedPlans = [...plans].sort((a, b) => a.sort_order - b.sort_order);

  return (
    <div className="min-h-screen bg-background">
      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 1 — Navbar                                                                 │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <nav className="bg-white shadow-sm sticky top-0 z-50 border-b border-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" aria-label="EduCore home">
              <Image
                src="/logos/educore-logo.svg"
                alt="EduCore — CBC Learning Made Simple"
                width={160}
                height={42}
                priority
                className="h-10 w-auto"
              />
            </Link>
            <div className="hidden md:flex items-center gap-6">
              <Link href="/grades" className="text-sm font-medium text-gray-600 hover:text-primary-800">
                Grades
              </Link>
              <Link href="/subjects" className="text-sm font-medium text-gray-600 hover:text-primary-800">
                Subjects
              </Link>
              <Link href="/resources" className="text-sm font-medium text-gray-600 hover:text-primary-800">
                Free Papers
              </Link>
              <Link href="/pricing" className="text-sm font-medium text-gray-600 hover:text-primary-800">
                Premium
              </Link>
              <Link href="/pricing" className="text-sm font-medium text-gray-600 hover:text-primary-800">
                Pricing
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="text-sm font-semibold text-gray-700 hover:text-primary-800 hidden sm:block"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="bg-accent-500 hover:bg-accent-600 text-white text-sm font-bold px-4 py-2 rounded-lg transition-colors shadow-sm"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 2 — Hero Section                                                           │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-800 via-primary-700 to-success-600 text-white">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj48Y2lyY2xlIGN4PSIzMCIgY3k9IjMwIiByPSIxIiBmaWxsPSJyZ2JhKDAsIDIwOCwgMTU1LCAwLjEpIi8+PC9zdmc+')] opacity-30" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-28">
          <div className="max-w-4xl mx-auto text-center">
            <span className="inline-block bg-white/10 backdrop-blur-sm text-white text-xs font-bold px-3 py-1 rounded-full mb-6 border border-white/10">
              CBC Curriculum Kenya
            </span>
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold leading-[1.08] mb-6">
              CBC Revision Made Simple
              <br />
              <span className="text-success-200">for Every Learner in Kenya</span>
            </h1>
            <p className="text-lg md:text-xl text-white/85 max-w-2xl mx-auto mb-10 leading-relaxed">
              Download exams, worksheets, notes, and quizzes for Grades 1–7.
              Aligned to CBC. Trusted by teachers and parents across Kenya.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                href="/grades"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-white text-primary-800 hover:bg-primary-50 font-bold px-6 py-3.5 rounded-xl transition-colors shadow-lg"
              >
                Browse Grades <ChevronRight className="h-4 w-4" />
              </Link>
              <Link
                href="/resources"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-accent-500 hover:bg-accent-600 text-white font-bold px-6 py-3.5 rounded-xl transition-colors shadow-lg"
              >
                <Search className="h-4 w-4" /> Start Learning
              </Link>
            </div>
          </div>

          <div className="mt-14 max-w-2xl mx-auto">
            <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-2 flex shadow-2xl">
              <div className="flex-1 flex items-center gap-2 bg-white rounded-xl px-4">
                <Search className="h-5 w-5 text-gray-400 flex-shrink-0" />
                <input
                  type="text"
                  placeholder="Grade 5 Maths Fractions..."
                  className="w-full py-3 text-sm text-gray-900 placeholder-gray-400 outline-none bg-transparent"
                />
              </div>
              <Link
                href="/search"
                className="m-1 px-5 py-2.5 bg-primary-800 hover:bg-primary-900 text-white text-sm font-bold rounded-xl transition-colors"
              >
                Search
              </Link>
            </div>
            <div className="flex flex-wrap justify-center gap-2 mt-3 text-[11px] text-white/70">
              {["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7"].map((g) => (
                <Link key={g} href={`/grades/${g.toLowerCase().replace(" ", "-")}`} className="hover:text-white underline-offset-2 hover:underline">
                  {g}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 3 — Search Quick Access                                                    │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <section className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Find resources fast</h2>
              <p className="text-sm text-gray-500">Filter by grade, subject, or topic</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {["All", "Exams", "Notes", "Worksheets", "Quizzes"].map((f) => (
                <span
                  key={f}
                  className="px-3 py-1.5 rounded-full text-xs font-semibold bg-gray-50 text-gray-600 border border-gray-100"
                >
                  {f}
                </span>
              ))}
              <Link
                href="/search"
                className="px-4 py-1.5 rounded-full text-xs font-bold bg-primary-800 text-white hover:bg-primary-900 transition-colors"
              >
                Advanced <ChevronDown className="h-3 w-3 inline" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 4 — Grade Selection Grid                                                    │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <section className="py-14 px-4 sm:px-6 lg:px-8 bg-background" id="grades">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-extrabold text-gray-900">
              Select Your Grade
            </h2>
            <p className="mt-2 text-sm text-gray-500">All CBC and 8-4-4 resources in one place</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 md:gap-4">
            {grades.length > 0 ? grades.map((g) => <GradeCard key={g.id} grade={g} />) : Array.from({ length: 7 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        </div>
      </section>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 5 — Subjects Section                                                        │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <section className="py-14 bg-white border-t border-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-extrabold text-gray-900">Popular Subjects</h2>
            <p className="mt-2 text-sm text-gray-500">Cover every area of the CBC curriculum</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 md:gap-4">
            {popularSubjects.map((s) => (
              <SubjectCard key={s.slug} subject={s} />
            ))}
          </div>
        </div>
      </section>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 6 — Featured Resources                                                      │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <section className="py-14 bg-background" id="resources">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-end justify-between mb-8">
            <div>
              <h2 className="text-2xl md:text-3xl font-extrabold text-gray-900">Latest & Trending</h2>
              <p className="mt-2 text-sm text-gray-500">Most downloaded by Kenyan students</p>
            </div>
            <Link href="/resources" className="hidden sm:inline-flex items-center text-sm font-bold text-primary-800 hover:text-primary-900">
              View all <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {resources.length > 0 ? resources.map((r) => <ResourceCard key={r.id} resource={r} />) : Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
          <div className="mt-6 text-center sm:hidden">
            <Link href="/resources" className="inline-flex items-center gap-1 text-sm font-bold text-primary-800">
              View all <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 7 — Free vs Premium                                                         │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <section className="py-14 bg-white" id="pricing">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-extrabold text-gray-900">Free vs Premium</h2>
            <p className="mt-2 text-sm text-gray-500">Start free. Upgrade when you’re ready to ace exams.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-gray-100 bg-background p-6 md:p-8">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-primary-50 text-primary-700">
                  <BookOpen className="h-4 w-4" />
                </span>
                <h3 className="text-lg font-bold text-gray-900">Free</h3>
              </div>
              <p className="mt-3 text-sm text-gray-500">Enough to practice and stay ahead.</p>
              <ul className="mt-6 space-y-3">
                {["Sample papers and worksheets", "Basic quizzes per topic", "Grade & subject browsing", "Limited downloads / day"].map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-gray-600">
                    <CheckCircle2 className="h-4 w-4 text-success-600 mt-0.5 flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-2xl border-2 border-accent-500 bg-white p-6 md:p-8 shadow-lg relative">
              <span className="absolute -top-3 right-6 bg-accent-500 text-white text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wide">
                Recommended
              </span>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-accent-50 text-accent-600">
                  <Award className="h-4 w-4" />
                </span>
                <h3 className="text-lg font-bold text-gray-900">Premium</h3>
              </div>
              <p className="mt-3 text-sm text-gray-500">Everything you need to score an A.</p>
              <ul className="mt-6 space-y-3">
                {["All past papers with answers", "Marking schemes (optional extra)", "Topic bundles + revision sets", "Unlimited downloads", "Early access to new exams", "Priority support"].map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="h-4 w-4 text-accent-500 mt-0.5 flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <Link
                href="/pricing"
                className="mt-8 block w-full text-center bg-accent-500 hover:bg-accent-600 text-white font-bold py-3 rounded-xl transition-colors"
              >
                Unlock Premium — Pay with M-Pesa
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 8 — How It Works                                                           │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <section className="py-14 bg-background border-t border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-extrabold text-gray-900">How It Works</h2>
            <p className="mt-2 text-sm text-gray-500">From signup to your first download in 60 seconds</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {HOW_IT_WORKS.map(({ step, title, desc, icon: Icon }) => (
              <div key={step} className="bg-white rounded-xl border border-gray-100 p-6 text-center shadow-sm hover:shadow-md transition-shadow">
                <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-primary-800 text-white text-sm font-extrabold mb-3">
                  {step}
                </span>
                <span className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 text-primary-800 mb-2">
                  <Icon className="h-5 w-5" />
                </span>
                <h3 className="text-sm font-bold text-gray-900">{title}</h3>
                <p className="text-xs text-gray-500 mt-1">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 9 — Testimonials                                                           │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <section className="py-14 bg-white border-t border-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-extrabold text-gray-900">What Our Community Says</h2>
            <p className="mt-2 text-sm text-gray-500">Real feedback from students, teachers and parents</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t) => (
              <div key={t.name} className="rounded-xl border border-gray-100 bg-background p-6 shadow-sm">
                <div className="flex gap-1 text-accent-500">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-current" />
                  ))}
                </div>
                <p className="mt-3 text-sm text-gray-700 leading-relaxed">“{t.quote}”</p>
                <div className="mt-4 flex items-center gap-3">
                  <span className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-primary-100 text-primary-800 text-xs font-bold">
                    {t.initials}
                  </span>
                  <div>
                    <p className="text-sm font-bold text-gray-900">{t.name}</p>
                    <p className="text-xs text-gray-500">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 10 — Subscription CTA                                                      │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <section className="py-14 bg-gradient-to-br from-primary-800 to-primary-900 text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-10 items-center">
            <div>
              <h2 className="text-2xl md:text-3xl font-extrabold leading-snug">
                Get Weekly CBC Revision Updates
              </h2>
              <p className="mt-3 text-sm text-white/75">
                Join 50,000+ learners. New resources every week — straight to your inbox or WhatsApp.
              </p>
              <div className="mt-5 flex flex-col sm:flex-row gap-2">
                <input
                  type="email"
                  placeholder="you@example.com"
                  className="flex-1 px-4 py-3 rounded-xl text-sm text-gray-900 placeholder-gray-400 bg-white/95 focus:bg-white"
                />
                <button
                  type="button"
                  className="bg-accent-500 hover:bg-accent-600 text-white font-bold px-5 py-3 rounded-xl transition-colors"
                >
                  Subscribe
                </button>
              </div>
              <button
                type="button"
                className="mt-3 inline-flex items-center gap-2 text-xs text-white/80 hover:text-white underline-offset-2 hover:underline"
              >
                <MessageCircle className="h-3 w-3" /> Or join our WhatsApp group
              </button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                <Users className="h-6 w-6 text-white/90 mb-2" />
                <p className="text-2xl font-extrabold">50k+</p>
                <p className="text-xs text-white/70 mt-1">Students</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                <Download className="h-6 w-6 text-white/90 mb-2" />
                <p className="text-2xl font-extrabold">10k+</p>
                <p className="text-xs text-white/70 mt-1">Resources</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                <Clock className="h-6 w-6 text-white/90 mb-2" />
                <p className="text-2xl font-extrabold">24/7</p>
                <p className="text-xs text-white/70 mt-1">Access</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                <Smartphone className="h-6 w-6 text-white/90 mb-2" />
                <p className="text-2xl font-extrabold">Mobile</p>
                <p className="text-xs text-white/70 mt-1">First design</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/*
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │ 11 — Footer                                                                 │
      └─────────────────────────────────────────────────────────────────────────────
      */}
      <footer className="bg-dark text-white/70 py-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-10">
            <div>
              <div className="mb-4">
              <Image
                src="/logos/educore-logo-white.svg"
                alt="EduCore"
                width={148}
                height={38}
                className="h-9 w-auto"
              />
            </div>
              <p className="text-sm text-white/60 leading-relaxed">
                Kenya’s trusted CBC revision platform. Built for learners, teachers and parents.
              </p>
            </div>
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">Resources</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/resources" className="hover:text-white">Past Papers</Link></li>
                <li><Link href="/resources" className="hover:text-white">Worksheets</Link></li>
                <li><Link href="/resources" className="hover:text-white">Notes & Quizzes</Link></li>
                <li><Link href="/pricing" className="hover:text-white">Premium Access</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/about" className="hover:text-white">About</Link></li>
                <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
                <li><Link href="/privacy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link href="/terms" className="hover:text-white">Terms of Service</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">Support</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/help" className="hover:text-white">Help Center</Link></li>
                <li><Link href="/contact" className="hover:text-white">M-Pesa Support</Link></li>
                <li><Link href="/contact" className="hover:text-white">Payment Issues</Link></li>
                <li><a href="https://wa.me/254700000000" target="_blank" rel="noopener noreferrer" className="hover:text-white flex items-center gap-1">
                    <MessageCircle className="h-3 w-3" /> WhatsApp us
                </a></li>
              </ul>
            </div>
          </div>
          <div className="mt-10 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-white/50">© {new Date().getFullYear()} EduCore. Built for Kenya.</p>
            <div className="flex gap-4 text-xs">
              <Link href="/privacy" className="hover:text-white">Privacy</Link>
              <Link href="/terms" className="hover:text-white">Terms</Link>
              <Link href="/sitemap.xml" className="hover:text-white">Sitemap</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
