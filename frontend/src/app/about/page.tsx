import type { Metadata } from "next";
import Link from "next/link";
import { PublicShell, Prose } from "@/components/layout/PublicShell";

export const metadata: Metadata = {
  title: "About EduCore",
  description: "EduCore helps Kenyan learners and parents revise the CBC curriculum with worksheets, exams and notes.",
};

export default function AboutPage() {
  return (
    <PublicShell>
      <Prose
        title="About EduCore"
        intro="EduCore is a revision platform built around Kenya's Competency-Based Curriculum (CBC)."
      >
        <section>
          <h2>What we do</h2>
          <p>
            We organise worksheets, past papers, mock exams, lesson notes and marking schemes by grade, subject and
            topic, so a learner or parent can find exactly what matches this week&apos;s lessons in a few clicks.
          </p>
        </section>
        <section>
          <h2>How it works</h2>
          <ul>
            <li>Browse every grade, subject and topic for free.</li>
            <li>Download a number of free resources each day, with or without an account.</li>
            <li>Upgrade to premium with M-Pesa for unlimited downloads and premium papers with marking schemes.</li>
          </ul>
        </section>
        <section>
          <h2>Quality you can trust</h2>
          <p>
            Resources are prepared by teachers and reviewed by our team before they are published. If something looks
            wrong, tell us through the <Link href="/contact" className="text-primary-600 hover:underline">contact page</Link> and
            we will fix it.
          </p>
        </section>
        <section>
          <p>
            <Link href="/grades" className="font-medium text-primary-600 hover:underline">
              Start browsing by grade →
            </Link>
          </p>
        </section>
      </Prose>
    </PublicShell>
  );
}
