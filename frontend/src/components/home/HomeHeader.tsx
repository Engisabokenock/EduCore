"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Menu, X } from "lucide-react";
import { useSignedInHome } from "./useSignedIn";

const NAV = [
  { href: "/grades", label: "Grades" },
  { href: "/subjects", label: "Subjects" },
  { href: "/resources", label: "Resources" },
  { href: "/pricing", label: "Pricing" },
  { href: "/help", label: "Help" },
];

/** Sticky site header: the logo and the sign-in actions stay visible while scrolling. */
export function HomeHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const home = useSignedInHome();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled || open
          ? "border-b border-gray-200/70 bg-white/90 shadow-sm backdrop-blur-lg"
          : "border-b border-transparent bg-white"
      }`}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:h-[72px] lg:px-8">
        <Link href="/" aria-label="EduCore home" className="flex shrink-0 items-center">
          <Image
            src="/logos/educore-logo.svg"
            alt="EduCore — CBC Learning Made Simple"
            width={168}
            height={49}
            priority
            className="h-10 w-auto lg:h-11"
          />
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-1 lg:flex">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 hover:text-primary-800"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {home ? (
            <Link
              href={home}
              className="inline-flex items-center gap-1.5 rounded-xl bg-primary-800 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-900"
            >
              My dashboard <ArrowRight className="h-4 w-4" />
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-xl px-3 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 hover:text-primary-800 sm:px-4"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="inline-flex items-center gap-1.5 rounded-xl bg-accent-500 px-4 py-2.5 text-sm font-bold text-white shadow-md shadow-accent-500/25 transition-all hover:-translate-y-px hover:bg-accent-600"
              >
                <span className="hidden sm:inline">Sign up free</span>
                <span className="sm:hidden">Sign up</span>
              </Link>
            </>
          )}
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            className="ml-1 inline-flex h-10 w-10 items-center justify-center rounded-xl text-gray-700 hover:bg-gray-100 lg:hidden"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {open && (
        <div className="border-t border-gray-100 bg-white lg:hidden">
          <nav aria-label="Mobile" className="mx-auto max-w-7xl space-y-1 px-4 py-4 sm:px-6">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="block rounded-xl px-4 py-3 text-base font-medium text-gray-800 hover:bg-gray-50"
              >
                {item.label}
              </Link>
            ))}
            {!home && (
              <div className="grid grid-cols-2 gap-3 pt-3">
                <Link
                  href="/login"
                  className="rounded-xl border border-gray-200 py-3 text-center text-sm font-semibold text-gray-800"
                >
                  Log in
                </Link>
                <Link href="/register" className="rounded-xl bg-accent-500 py-3 text-center text-sm font-bold text-white">
                  Sign up free
                </Link>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}

/** Phone-only bar pinned to the bottom so signing up is always one tap away. */
export function MobileSignupBar() {
  const home = useSignedInHome();
  if (home) return null;
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-gray-200 bg-white/95 px-4 py-3 shadow-[0_-4px_20px_rgba(15,23,42,0.08)] backdrop-blur sm:hidden">
      <div className="flex items-center gap-3">
        <Link href="/login" className="flex-1 rounded-xl border border-gray-200 py-3 text-center text-sm font-semibold text-gray-800">
          Log in
        </Link>
        <Link href="/register" className="flex-[1.4] rounded-xl bg-accent-500 py-3 text-center text-sm font-bold text-white shadow-md shadow-accent-500/25">
          Sign up free
        </Link>
      </div>
    </div>
  );
}
