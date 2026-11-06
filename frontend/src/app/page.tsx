import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  Download,
  FileText,
  GraduationCap,
  Heart,
  Lock,
  MessageCircle,
  Phone,
  Search,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import { HomeHeader, MobileSignupBar } from "@/components/home/HomeHeader";
import { serverApi } from "@/lib/server-api";
import { site, whatsappLink } from "@/lib/site";
import type { Grade, Plan, Resource } from "@/types";

export const metadata: Metadata = {
  title: "EduCore — CBC Revision Made Simple for Kenyan Learners",
  description:
    "CBC exams, worksheets, notes and quizzes for Kenyan learners. Start free, follow your child's progress, and unlock premium papers with M-Pesa.",
  openGraph: {
    title: "EduCore — CBC Revision Made Simple for Kenyan Learners",
    description: "CBC exams, worksheets, notes and quizzes. Start free and unlock premium with M-Pesa.",
    url: "/",
    type: "website",
  },
  alternates: { canonical: "/" },
};

/* ── Static content ──────────────────────────────────────────────────────────── */

type SubjectTile = { name: string; icon: string; tone: string; slug: string };

const SUBJECT_TONES = [
  "from-blue-50 to-blue-100/60 text-blue-800 ring-blue-100",
  "from-violet-50 to-violet-100/60 text-violet-800 ring-violet-100",
  "from-emerald-50 to-emerald-100/60 text-emerald-800 ring-emerald-100",
  "from-cyan-50 to-cyan-100/60 text-cyan-800 ring-cyan-100",
  "from-amber-50 to-amber-100/60 text-amber-800 ring-amber-100",
  "from-teal-50 to-teal-100/60 text-teal-800 ring-teal-100",
  "from-pink-50 to-pink-100/60 text-pink-800 ring-pink-100",
  "from-orange-50 to-orange-100/60 text-orange-800 ring-orange-100",
];

const SUBJECT_ICONS: [string, string][] = [
  ["math", "🔢"],
  ["english", "📖"],
  ["kiswahili", "🗣️"],
  ["science", "🔬"],
  ["social", "🌍"],
  ["religious", "🕊️"],
  ["cre", "🕊️"],
  ["creative", "🎨"],
  ["art", "🎨"],
  ["agricult", "🌱"],
  ["home", "🏠"],
  ["computer", "💻"],
  ["technical", "⚙️"],
  ["physical", "⚽"],
];

function iconFor(name: string): string {
  const key = name.toLowerCase();
  return SUBJECT_ICONS.find(([k]) => key.includes(k))?.[1] ?? "📚";
}

const FALLBACK_SUBJECTS: SubjectTile[] = [
  ["Mathematics", "mathematics"],
  ["English", "english"],
  ["Kiswahili", "kiswahili"],
  ["Science & Technology", "science-and-technology"],
  ["Social Studies", "social-studies"],
  ["Religious Education", "religious-education"],
  ["Creative Arts", "creative-arts"],
  ["Agriculture", "agriculture"],
].map(([name, slug], i) => ({ name, slug, icon: iconFor(name), tone: SUBJECT_TONES[i % SUBJECT_TONES.length] }));

const RESOURCE_TYPES = [
  { type: "past_paper", label: "Past Papers", icon: FileText },
  { type: "exam", label: "Exams", icon: ClipboardCheck },
  { type: "worksheet", label: "Worksheets", icon: BookOpen },
  { type: "lesson_note", label: "Lesson Notes", icon: GraduationCap },
  { type: "marking_scheme", label: "Marking Schemes", icon: CheckCircle2 },
];

const FEATURES = [
  {
    icon: BookOpen,
    title: "Everything CBC, in one place",
    desc: "Exams, worksheets, lesson notes and marking schemes organised by grade, subject and topic.",
  },
  {
    icon: Zap,
    title: "Practice that sticks",
    desc: "Topic quizzes give instant feedback, so learners know exactly what to revise next.",
  },
  {
    icon: BarChart3,
    title: "See real progress",
    desc: "Parents follow scores and activity for each child, all from one account.",
  },
  {
    icon: Smartphone,
    title: "Made for phones",
    desc: "Fast on any smartphone and light on data. Download a PDF once, then print or study offline.",
  },
  {
    icon: Lock,
    title: "Pay simply with M-Pesa",
    desc: "Unlock premium in seconds with an M-Pesa prompt on your phone. No card needed.",
  },
  {
    icon: ShieldCheck,
    title: "Safe for children",
    desc: "No ads and no strangers. Teachers are vetted and approved before they can publish.",
  },
];

