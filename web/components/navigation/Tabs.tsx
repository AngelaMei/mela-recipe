"use client";

import { useRef } from "react";

export interface TabsProps<T extends string> {
  label: string;
  value: T;
  tabs: { value: T; label: string }[];
  onChange: (v: T) => void;
  idPrefix: string;
}

export function Tabs<T extends string>({ label, value, tabs, onChange, idPrefix }: TabsProps<T>) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const onKey = (e: React.KeyboardEvent, i: number) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const next = (i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    onChange(tabs[next].value);
    refs.current[next]?.focus();
  };
  return (
    <div className="tabs" role="tablist" aria-label={label}>
      {tabs.map((tab, i) => (
        <button
          key={tab.value}
          ref={(el) => {
            refs.current[i] = el;
          }}
          id={`${idPrefix}-tab-${tab.value}`}
          type="button"
          role="tab"
          aria-selected={tab.value === value}
          aria-controls={`${idPrefix}-panel-${tab.value}`}
          tabIndex={tab.value === value ? 0 : -1}
          className="tabs__tab"
          onClick={() => onChange(tab.value)}
          onKeyDown={(e) => onKey(e, i)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
