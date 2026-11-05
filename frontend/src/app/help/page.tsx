import type { Metadata } from "next";
import Link from "next/link";
import { PublicShell, Prose } from "@/components/layout/PublicShell";

export const metadata: Metadata = {
  title: "Help Center — EduCore",
  description: "Answers to common questions about EduCore accounts, downloads and M-Pesa payments.",
};

const FAQ: { q: string; a: React.ReactNode }[] = [
  {
    q: "Do I need an account to download?",
    a: "No. You can download a limited number of free resources each day without an account. Creating a free account lets you see your download history.",
  },
  {
    q: "How many free downloads do I get?",
    a: "Everyone gets a daily allowance of free downloads. It resets every day. Premium members download without limits.",
  },
  {
    q: "How do I pay for premium?",
    a: (
      <>
        Choose a plan on the <Link href="/pricing" className="text-primary-600 hover:underline">pricing page</Link>, enter
        your Safaricom number and approve the M-Pesa prompt on your phone with your PIN. Premium activates as soon as the
        payment is confirmed.
      </>
    ),
  },
  {
    q: "I paid but premium is not active. What should I do?",
    a: (
      <>
        Wait a minute and refresh your dashboard, because confirmations can be delayed. If it is still not active,{" "}
        <Link href="/contact" className="text-primary-600 hover:underline">contact us</Link> with your M-Pesa
        confirmation code.
      </>
    ),
  },
  {
    q: "Can I cancel my subscription?",
    a: "Yes. Turn off auto-renew from your dashboard. You keep premium access until the end of the period you paid for.",
  },
  {
    q: "I forgot my password.",
    a: (
      <>
        Use <Link href="/forgot-password" className="text-primary-600 hover:underline">password reset</Link>. We will
        e-mail you a link that is valid for a limited time.
      </>
    ),
  },
  {
    q: "Which grades and subjects are covered?",
    a: (
      <>
        See the full list on the <Link href="/grades" className="text-primary-600 hover:underline">grades page</Link>.
        New resources are added every week.
      </>
    ),
  },
];

export default function HelpPage() {
  return (
    <PublicShell>
      <Prose title="Help Center" intro="Quick answers to the questions we hear most.">
        <section className="divide-y divide-gray-100 rounded-xl border border-gray-100 bg-white">
          {FAQ.map((item) => (
            <details key={item.q} className="group px-5 py-4">
              <summary className="cursor-pointer list-none font-medium text-gray-900 marker:hidden">
                <span className="mr-2 inline-block text-gray-400 transition-transform group-open:rotate-90">›</span>
                {item.q}
              </summary>
              <div className="mt-2 pl-5 text-gray-600">{item.a}</div>
            </details>
          ))}
        </section>
        <section>
          <p>
            Still stuck?{" "}
            <Link href="/contact" className="font-medium text-primary-600 hover:underline">
              Contact support
            </Link>
            .
          </p>
        </section>
      </Prose>
    </PublicShell>
  );
}
