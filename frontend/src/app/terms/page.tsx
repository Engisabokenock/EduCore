import type { Metadata } from "next";
import Link from "next/link";
import { PublicShell, Prose } from "@/components/layout/PublicShell";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Terms of Service — EduCore",
  description: "The terms that apply when you use EduCore.",
};

export default function TermsPage() {
  return (
    <PublicShell>
      <Prose title="Terms of Service" intro={`Last updated ${site.legalUpdated}.`}>
        <section>
          <h2>Using EduCore</h2>
          <p>
            By using {site.name} you agree to these terms. If you are under 18, a parent or guardian must agree to them
            on your behalf and supervise your use of the platform.
          </p>
        </section>
        <section>
          <h2>Your account</h2>
          <ul>
            <li>Give accurate information and keep your password private.</li>
            <li>You are responsible for activity on your account.</li>
            <li>Tell us straight away if you think someone else has accessed it.</li>
          </ul>
        </section>
        <section>
          <h2>Resources and acceptable use</h2>
          <p>
            Resources are for personal, non-commercial study and classroom use. You may not resell, republish or
            redistribute them, share premium files publicly, or use automated tools to download content in bulk.
          </p>
        </section>
        <section>
          <h2>Premium subscriptions and payments</h2>
          <ul>
            <li>Premium plans are paid through M-Pesa at the price shown when you check out.</li>
            <li>Access starts once the payment is confirmed and lasts for the period of the plan you chose.</li>
            <li>You can turn off auto-renew at any time and keep access until the paid period ends.</li>
            <li>
              If you were charged in error or premium did not activate,{" "}
              <Link href="/contact" className="text-primary-600 hover:underline">contact us</Link> and we will review
              it. Refunds are handled case by case.
            </li>
          </ul>
        </section>
        <section>
          <h2>Content accuracy</h2>
          <p>
            We review resources carefully, but they are revision aids and may contain errors. They do not replace
            guidance from teachers or the official curriculum.
          </p>
        </section>
        <section>
          <h2>Suspension</h2>
          <p>
            We may suspend or close accounts that break these terms, for example by sharing premium content or abusing
            the service.
          </p>
        </section>
        <section>
          <h2>Liability</h2>
          <p>
            The service is provided as is. To the extent the law allows, we are not liable for indirect losses arising
            from its use. Nothing in these terms limits rights you have under Kenyan consumer protection law.
          </p>
        </section>
        <section>
          <h2>Changes and governing law</h2>
          <p>
            We may update these terms and will post changes on this page. These terms are governed by the laws of
            Kenya.
          </p>
        </section>
      </Prose>
    </PublicShell>
  );
}
