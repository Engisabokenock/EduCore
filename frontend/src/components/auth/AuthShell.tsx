import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";
import { CheckCircle2 } from "lucide-react";

const DEFAULT_POINTS = [
  "CBC exams, worksheets and notes for every grade",
  "Topic quizzes with instant marks",
  "Parents see each child's progress",
  "Unlock premium in seconds with M-Pesa",
];

/**
 * Split-screen layout for the learner sign-in and sign-up pages: brand panel on the
 * left (desktop), form on the right. The logo is always visible on every screen size.
 */
export function AuthShell({
  title,
  subtitle,
  children,
  footer,
  panelTitle = "Revise smarter. Score higher.",
  points = DEFAULT_POINTS,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  panelTitle?: string;
  points?: string[];
}) {
  return (
    <div className="flex min-h-screen bg-white">
      {/* Brand panel */}
      <aside className="relative hidden w-[46%] max-w-[640px] flex-col justify-between overflow-hidden bg-primary-950 p-12 text-white lg:flex">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(59,130,246,0.5),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(22,163,74,0.4),transparent_55%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_at_center,black_35%,transparent_75%)]" />

        <Link href="/" aria-label="EduCore home" className="relative">
          <Image src="/logos/educore-logo-white.svg" alt="EduCore" width={190} height={56} priority className="h-12 w-auto" />
        </Link>

        <div className="relative">
          <h2 className="text-4xl font-extrabold leading-tight tracking-tight xl:text-5xl">{panelTitle}</h2>
          <ul className="mt-8 space-y-4">
            {points.map((p) => (
              <li key={p} className="flex items-start gap-3 text-base text-blue-50/90">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/10">
                  <CheckCircle2 className="h-4 w-4 text-accent-400" />
                </span>
                {p}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur">
          <p className="text-sm leading-relaxed text-blue-50/90">
            Free to start, no card needed. Built for Kenya&apos;s CBC curriculum, for learners and the parents who
            support them.
          </p>
        </div>
      </aside>

      {/* Form */}
      <main className="flex flex-1 flex-col bg-gradient-to-b from-white to-background">
        <div className="flex items-center justify-between px-6 py-5 sm:px-10">
          <Link href="/" aria-label="EduCore home" className="lg:invisible">
            <Image src="/logos/educore-logo.svg" alt="EduCore" width={160} height={47} priority className="h-10 w-auto" />
          </Link>
          <Link href="/" className="text-sm font-medium text-gray-500 hover:text-primary-800">
            ← Back to home
          </Link>
        </div>

        <div className="flex flex-1 items-center justify-center px-6 pb-12 sm:px-10">
          <div className="w-full max-w-md">
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">{title}</h1>
            {subtitle && <p className="mt-2 text-gray-500">{subtitle}</p>}
            <div className="mt-8">{children}</div>
            {footer && <div className="mt-8 text-center text-sm text-gray-500">{footer}</div>}
          </div>
        </div>
      </main>
    </div>
  );
}

/** Shared input styling for the auth forms. */
export const authInput =
  "w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition placeholder:text-gray-400 focus:border-primary-500 focus:ring-4 focus:ring-primary-100";

export const authLabel = "mb-1.5 block text-sm font-semibold text-gray-700";

export const authButton =
  "flex w-full items-center justify-center gap-2 rounded-xl bg-accent-500 py-3.5 text-base font-bold text-white shadow-lg shadow-accent-500/25 transition-all hover:-translate-y-px hover:bg-accent-600 disabled:translate-y-0 disabled:opacity-60";

export function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p role="alert" className="mt-1.5 text-xs font-medium text-red-600">
      {message}
    </p>
  );
}
