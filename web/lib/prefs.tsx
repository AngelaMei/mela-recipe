"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import useSWR from "swr";

import { fetcher } from "./api";
import { STRINGS, type Lang, type Strings } from "./i18n";
import type { Me } from "./types";

export type Theme = "light" | "dark";

const LANG_KEY = "mela.lang";
const THEME_KEY = "mela.theme";

interface Prefs {
  lang: Lang;
  t: Strings;
  setLang: (l: Lang) => void;
  theme: Theme;
  setTheme: (t: Theme) => void;
}

const PrefsContext = createContext<Prefs | null>(null);

function read<T extends string>(key: string, allowed: readonly T[]): T | null {
  try {
    const v = localStorage.getItem(key);
    return v && (allowed as readonly string[]).includes(v) ? (v as T) : null;
  } catch {
    return null;
  }
}

function write(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode */
  }
}

/** Runs before hydration (see layout.tsx) so there's no flash of the wrong theme/language. */
export const PREFS_BOOT_SCRIPT = `(function(){try{var d=document.documentElement;var l=localStorage.getItem('${LANG_KEY}');if(l==='zh'){d.lang='zh-Hant'}var t=localStorage.getItem('${THEME_KEY}');if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}d.setAttribute('data-theme',t)}catch(e){}})();`;

export function PrefsProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  const [theme, setThemeState] = useState<Theme>("light");

  useEffect(() => {
    setLangState(read(LANG_KEY, ["en", "zh"] as const) ?? "en");
    const saved = read(THEME_KEY, ["light", "dark"] as const);
    setThemeState(saved ?? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang === "zh" ? "zh-Hant" : "en";
  }, [lang]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    const meta = document.querySelector('meta[name="theme-color"]');
    meta?.setAttribute("content", theme === "dark" ? "#1d1915" : "#fbf7ef");
  }, [theme]);

  const setLang = useCallback((l: Lang) => {
    write(LANG_KEY, l);
    setLangState(l);
  }, []);
  const setTheme = useCallback((t: Theme) => {
    write(THEME_KEY, t);
    setThemeState(t);
  }, []);

  const value = useMemo(() => ({ lang, t: STRINGS[lang], setLang, theme, setTheme }), [lang, theme, setLang, setTheme]);
  return <PrefsContext.Provider value={value}>{children}</PrefsContext.Provider>;
}

export function usePrefs(): Prefs {
  const ctx = useContext(PrefsContext);
  if (!ctx) throw new Error("usePrefs outside PrefsProvider");
  return ctx;
}

/** The signed-in member and household. */
export function useMe() {
  return useSWR<Me>("/api/auth/me", fetcher, { revalidateOnFocus: false });
}

/** Display name of a member in the current language. */
export function useMemberName() {
  const { lang } = usePrefs();
  const { data } = useMe();
  return useCallback(
    (name: string) => {
      const m = data?.household.members.find((x) => x.name === name);
      return m ? (lang === "zh" ? m.name_zh : m.name) : name;
    },
    [data, lang],
  );
}

/** The other member(s), for "shared with Paul". */
export function useOthers(): string {
  const { lang } = usePrefs();
  const { data } = useMe();
  if (!data) return "";
  const others = data.household.members.filter((m) => m.name !== data.member);
  return others.map((m) => (lang === "zh" ? m.name_zh : m.name)).join(lang === "zh" ? "、" : " & ");
}
