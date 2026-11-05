/**
 * Public site details. Contact channels come from environment variables so real
 * support addresses are configured per deployment, never hard-coded:
 *
 *   NEXT_PUBLIC_SUPPORT_EMAIL     e.g. support@yourdomain.co.ke
 *   NEXT_PUBLIC_SUPPORT_PHONE     e.g. +254 7XX XXX XXX
 *   NEXT_PUBLIC_SUPPORT_WHATSAPP  international number without "+", e.g. 2547XXXXXXXX
 */
export const site = {
  name: "EduCore",
  tagline: "Kenya's CBC revision platform for learners and parents.",
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL?.trim() || null,
  supportPhone: process.env.NEXT_PUBLIC_SUPPORT_PHONE?.trim() || null,
  supportWhatsapp: process.env.NEXT_PUBLIC_SUPPORT_WHATSAPP?.replace(/\D/g, "") || null,
  legalUpdated: "4 November 2026",
};

export function whatsappLink(message?: string): string | null {
  if (!site.supportWhatsapp) return null;
  const text = message ? `?text=${encodeURIComponent(message)}` : "";
  return `https://wa.me/${site.supportWhatsapp}${text}`;
}
