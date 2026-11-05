import type { Metadata } from "next";
import Link from "next/link";
import { PublicShell, Prose } from "@/components/layout/PublicShell";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Privacy Policy — EduCore",
  description: "How EduCore collects, uses and protects your personal data.",
};

export default function PrivacyPage() {
  return (
    <PublicShell>
      <Prose title="Privacy Policy" intro={`Last updated ${site.legalUpdated}.`}>
        <section>
          <h2>Who we are</h2>
          <p>
            {site.name} operates this website and processes personal data in line with the Kenya Data Protection Act,
            2019. This policy explains what we collect, why, and the choices you have.
          </p>
        </section>
        <section>
          <h2>What we collect</h2>
          <ul>
            <li>Account details: your name, e-mail address, optional phone number and account type.</li>
            <li>Payment details: the phone number used for M-Pesa, amounts and M-Pesa confirmation codes. We never see or store your M-Pesa PIN.</li>
            <li>Usage information: the resources you view and download, and technical data such as IP address and browser type, used for security and to enforce download limits.</li>
          </ul>
        </section>
        <section>
          <h2>How we use it</h2>
          <ul>
            <li>To run your account and give you access to the resources you are entitled to.</li>
            <li>To process payments and resolve payment issues.</li>
            <li>To keep the platform secure, prevent abuse and investigate problems.</li>
            <li>To send account messages such as password resets and payment confirmations.</li>
          </ul>
        </section>
        <section>
          <h2>Sharing</h2>
          <p>
            We do not sell your data. We share it only with service providers that help us run the platform, such as
            Safaricom for M-Pesa payments and our hosting and storage providers, and only as far as they need it to
            provide their service. We may disclose data when the law requires it.
          </p>
        </section>
        <section>
          <h2>Children</h2>
          <p>
            Many of our learners are children. Accounts for learners under 18 should be created or supervised by a
            parent or guardian, who may contact us at any time about their child&apos;s data.
          </p>
        </section>
        <section>
          <h2>Retention and security</h2>
          <p>
            We keep account data while your account is active. Payment records are kept for as long as financial
            regulations require. Passwords are stored using strong one-way hashing, and access to personal data is
            restricted to staff who need it.
          </p>
        </section>
        <section>
          <h2>Your rights</h2>
          <p>
            You may ask to see, correct or delete your personal data, or object to how it is used. You can delete your
            account from your dashboard, which removes your personal details while keeping anonymised payment records
            we are required to retain. For any other request, use the{" "}
            <Link href="/contact" className="text-primary-600 hover:underline">contact page</Link>. You also have the
            right to complain to the Office of the Data Protection Commissioner.
          </p>
        </section>
        <section>
          <h2>Changes</h2>
          <p>We will post any changes to this policy on this page and update the date above.</p>
        </section>
      </Prose>
    </PublicShell>
  );
}
