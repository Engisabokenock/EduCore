import type { Metadata } from "next";
import Link from "next/link";
import { Check, Zap } from "lucide-react";
import { serverApi } from "@/lib/server-api";
import type { Plan } from "@/types";

export const metadata: Metadata = {
  title: "Pricing — Unlock Premium Content",
  description:
    "Subscribe to EduCore Premium and access unlimited CBC curriculum notes, past papers, and worksheets for all grades.",
  openGraph: {
    title: "EduCore Pricing — Unlock Premium CBC Content",
    description: "Affordable plans for students in Kenya. Access all premium study materials.",
    url: "/pricing",
  },
  alternates: { canonical: "/pricing" },
};

export default async function PricingPage() {
  const plans: Plan[] = (await serverApi.getPlans()) ?? [];

  return (
    <div className="min-h-screen bg-white">
      <nav className="border-b border-gray-100 py-4 px-6 flex items-center justify-between">
        <Link href="/" className="font-bold text-xl text-gray-900">EduCore</Link>
        <Link href="/login" className="text-sm text-primary-600 font-medium hover:underline">Log in</Link>
      </nav>

      <section className="py-20 px-4 text-center">
        <h1 className="text-4xl font-extrabold text-gray-900 mb-4">Simple, Transparent Pricing</h1>
        <p className="text-gray-500 text-lg mb-16">
          Unlock all premium content for less than the cost of a single textbook.
        </p>

        {plans.length === 0 ? (
          <p className="text-gray-400">No plans available at the moment.</p>
        ) : (
          <div className="max-w-4xl mx-auto grid md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={`rounded-2xl border p-6 text-left flex flex-col ${
                  plan.is_featured
                    ? "border-primary-500 bg-primary-50 shadow-lg"
                    : "border-gray-200 bg-white"
                }`}
              >
                {plan.is_featured && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold bg-primary-600 text-white rounded-full px-3 py-1 mb-4 self-start">
                    <Zap className="h-3 w-3" /> Most Popular
                  </span>
                )}
                <h2 className="text-xl font-bold text-gray-900 mb-1">{plan.name}</h2>
                <p className="text-gray-500 text-sm mb-4">{plan.description}</p>
                <div className="mb-6">
                  <span className="text-4xl font-extrabold text-gray-900">
                    {Number(plan.price) === 0 ? "Free" : `KES ${plan.price}`}
                  </span>
                  {Number(plan.price) > 0 && (
                    <span className="text-gray-400 text-sm ml-1">
                      /{plan.billing_cycle === "monthly" ? "mo" : plan.billing_cycle === "annual" ? "yr" : "lifetime"}
                    </span>
                  )}
                </div>
                <ul className="space-y-2 mb-8 flex-1">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm text-gray-700">
                      <Check className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link
                  href={Number(plan.price) === 0 ? "/register" : `/checkout?plan=${plan.id}`}
                  className={`w-full text-center py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                    plan.is_featured
                      ? "bg-primary-600 hover:bg-primary-700 text-white"
                      : "bg-gray-100 hover:bg-gray-200 text-gray-900"
                  }`}
                >
                  {Number(plan.price) === 0 ? "Get Started Free" : "Subscribe Now"}
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