const STEPS = [
  { title: "Create a free account", desc: "Sign up in under a minute as a learner or a parent." },
  { title: "Pick a grade and subject", desc: "Browse topics the way your class teacher teaches them." },
  { title: "Practise and download", desc: "Take quizzes, download papers and track every result." },
];

const FAQ = [
  {
    q: "Is EduCore really free?",
    a: "Yes. A free account gives you sample papers, worksheets, topic quizzes and full browsing by grade and subject. Premium unlocks every paper, marking schemes and unlimited downloads.",
  },
  {
    q: "How do I pay for premium?",
    a: "With M-Pesa. Choose a plan, enter your Safaricom number and approve the prompt on your phone. Premium activates as soon as the payment is confirmed.",
  },
  {
    q: "Can a parent follow more than one child?",
    a: "Yes. A parent account can link several learners and see each child's quiz results and activity.",
  },
  {
    q: "Does it follow the Kenyan CBC curriculum?",
    a: "Yes. Resources are organised by CBC grade, learning area and strand, so what your child practises matches what they learn in class.",
  },
  {
    q: "I paid but premium is not active. What do I do?",
    a: `Refresh your dashboard first, since M-Pesa confirmations are sometimes delayed. If it is still not active, WhatsApp or call us on ${site.supportPhone} with your M-Pesa code.`,
  },
];

/* ── Data (every call degrades gracefully if the API is unavailable) ─────────── */

async function getGrades(): Promise<Grade[]> {
  const data = await serverApi.getGrades();
  return Array.isArray(data) ? data.slice(0, 12) : [];
}

async function getSubjects(): Promise<SubjectTile[]> {
  const data = await serverApi.getSubjects();
  if (!Array.isArray(data) || data.length === 0) return FALLBACK_SUBJECTS;
  // Subject slugs repeat across grades; show each learning area once.
  const seen = new Set<string>();
  const unique = data.filter((s) => {
    if (seen.has(s.slug)) return false;
    seen.add(s.slug);
    return true;
  });
  return unique.slice(0, 8).map((s, i) => ({
    name: s.name,
    slug: s.slug,
    icon: iconFor(s.name),
    tone: SUBJECT_TONES[i % SUBJECT_TONES.length],
  }));
}

async function getFeaturedResources(): Promise<Resource[]> {
  const data = await serverApi.getResources({ is_published: "true", ordering: "-downloads_count", page_size: "6" });
  return data && Array.isArray(data.results) ? data.results.slice(0, 6) : [];
}

async function getPlans(): Promise<Plan[]> {
  const plans = (await serverApi.getPlans()) ?? [];
  return [...plans].sort((a, b) => a.sort_order - b.sort_order);
}

/* ── Small pieces ────────────────────────────────────────────────────────────── */

function SectionHeading({ eyebrow, title, intro }: { eyebrow: string; title: string; intro?: string }) {
  return (
    <div className="mx-auto mb-12 max-w-2xl text-center">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-accent-600">{eyebrow}</p>
      <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-gray-900 md:text-4xl">{title}</h2>
      {intro && <p className="mt-4 text-base leading-relaxed text-gray-500">{intro}</p>}
    </div>
  );
}

function gradeBadge(name: string): string {
  return name.replace(/[^0-9]/g, "") || name.slice(0, 3).toUpperCase();
}

