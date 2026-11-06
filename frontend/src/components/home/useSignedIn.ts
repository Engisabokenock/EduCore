"use client";

import { useEffect, useState } from "react";
import { getAccessToken, getPortalCookie, getRefreshToken } from "@/lib/auth-cookies";

/**
 * Where a returning visitor should go, or null when signed out. Read after mount so the
 * server-rendered (signed-out) markup and the first client render always match.
 */
export function useSignedInHome(): string | null {
  const [home, setHome] = useState<string | null>(null);
  useEffect(() => {
    if (!(getAccessToken() || getRefreshToken())) return;
    setHome(getPortalCookie() === "staff" ? "/staff" : "/dashboard");
  }, []);
  return home;
}
