"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import useSWR from "swr";

import { fetcher } from "@/lib/api";
import { usePrefs } from "@/lib/prefs";
import type { GroceryList } from "@/lib/types";

import { Badge } from "../core/Badge";
import { Icon } from "../core/Icon";

/** Floating dark pill with exactly 4 tabs (bottom-left) + terracotta add button (bottom-right). */
export function BottomNav() {
  const { t } = usePrefs();
  const pathname = usePathname();
  const { data: grocery } = useSWR<GroceryList>("/api/grocery", fetcher, { refreshInterval: 8000 });

  const items = [
    { href: "/", icon: "home", label: t.tabHome },
    { href: "/search", icon: "search", label: t.tabSearch },
    { href: "/grocery", icon: "shopping_basket", label: t.tabGrocery, badge: grocery?.open_count ?? 0 },
    { href: "/recipes", icon: "menu_book", label: t.tabRecipes },
  ];

  return (
    <>
      <nav className="bottom-nav" aria-label="Main">
        {items.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className="bottom-nav__item"
              aria-current={active ? "page" : undefined}
              aria-label={active ? undefined : item.badge ? `${item.label} (${item.badge})` : item.label}
            >
              <Icon name={item.icon} fill={active} />
              {active && <span className="bottom-nav__label">{item.label}</span>}
              {!!item.badge && <Badge count={item.badge} className="bottom-nav__badge" />}
            </Link>
          );
        })}
      </nav>
      <Link href="/add" className="fab" aria-label={t.addRecipe}>
        <Icon name="add" />
      </Link>
    </>
  );
}
