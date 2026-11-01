"use client";

import { useState } from "react";
import useSWR from "swr";

import { Button } from "@/components/core/Button";
import { IconButton } from "@/components/core/IconButton";
import { TextField } from "@/components/forms/TextField";
import { GroceryItem } from "@/components/recipe/GroceryItem";
import { api } from "@/lib/api";
import { groceryQty, grocerySources } from "@/lib/format";
import { useMemberName, useOthers, usePrefs } from "@/lib/prefs";
import type { GroceryList } from "@/lib/types";

export function GroceryScreen() {
  const { t } = usePrefs();
  const memberName = useMemberName();
  const others = useOthers();
  // Poll so the list stays in sync between the two phones.
  const { data, mutate } = useSWR<GroceryList>("/api/grocery", { refreshInterval: 4000 });
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    const value = text.trim();
    if (!value) return;
    setText("");
    try {
      await mutate(api.post<GroceryList>("/api/grocery", { text: value }), { revalidate: false });
      setError(null);
    } catch {
      setText(value);
      setError(t.genericError);
    }
  };

  const toggle = async (id: string, checked: boolean) => {
    if (!data) return;
    const move = (list: GroceryList): GroceryList => {
      const all = [...list.open, ...list.basket].map((i) => (i.id === id ? { ...i, checked } : i));
      const open = all.filter((i) => !i.checked);
      return { open, basket: all.filter((i) => i.checked), open_count: open.length };
    };
    await mutate(api.patch<GroceryList>(`/api/grocery/${id}`, { checked }), {
      optimisticData: move(data),
      rollbackOnError: true,
      revalidate: false,
    });
  };

  const clear = async () => {
    if (!data) return;
    await mutate(api.post<GroceryList>("/api/grocery/clear"), {
      optimisticData: { ...data, basket: [] },
      rollbackOnError: true,
      revalidate: false,
    });
  };

  const openItems = data?.open ?? [];
  const basket = data?.basket ?? [];

  return (
    <main className="screen">
      <div className="screen__head">
        <div>
          <h1 className="display">{t.groceryTitle}</h1>
          <p className="subtitle">{data ? t.toBuyShared(data.open_count, others) : " "}</p>
        </div>
      </div>

      <form className="grocery-add" onSubmit={add}>
        <TextField
          id="grocery-add"
          label={t.addItemPlaceholder}
          hideLabel
          placeholder={t.addItemPlaceholder}
          value={text}
          autoComplete="off"
          enterKeyHint="done"
          onChange={(e) => setText(e.target.value)}
        />
        <IconButton icon="add" label={t.addItem} variant="dark-square" type="submit" iconSize={26} />
      </form>
      {error && <p className="error-text">{error}</p>}

      <section className="section" style={{ marginTop: 12 }}>
        {data && openItems.length === 0 && <p className="empty">{t.groceryEmpty}</p>}
        <ul className="list">
          {openItems.map((item) => (
            <GroceryItem
              key={item.id}
              item={item}
              qty={groceryQty(item, t)}
              sources={grocerySources(item, t, memberName)}
              onToggle={() => toggle(item.id, true)}
            />
          ))}
        </ul>
      </section>

      {basket.length > 0 && (
        <section className="section">
          <div className="section__head">
            <h2 className="overline">{t.inBasket(basket.length)}</h2>
            <Button variant="ghost" size="sm" onClick={clear}>
              {t.clear}
            </Button>
          </div>
          <ul className="list">
            {basket.map((item) => (
              <GroceryItem
                key={item.id}
                item={item}
                qty={groceryQty(item, t)}
                sources={grocerySources(item, t, memberName)}
                onToggle={() => toggle(item.id, false)}
              />
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
