import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";
import { Providers } from "@/components/providers";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "https://educore.co.ke";

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: {
    default: "EduCore — Learn Smarter",
    template: "%s | EduCore",
  },
  description:
    "Kenya's #1 education platform. Access CBC curriculum notes, past papers, worksheets and revision materials for all grades.",
  keywords: ["CBC", "Kenya education", "past papers", "revision notes", "KCPE", "KCSE", "CBC curriculum", "Grade 5 notes"],
  authors: [{ name: "EduCore" }],
  creator: "EduCore",
  publisher: "EduCore",
  openGraph: {
    type: "website",
    locale: "en_KE",
    siteName: "EduCore",
    url: SITE,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "EduCore — Kenya's #1 Education Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    site: "@educore_ke",
    creator: "@educore_ke",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: SITE,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION ?? "",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          {children}
          <Toaster richColors position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
