"use client";

import { useRouter } from "next/navigation";

import { SegmentedControl } from "@/components/forms/SegmentedControl";
import { TopBar } from "@/components/navigation/TopBar";
import { api } from "@/lib/api";
import type { Lang } from "@/lib/i18n";
import { useMe, useMemberName, usePrefs, type Theme } from "@/lib/prefs";

export function SettingsScreen() {
  const { t, lang, setLang, theme, setTheme } = usePrefs();
  const { data: me } = useMe();
  const memberName = useMemberName();
  const router = useRouter();

  const signOut = async () => {
    await api.post("/api/auth/logout");
    router.replace("/login");
  };

  return (
    <main>
      <TopBar title={t.settingsTitle} backHref="/" />
      <div className="add add__stack" style={{ paddingTop: 16 }}>
        <section>
          <h2 className="overline" style={{ marginBottom: 10 }}>
            {t.language}
          </h2>
          <SegmentedControl<Lang>
            label={t.language}
            value={lang}
            onChange={setLang}
            options={[
              { value: "en", label: "English", lang: "en" },
              { value: "zh", label: "繁體中文", lang: "zh-Hant" },
            ]}
          />
        </section>
        <section>
          <h2 className="overline" style={{ marginBottom: 10 }}>
            {t.appearance}
          </h2>
          <SegmentedControl<Theme>
            label={t.appearance}
            value={theme}
            onChange={setTheme}
            options={[
              { value: "light", label: t.light },
              { value: "dark", label: t.dark },
            ]}
          />
        </section>
        <section>
          <h2 className="overline" style={{ marginBottom: 10 }}>
            {t.kitchen}
          </h2>
          <div className="group">
            <div className="group__row">
              <span>{t.household}</span>
              <span className="group__value">{me ? (lang === "zh" ? me.household.name_zh : me.household.name) : ""}</span>
            </div>
            <div className="group__row">
              <span>{t.units}</span>
              <span className="group__value">{t.unitsValue}</span>
            </div>
          </div>
        </section>
        <section>
          <div className="group">
            <div className="group__row">
              <span>{me ? t.signedInAs(memberName(me.member)) : ""}</span>
            </div>
            <button type="button" className="group__row" style={{ color: "var(--accent)", fontWeight: 600 }} onClick={signOut}>
              {t.signOut}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