/** Product preview built from real UI pieces, so it always matches the brand. */
function HeroPreview() {
  return (
    <div className="relative mx-auto w-full max-w-md lg:max-w-none" aria-hidden="true">
      <div className="absolute -inset-6 rounded-[2rem] bg-gradient-to-tr from-accent-400/30 via-white/10 to-success-500/30 blur-2xl" />
      <div className="relative rounded-3xl border border-white/20 bg-white p-5 shadow-2xl shadow-primary-950/40">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-gray-400">Grade 6 · Mathematics</p>
            <p className="mt-0.5 text-base font-bold text-gray-900">Fractions &amp; Decimals</p>
          </div>
          <span className="rounded-full bg-success-50 px-2.5 py-1 text-[11px] font-bold text-success-700">CBC</span>
        </div>

        <div className="mt-5 rounded-2xl bg-gray-50 p-4">
          <p className="text-sm font-semibold text-gray-800">What is ¾ written as a decimal?</p>
          <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
            {["0.34", "0.75", "0.43", "7.5"].map((o) => (
              <div
                key={o}
                className={`rounded-xl border px-3 py-2 font-medium ${
                  o === "0.75"
                    ? "border-success-500 bg-success-50 text-success-700"
                    : "border-gray-200 bg-white text-gray-600"
                }`}
              >
                {o} {o === "0.75" && "✓"}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-gray-700">Topic mastery</span>
            <span className="font-bold text-primary-700">82%</span>
          </div>
          <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-gray-100">
            <div className="h-full w-[82%] rounded-full bg-gradient-to-r from-primary-600 to-success-500" />
          </div>
        </div>

        <div className="mt-5 flex items-center gap-3 rounded-2xl border border-gray-100 p-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-50 text-red-600">
            <FileText className="h-5 w-5" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-gray-900">End Term Exam — Grade 6</p>
            <p className="text-xs text-gray-400">PDF · with marking scheme</p>
          </div>
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-800 text-white">
            <Download className="h-4 w-4" />
          </span>
        </div>
      </div>

      <div className="absolute -left-4 top-10 hidden rounded-2xl bg-white px-4 py-3 shadow-xl sm:block lg:-left-10">
        <p className="text-[11px] font-medium text-gray-400">Quiz score</p>
        <p className="text-lg font-extrabold text-success-600">9 / 10 🎉</p>
      </div>
      <div className="absolute -bottom-5 -right-3 hidden items-center gap-2 rounded-2xl bg-white px-4 py-3 shadow-xl sm:flex lg:-right-8">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-green-600 text-xs font-extrabold text-white">
          M
        </span>
        <div>
          <p className="text-[11px] font-medium text-gray-400">M-Pesa</p>
          <p className="text-sm font-bold text-gray-900">Premium active</p>
        </div>
      </div>
    </div>
  );
}

function ResourceCard({ resource }: { resource: Resource }) {
  return (
    <Link
      href={`/resources/${resource.slug}`}
      className="group flex flex-col rounded-2xl border border-gray-100 bg-white p-5 shadow-sm transition-all hover:-translate-y-1 hover:border-primary-100 hover:shadow-xl"
    >
      <div className="flex items-start justify-between gap-3">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-primary-700">
          <FileText className="h-5 w-5" />
        </span>
        {resource.is_premium ? (
          <span className="rounded-full bg-accent-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-accent-700">
            Premium
          </span>
        ) : (
          <span className="rounded-full bg-success-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-success-700">
            Free
          </span>
        )}
      </div>
      <h3 className="mt-4 line-clamp-2 font-semibold leading-snug text-gray-900 group-hover:text-primary-800">
        {resource.title}
      </h3>
      <div className="mt-auto flex items-center justify-between pt-4 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <Download className="h-3.5 w-3.5" /> {(resource.downloads_count ?? 0).toLocaleString()} downloads
        </span>
        <ArrowRight className="h-4 w-4 text-primary-600 opacity-0 transition-opacity group-hover:opacity-100" />
      </div>
    </Link>
  );
}

const PERIOD: Record<string, string> = { weekly: "week", monthly: "month", quarterly: "quarter", yearly: "year" };

function PlanCard({ plan }: { plan: Plan }) {
  const featured = plan.is_featured;
  return (
    <div
      className={`relative flex flex-col rounded-3xl p-7 transition-all ${
        featured
          ? "bg-gradient-to-b from-primary-800 to-primary-950 text-white shadow-2xl shadow-primary-900/30"
          : "border border-gray-200 bg-white shadow-sm hover:shadow-lg"
      }`}
    >
      {featured && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-accent-500 px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-white shadow">
          Most popular
        </span>
      )}
      <h3 className={`text-lg font-bold ${featured ? "text-white" : "text-gray-900"}`}>{plan.name}</h3>
      <p className="mt-4">
        <span className="text-4xl font-extrabold tracking-tight">KES {Number(plan.price).toLocaleString()}</span>
        <span className={`text-sm ${featured ? "text-white/70" : "text-gray-400"}`}> / {PERIOD[plan.tier] ?? plan.tier}</span>
      </p>
      <ul className="mt-6 flex-1 space-y-3">
        {(plan.features ?? []).slice(0, 6).map((f) => (
          <li key={f} className={`flex items-start gap-2.5 text-sm ${featured ? "text-white/90" : "text-gray-600"}`}>
            <CheckCircle2 className={`mt-0.5 h-4 w-4 shrink-0 ${featured ? "text-accent-400" : "text-success-600"}`} />
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <Link
        href={`/register?redirect=${encodeURIComponent(`/checkout?plan=${plan.id}`)}`}
        className={`mt-8 block rounded-xl py-3 text-center text-sm font-bold transition-colors ${
          featured ? "bg-accent-500 text-white hover:bg-accent-600" : "bg-primary-50 text-primary-800 hover:bg-primary-100"
        }`}
      >
        Choose {plan.name}
      </Link>
    </div>
  );
}

function CheckList({ items, iconClass, textClass }: { items: string[]; iconClass: string; textClass: string }) {
  return (
    <ul className={`space-y-3 text-sm ${textClass}`}>
      {items.map((t) => (
        <li key={t} className="flex items-start gap-2">
          <CheckCircle2 className={`mt-0.5 h-4 w-4 shrink-0 ${iconClass}`} /> {t}
        </li>
      ))}
    </ul>
  );
}

/* ── Page ────────────────────────────────────────────────────────────────────── */

export default async function HomePage() {
  const [grades, subjects, resources, plans] = await Promise.all([
    getGrades(),
    getSubjects(),
    getFeaturedResources(),
    getPlans(),
  ]);

  return (
    <div className="min-h-screen bg-white pb-20 sm:pb-0">
      <HomeHeader />

      {/* Hero */}
      <section className="relative overflow-hidden bg-primary-950 text-white">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(59,130,246,0.45),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(22,163,74,0.35),transparent_50%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_at_center,black_40%,transparent_75%)]" />

        <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-4 pb-20 pt-14 sm:px-6 md:pt-20 lg:grid-cols-[1.1fr_1fr] lg:gap-12 lg:px-8 lg:pb-28 lg:pt-24">
          <div className="text-center lg:text-left">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3.5 py-1.5 text-xs font-semibold backdrop-blur">
              <Sparkles className="h-3.5 w-3.5 text-accent-400" /> Built for Kenya&apos;s CBC curriculum
            </span>
            <h1 className="mt-6 text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl lg:text-6xl">
              Revise smarter.
              <br />
              <span className="bg-gradient-to-r from-accent-400 via-amber-300 to-success-500 bg-clip-text text-transparent">
                Score higher.
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-blue-100/85 lg:mx-0">
              CBC exams, worksheets, notes and quizzes in one place, with progress parents can actually see. Start
              free today.
            </p>

            <div className="mt-9 flex flex-col items-center gap-3 sm:flex-row sm:justify-center lg:justify-start">
              <Link
                href="/register"
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-accent-500 px-7 py-4 text-base font-bold text-white shadow-lg shadow-accent-500/30 transition-all hover:-translate-y-0.5 hover:bg-accent-600 sm:w-auto"
              >
                Create free account <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/login"
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/10 px-7 py-4 text-base font-semibold text-white backdrop-blur transition-colors hover:bg-white/20 sm:w-auto"
              >
                Log in
              </Link>
            </div>

            <form action="/search" method="get" role="search" className="mx-auto mt-8 max-w-xl lg:mx-0">
              <label htmlFor="hero-search" className="sr-only">
                Search resources
              </label>
              <div className="flex items-center gap-2 rounded-2xl bg-white p-1.5 shadow-xl">
                <Search className="ml-3 h-5 w-5 shrink-0 text-gray-400" />
                <input
                  id="hero-search"
                  name="q"
                  type="search"
                  required
                  placeholder="Try “Grade 5 fractions”"
                  className="min-w-0 flex-1 bg-transparent py-2.5 text-sm text-gray-900 placeholder-gray-400 outline-none"
                />
                <button
                  type="submit"
                  className="rounded-xl bg-primary-800 px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-primary-900"
                >
                  Search
                </button>
              </div>
            </form>

            <ul className="mt-8 flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-blue-100/80 lg:justify-start">
              {["Free to start", "No card needed", "Pay with M-Pesa"].map((t) => (
                <li key={t} className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-success-500" /> {t}
                </li>
              ))}
            </ul>
          </div>

          <HeroPreview />
        </div>
      </section>

      {/* Resource types */}
      <section className="border-b border-gray-100 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex gap-3 overflow-x-auto pb-1 [scrollbar-width:none] md:justify-center">
            {RESOURCE_TYPES.map(({ type, label, icon: Icon }) => (
              <Link
                key={type}
                href={`/resources?type=${type}`}
                className="inline-flex shrink-0 items-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition-colors hover:border-primary-200 hover:bg-primary-50 hover:text-primary-800"
              >
                <Icon className="h-4 w-4 text-primary-600" /> {label}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Grades */}
      <section id="grades" className="bg-background py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <SectionHeading
            eyebrow="Start here"
            title="Choose your grade"
            intro="Every resource is sorted by grade, so you find the right level in one tap."
          />
          {grades.length > 0 ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
              {grades.map((g) => (
                <Link
                  key={g.id}
                  href={`/grades/${g.slug}`}
                  className="group rounded-2xl border border-gray-100 bg-white p-5 text-center shadow-sm transition-all hover:-translate-y-1 hover:border-primary-200 hover:shadow-lg"
                >
                  <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-600 to-primary-800 text-xl font-extrabold text-white shadow-md shadow-primary-600/30 transition-transform group-hover:scale-105">
                    {gradeBadge(g.name)}
                  </span>
                  <p className="mt-3 font-semibold text-gray-900">{g.name}</p>
                  {g.curriculum && <p className="text-xs uppercase tracking-wide text-gray-400">{g.curriculum}</p>}
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center">
              <Link
                href="/grades"
                className="inline-flex items-center gap-2 rounded-xl bg-primary-800 px-6 py-3 font-semibold text-white hover:bg-primary-900"
              >
                See all grades <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Subjects */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <SectionHeading eyebrow="Learning areas" title="Every CBC subject covered" />
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {subjects.map((s) => (
              <Link
                key={s.slug}
                href={`/subjects/${s.slug}`}
                className={`group flex items-center gap-3 rounded-2xl bg-gradient-to-br p-5 ring-1 transition-all hover:-translate-y-1 hover:shadow-lg ${s.tone}`}
              >
                <span className="text-3xl transition-transform group-hover:scale-110">{s.icon}</span>
                <span className="font-semibold leading-tight">{s.name}</span>
              </Link>
            ))}
          </div>
          <div className="mt-8 text-center">
            <Link href="/subjects" className="inline-flex items-center gap-1 text-sm font-bold text-primary-800 hover:text-primary-900">
              View all subjects <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="bg-background py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <SectionHeading
            eyebrow="Why EduCore"
            title="Everything a learner needs to do well"
            intro="Designed with Kenyan families in mind: simple, affordable and focused on results."
          />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="rounded-2xl border border-gray-100 bg-white p-7 shadow-sm transition-shadow hover:shadow-lg">
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-50 text-primary-700">
                  <Icon className="h-6 w-6" />
                </span>
                <h3 className="mt-5 text-lg font-bold text-gray-900">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Learners & parents */}
      <section className="bg-white py-20">
        <div className="mx-auto grid max-w-7xl gap-6 px-4 sm:px-6 md:grid-cols-2 lg:px-8">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary-700 to-primary-900 p-8 text-white md:p-10">
            <GraduationCap className="absolute -bottom-6 -right-6 h-40 w-40 text-white/10" />
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-200">For learners</p>
            <h3 className="mt-3 text-2xl font-extrabold md:text-3xl">Practise, get instant marks, improve.</h3>
            <div className="mt-6">
              <CheckList
                items={["Quizzes for every topic", "Past papers and exams to download", "Track your scores over time"]}
                iconClass="text-accent-400"
                textClass="text-blue-50"
              />
            </div>
            <Link
              href="/register"
              className="relative mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-primary-800 hover:bg-blue-50"
            >
              Sign up as a learner <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-success-600 to-emerald-800 p-8 text-white md:p-10">
            <Heart className="absolute -bottom-6 -right-6 h-40 w-40 text-white/10" />
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-100">For parents</p>
            <h3 className="mt-3 text-2xl font-extrabold md:text-3xl">Know how your child is really doing.</h3>
            <div className="mt-6">
              <CheckList
                items={["Link all your children to one account", "See quiz results and activity", "Print papers for weekend revision"]}
                iconClass="text-amber-300"
                textClass="text-emerald-50"
              />
            </div>
            <Link
              href="/register"
              className="relative mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-success-700 hover:bg-emerald-50"
            >
              Sign up as a parent <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Popular resources (hidden until there is real content) */}
      {resources.length > 0 && (
        <section id="resources" className="bg-background py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-10 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-end">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-accent-600">Popular now</p>
                <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-gray-900 md:text-4xl">
                  Most downloaded resources
                </h2>
              </div>
              <Link href="/resources" className="inline-flex items-center gap-1 text-sm font-bold text-primary-800 hover:text-primary-900">
                Browse all <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {resources.map((r) => (
                <ResourceCard key={r.id} resource={r} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* How it works */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <SectionHeading eyebrow="Get started" title="Up and running in three steps" />
          <ol className="grid gap-10 md:grid-cols-3">
            {STEPS.map((s, i) => (
              <li key={s.title} className="text-center">
                <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-accent-500 text-xl font-extrabold text-white shadow-lg shadow-accent-500/30">
                  {i + 1}
                </span>
                <h3 className="mt-5 text-lg font-bold text-gray-900">{s.title}</h3>
                <p className="mt-2 text-sm text-gray-500">{s.desc}</p>
              </li>
            ))}
          </ol>
          <div className="mt-12 text-center">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-xl bg-primary-800 px-7 py-3.5 font-bold text-white shadow-md transition-colors hover:bg-primary-900"
            >
              Get started free <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="bg-background py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <SectionHeading
            eyebrow="Pricing"
            title="Start free. Upgrade when you're ready."
            intro="Premium unlocks every paper and marking scheme. Pay with M-Pesa."
          />
          {plans.length > 0 ? (
            <div className={`grid items-stretch gap-6 ${plans.length >= 3 ? "lg:grid-cols-3" : "md:grid-cols-2"}`}>
              {plans.slice(0, 3).map((p) => (
                <PlanCard key={p.id} plan={p} />
              ))}
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              <div className="flex flex-col rounded-3xl border border-gray-200 bg-white p-8">
                <h3 className="text-lg font-bold text-gray-900">Free</h3>
                <p className="mb-6 mt-1 text-sm text-gray-500">Enough to practise and stay ahead.</p>
                <CheckList
                  items={["Sample papers and worksheets", "Topic quizzes", "Browse every grade and subject"]}
                  iconClass="text-success-600"
                  textClass="text-gray-600"
                />
                <Link
                  href="/register"
                  className="mt-8 block rounded-xl bg-primary-50 py-3 text-center text-sm font-bold text-primary-800 hover:bg-primary-100"
                >
                  Create free account
                </Link>
              </div>
              <div className="flex flex-col rounded-3xl bg-gradient-to-b from-primary-800 to-primary-950 p-8 text-white shadow-2xl">
                <h3 className="text-lg font-bold">Premium</h3>
                <p className="mb-6 mt-1 text-sm text-white/70">Everything you need to score an A.</p>
                <CheckList
                  items={["Every past paper and exam", "Marking schemes", "Unlimited downloads", "Priority support"]}
                  iconClass="text-accent-400"
                  textClass="text-white/90"
                />
                <Link
                  href="/pricing"
                  className="mt-8 block rounded-xl bg-accent-500 py-3 text-center text-sm font-bold hover:bg-accent-600"
                >
                  See premium plans
                </Link>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* FAQ */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <SectionHeading eyebrow="Questions" title="Frequently asked questions" />
          <div className="divide-y divide-gray-100 rounded-2xl border border-gray-100 bg-white shadow-sm">
            {FAQ.map((item) => (
              <details key={item.q} className="group px-6 py-5">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold text-gray-900 [&::-webkit-details-marker]:hidden">
                  {item.q}
                  <ChevronDown className="h-5 w-5 shrink-0 text-gray-400 transition-transform group-open:rotate-180" />
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-gray-500">{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Final call to action */}
      <section className="px-4 pb-20 sm:px-6 lg:px-8">
        <div className="relative mx-auto max-w-6xl overflow-hidden rounded-[2rem] bg-primary-950 px-6 py-16 text-center text-white md:px-16">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(249,115,22,0.35),transparent_60%)]" />
          <div className="relative">
            <Image src="/logos/educore-logo-white.svg" alt="EduCore" width={180} height={53} className="mx-auto h-12 w-auto" />
            <h2 className="mx-auto mt-6 max-w-2xl text-3xl font-extrabold tracking-tight md:text-4xl">
              Give your child the revision edge this term.
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-blue-100/80">Join free in under a minute. No card needed.</p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                href="/register"
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-accent-500 px-8 py-4 font-bold shadow-lg shadow-accent-500/30 transition-all hover:-translate-y-0.5 hover:bg-accent-600 sm:w-auto"
              >
                Sign up free <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/login"
                className="inline-flex w-full items-center justify-center rounded-xl border border-white/25 px-8 py-4 font-semibold hover:bg-white/10 sm:w-auto"
              >
                I already have an account
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-blue-100/80">
              <a
                href={whatsappLink("Hello EduCore, I have a question about ")}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 hover:text-white"
              >
                <MessageCircle className="h-4 w-4" /> WhatsApp {site.supportPhone}
              </a>
              <a href={`tel:${site.supportPhoneTel}`} className="inline-flex items-center gap-1.5 hover:text-white">
                <Phone className="h-4 w-4" /> Call {site.supportPhone}
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-dark py-16 text-white/70">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
            <div>
              <Image src="/logos/educore-logo-white.svg" alt="EduCore" width={160} height={47} className="h-10 w-auto" />
              <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/60">{site.tagline}</p>
              <p className="mt-5 flex items-center gap-2 text-sm text-white/60">
                <Users className="h-4 w-4" /> For learners, parents and teachers
              </p>
            </div>
            <div>
              <h4 className="mb-4 text-xs font-bold uppercase tracking-wider text-white">Learn</h4>
              <ul className="space-y-2.5 text-sm">
                <li><Link href="/grades" className="hover:text-white">Grades</Link></li>
                <li><Link href="/subjects" className="hover:text-white">Subjects</Link></li>
                <li><Link href="/resources?type=past_paper" className="hover:text-white">Past papers</Link></li>
                <li><Link href="/resources?type=worksheet" className="hover:text-white">Worksheets</Link></li>
                <li><Link href="/pricing" className="hover:text-white">Premium</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-xs font-bold uppercase tracking-wider text-white">Company</h4>
              <ul className="space-y-2.5 text-sm">
                <li><Link href="/about" className="hover:text-white">About</Link></li>
                <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
                <li><Link href="/privacy" className="hover:text-white">Privacy policy</Link></li>
                <li><Link href="/terms" className="hover:text-white">Terms of service</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-xs font-bold uppercase tracking-wider text-white">Support</h4>
              <ul className="space-y-2.5 text-sm">
                <li><Link href="/help" className="hover:text-white">Help center</Link></li>
                <li><Link href="/contact" className="hover:text-white">M-Pesa payment help</Link></li>
                <li>
                  <a
                    href={whatsappLink("Hello EduCore, I need help with ")}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 hover:text-white"
                  >
                    <MessageCircle className="h-3.5 w-3.5" /> WhatsApp us
                  </a>
                </li>
                <li>
                  <a href={`tel:${site.supportPhoneTel}`} className="inline-flex items-center gap-1.5 hover:text-white">
                    <Phone className="h-3.5 w-3.5" /> Call {site.supportPhone}
                  </a>
                </li>
                <li>
                  <a href={`mailto:${site.supportEmail}`} className="break-all hover:text-white">
                    {site.supportEmail}
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-8 sm:flex-row">
            <p className="text-xs text-white/50">© {new Date().getFullYear()} EduCore. Made in Kenya.</p>
            <div className="flex gap-5 text-xs">
              <Link href="/privacy" className="hover:text-white">Privacy</Link>
              <Link href="/terms" className="hover:text-white">Terms</Link>
            </div>
          </div>
        </div>
      </footer>

      <MobileSignupBar />
    </div>
  );
}
