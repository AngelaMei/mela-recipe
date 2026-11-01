"use client";

import { useRouter } from "next/navigation";

import { usePrefs } from "@/lib/prefs";

import { Icon } from "../core/Icon";

export interface TopBarProps {
  title?: string;
  start?: React.ReactNode;
  end?: React.ReactNode;
  backHref?: string;
}

/** Sub-page header. Hides the nav; shows a back control or custom start/end. */
export function TopBar({ title, start, end, backHref }: TopBarProps) {
  const router = useRouter();
  const { t } = usePrefs();
  return (
    <header className="topbar">
      <div className="topbar__start">
        {start ??
          (backHref !== undefined && (
            <button
              type="button"
              className="topbar__back"
              onClick={() => (window.history.length > 1 ? router.back() : router.push(backHref))}
            >
              <Icon name="chevron_left" size={26} />
              {t.back}
            </button>
          ))}
      </div>
      {title ? <h1 className="topbar__title">{title}</h1> : <span />}
      <div className="topbar__end">{end}</div>
    </header>
  );
}
