"use client";

import { SWRConfig } from "swr";

import { fetcher } from "@/lib/api";
import { PrefsProvider } from "@/lib/prefs";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig value={{ fetcher, revalidateOnFocus: true, keepPreviousData: true }}>
      <PrefsProvider>{children}</PrefsProvider>
    </SWRConfig>
  );
}
