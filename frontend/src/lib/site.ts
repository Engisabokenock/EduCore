/**
 * Public site details. The support channels below are the defaults; each can be
 * overridden per deployment without a code change:
 *
 *   NEXT_PUBLIC_SUPPORT_EMAIL     e.g. support@yourdomain.co.ke
 *   NEXT_PUBLIC_SUPPORT_PHONE     Kenyan number, e.g. 0729436062 (used for calls and WhatsApp)
 *   NEXT_PUBLIC_SUPPORT_WHATSAPP  only if WhatsApp uses a different number
 */
const DEFAULT_SUPPORT_EMAIL = "onyinkwafranciscah@gmail.com";
const DEFAULT_SUPPORT_PHONE = "0729436062";

/** Normalise a Kenyan number to international digits: 0729436062 -> 254729436062. */
export function toInternational(phone: string): string {
  const digits = phone.replace(/\D/g, "");
  if (digits.startsWith("254")) return digits;
  if (digits.startsWith("0")) return `254${digits.slice(1)}`;
  if (digits.length === 9) return `254${digits}`;
  return digits;
}

/** Human-friendly local format: 254729436062 -> 0729 436 062. */
export function formatLocal(phone: string): string {
  const intl = toInternational(phone);
  if (!intl.startsWith("254") || intl.length !== 12) return phone;
  const local = `0${intl.slice(3)}`;
  return `${local.slice(0, 4)} ${local.slice(4, 7)} ${local.slice(7)}`;
}

const phone = process.env.NEXT_PUBLIC_SUPPORT_PHONE?.trim() || DEFAULT_SUPPORT_PHONE;
const whatsapp = process.env.NEXT_PUBLIC_SUPPORT_WHATSAPP?.trim() || phone;

export const site = {
  name: "EduCore",
  tagline: "Kenya's CBC revision platform for learners and parents.",
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL?.trim() || DEFAULT_SUPPORT_EMAIL,
  /** Display format, e.g. "0729 436 062". */
  supportPhone: formatLocal(phone),
  /** For tel: links, e.g. "+254729436062". */
  supportPhoneTel: `+${toInternational(phone)}`,
  /** For wa.me links, e.g. "254729436062". */
  supportWhatsapp: toInternational(whatsapp),
  legalUpdated: "4 November 2026",
};

export function whatsappLink(message?: string): string {
  const text = message ? `?text=${encodeURIComponent(message)}` : "";
  return `https://wa.me/${site.supportWhatsapp}${text}`;
}
