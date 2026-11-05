import type { Metadata } from "next";
import Link from "next/link";
import { Mail, MessageCircle, Phone } from "lucide-react";
import { PublicShell, Prose } from "@/components/layout/PublicShell";
import { site, whatsappLink } from "@/lib/site";

export const metadata: Metadata = {
  title: "Contact EduCore",
  description: "Get help with your EduCore account, M-Pesa payments or resources.",
};

export default function ContactPage() {
  const whatsapp = whatsappLink("Hello EduCore, I need help with ");
  const hasChannel = !!(site.supportEmail || site.supportPhone || whatsapp);

  return (
    <PublicShell>
      <Prose title="Contact us" intro="We usually reply within one working day.">
        {hasChannel ? (
          <section className="grid gap-4 sm:grid-cols-3">
            {site.supportEmail && (
              <a
                href={`mailto:${site.supportEmail}`}
                className="rounded-xl border border-gray-100 bg-white p-5 hover:shadow-sm"
              >
                <Mail className="mb-2 h-5 w-5 text-primary-600" />
                <p className="font-medium text-gray-900">E-mail</p>
                <p className="break-all text-sm text-gray-600">{site.supportEmail}</p>
              </a>
            )}
            {site.supportPhone && (
              <a
                href={`tel:${site.supportPhone.replace(/\s/g, "")}`}
                className="rounded-xl border border-gray-100 bg-white p-5 hover:shadow-sm"
              >
                <Phone className="mb-2 h-5 w-5 text-primary-600" />
                <p className="font-medium text-gray-900">Phone</p>
                <p className="text-sm text-gray-600">{site.supportPhone}</p>
              </a>
            )}
            {whatsapp && (
              <a
                href={whatsapp}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl border border-gray-100 bg-white p-5 hover:shadow-sm"
              >
                <MessageCircle className="mb-2 h-5 w-5 text-green-600" />
                <p className="font-medium text-gray-900">WhatsApp</p>
                <p className="text-sm text-gray-600">Chat with support</p>
              </a>
            )}
          </section>
        ) : (
          <section className="rounded-xl border border-amber-100 bg-amber-50 p-5 text-sm text-amber-900">
            Our support channels are being set up. In the meantime, most questions are answered in the{" "}
            <Link href="/help" className="font-medium underline">
              Help Center
            </Link>
            .
          </section>
        )}

        <section>
          <h2>M-Pesa payment issues</h2>
          <p>If you paid but premium is not active yet, please include these details so we can find your payment quickly:</p>
          <ul>
            <li>The M-Pesa confirmation code (for example, QFT1AB2CD3).</li>
            <li>The phone number that paid.</li>
            <li>The e-mail address of your EduCore account.</li>
          </ul>
          <p className="mt-2">
            Most payments activate within a minute. Refresh your dashboard first, because confirmations from Safaricom
            are sometimes delayed.
          </p>
        </section>

        <section>
          <h2>Account help</h2>
          <p>
            Forgot your password? Use{" "}
            <Link href="/forgot-password" className="text-primary-600 hover:underline">
              password reset
            </Link>{" "}
            to get a new one by e-mail.
          </p>
        </section>
      </Prose>
    </PublicShell>
  );
}
