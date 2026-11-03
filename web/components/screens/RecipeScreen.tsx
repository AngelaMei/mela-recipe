"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import useSWR, { useSWRConfig } from "swr";

import { Button } from "@/components/core/Button";
import { Icon } from "@/components/core/Icon";
import { IconButton } from "@/components/core/IconButton";
import { Tabs } from "@/components/navigation/Tabs";
import { LogForm } from "@/components/recipe/LogForm";
import { IngredientRow } from "@/components/recipe/IngredientRow";
import { LogEntry } from "@/components/recipe/LogEntry";
import { Plate } from "@/components/recipe/Plate";
import { PlatePicker } from "@/components/recipe/PlatePicker";
import { plateDef } from "@/lib/plates";
import { StepRow } from "@/components/recipe/StepRow";
import { api } from "@/lib/api";
import { sourceGlyph } from "@/lib/format";
import { formatDate } from "@/lib/i18n";
import { useMemberName, usePrefs } from "@/lib/prefs";
import type { CookLog, Recipe } from "@/lib/types";

type Tab = "ingredients" | "steps" | "log";

export function RecipeScreen({ id }: { id: string }) {
  const { t, lang } = usePrefs();
  const router = useRouter();
  const memberName = useMemberName();
  const { mutate: globalMutate } = useSWRConfig();
  const { data: recipe, mutate, error } = useSWR<Recipe>(`/api/recipes/${id}`);

  const [tab, setTab] = useState<Tab>("ingredients");
  // Ticked ingredients are the ones to buy.
  const [toBuy, setToBuy] = useState<Set<number>>(new Set());
  const [added, setAdded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  // first: the "We made it!" cook, followed by choosing a plate
  const [logOpen, setLogOpen] = useState<{ log: CookLog | null; first?: boolean } | null>(null);

  useEffect(() => {
    setAdded(false);
  }, [toBuy]);

  const refreshLists = () => globalMutate((k) => typeof k === "string" && (k.startsWith("/api/recipes") || k.startsWith("/api/search")));

  if (error) {
    return (
      <main className="screen">
        <p className="empty">{t.genericError}</p>
      </main>
    );
  }
  if (!recipe) return <main className="hero linen" aria-busy="true" />;

  const made = recipe.made_count > 0;
  const linkOnly = recipe.ingredients.length === 0 && recipe.steps.length === 0;
  const logs = recipe.logs ?? [];
  const selected = recipe.ingredients.map((_, i) => i).filter((i) => toBuy.has(i));
  const allSelected = recipe.ingredients.length > 0 && selected.length === recipe.ingredients.length;

  const toggleToBuy = (i: number) =>
    setToBuy((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });

  const addSelected = async () => {
    setBusy(true);
    try {
      await api.post("/api/grocery/from-recipe", { recipe_id: recipe.id, indices: selected });
      await globalMutate("/api/grocery");
      setAdded(true);
    } finally {
      setBusy(false);
    }
  };

  // First cook: write the log (rating, note, photo...), then pick a plate.
  const weMadeIt = () => setLogOpen({ log: null, first: true });

  const choosePlate = async (plateId: string) => {
    await mutate(api.patch<Recipe>(`/api/recipes/${recipe.id}`, { plate_id: plateId }), { revalidate: false });
    refreshLists();
    setPickerOpen(false);
  };

  const sourceLabel = t.sourceLabel[recipe.source];
  const meta: React.ReactNode[] = [made ? t.madeTimes(recipe.made_count) : t.notMadeYet];
  if (recipe.avg_rating) meta.push(<span key="r" aria-label={t.ratingOf(recipe.avg_rating)}>{t.avgRating(recipe.avg_rating)}</span>);
  if (recipe.last_cooked) meta.push(t.last(formatDate(recipe.last_cooked, lang)));
  if (recipe.source_url && sourceLabel)
    meta.push(
      <a key="s" href={recipe.source_url} target="_blank" rel="noreferrer">
        {sourceLabel}
        <Icon name="open_in_new" size={15} />
      </a>,
    );

  // Sticky CTA per tab
  let cta: React.ReactNode = null;
  if (tab === "ingredients" && recipe.ingredients.length > 0) {
    if (added) {
      cta = <Button variant="primary" block done disabled icon="check">{t.addedToGrocery}</Button>;
    } else {
      cta = (
        <Button variant="primary" block onClick={addSelected} disabled={busy || selected.length === 0}>
          {selected.length ? t.addToGrocery(selected.length) : t.tickToAdd}
        </Button>
      );
    }
  } else if (tab !== "ingredients" || linkOnly) {
    cta = made ? (
      <Button variant="dark" block onClick={() => setLogOpen({ log: null })}>
        {t.logToday}
      </Button>
    ) : (
      <Button variant="primary" block onClick={weMadeIt} disabled={busy}>
        {t.weMadeIt}
      </Button>
    );
  }

  return (
    <main>
      <div className={made ? `hero cloth cloth--${plateDef(recipe.plate_id).cloth}` : "hero linen"}>
        <IconButton
          className="hero__back"
          icon="chevron_left"
          iconSize={26}
          label={t.back}
          variant="overlay"
          onClick={() => (window.history.length > 1 ? router.back() : router.push("/"))}
        />
        <div className="hero__actions">
          {made && (
            <button type="button" className="hero__change pressable" onClick={() => setPickerOpen(true)}>
              {t.changePlate}
            </button>
          )}
          <IconButton
            icon="edit"
            iconSize={20}
            label={t.editRecipe}
            variant="overlay"
            onClick={() => router.push(`/recipes/${recipe.id}/edit`)}
          />
        </div>
        <Plate
          size={200}
          plateId={recipe.plate_id}
          photoUrl={recipe.photo_url}
          photoCrop={recipe.photo_crop}
          empty={!made}
          glyph={!made ? sourceGlyph(recipe.source) : undefined}
          label={recipe.name}
        />
      </div>

      <div className="detail">
        <h1 className="title">{recipe.name}</h1>
        {recipe.name_alt && <p className="detail__alt">{recipe.name_alt}</p>}
        <div className="meta-row">
          {meta.map((m, i) => (
            <span key={i} style={{ display: "contents" }}>
              {i > 0 && <span className="meta-row__sep" aria-hidden="true">·</span>}
              <span>{m}</span>
            </span>
          ))}
        </div>
        {!made && recipe.note && <p className="saved-note">{recipe.note}</p>}

        {linkOnly ? (
          <div className="notice">
            <Icon name="content_paste" />
            <div>
              <strong style={{ color: "var(--text-primary)" }}>{t.linkOnlyTitle}</strong>
              <div className="muted">{t.linkOnlyBody}</div>
              <div className="notice__actions">
                <Button size="sm" variant="secondary" icon="add" onClick={() => router.push(`/recipes/${recipe.id}/edit`)}>
                  {t.addIngredientsAndSteps}
                </Button>
                {recipe.source_url && (
                  <Button size="sm" variant="secondary" icon="open_in_new" onClick={() => window.open(recipe.source_url!, "_blank", "noopener")}>
                    {t.openOriginal}
                  </Button>
                )}
              </div>
            </div>
          </div>
        ) : (
          <>
            <Tabs
              idPrefix="recipe"
              label={recipe.name}
              value={tab}
              onChange={setTab}
              tabs={[
                { value: "ingredients", label: t.ingredients },
                { value: "steps", label: t.steps(recipe.steps.length) },
                { value: "log", label: t.log(logs.length) },
              ]}
            />
            <div role="tabpanel" id={`recipe-panel-${tab}`} aria-labelledby={`recipe-tab-${tab}`}>
              {tab === "ingredients" &&
                (recipe.ingredients.length ? (
                  <>
                    <div className="tab-hint tab-hint--row">
                      <span>{t.tickToBuy}</span>
                      <button
                        type="button"
                        className="link"
                        onClick={() => setToBuy(allSelected ? new Set() : new Set(recipe.ingredients.map((_, i) => i)))}
                      >
                        {allSelected ? t.clearSelection : t.selectAll}
                      </button>
                    </div>
                    <ul className="list">
                      {recipe.ingredients.map((ing, i) => (
                        <IngredientRow key={i} ingredient={ing} selected={toBuy.has(i)} onToggle={() => toggleToBuy(i)} />
                      ))}
                    </ul>
                  </>
                ) : (
                  <p className="empty">{t.noIngredients}</p>
                ))}
              {tab === "steps" &&
                (recipe.steps.length ? (
                  <ol className="list">
                    {recipe.steps.map((s, i) => (
                      <StepRow key={i} index={i} text={s} />
                    ))}
                  </ol>
                ) : (
                  <p className="empty">{t.noSteps}</p>
                ))}
              {tab === "log" &&
                (logs.length ? (
                  <ul className="list">
                    {logs.map((log) => (
                      <LogEntry
                        key={log.id}
                        log={log}
                        date={formatDate(log.cooked_on, lang)}
                        ratingLabel={log.rating ? t.ratingOf(log.rating) : undefined}
                        tweaksLabel={t.tweaks}
                        byLabel={t.by(memberName(log.created_by))}
                        onOpen={() => setLogOpen({ log })}
                      />
                    ))}
                  </ul>
                ) : (
                  <p className="empty">{t.noLogs}</p>
                ))}
            </div>
          </>
        )}

      </div>

      {cta && <div className="sticky-cta">{cta}</div>}

      <PlatePicker
        open={pickerOpen}
        current={recipe.plate_id}
        photoUrl={recipe.photo_url}
        photoCrop={recipe.photo_crop}
        onClose={() => setPickerOpen(false)}
        onChoose={choosePlate}
      />
      <LogForm
        open={!!logOpen}
        recipeId={recipe.id}
        plateId={recipe.plate_id}
        log={logOpen?.log ?? null}
        title={logOpen?.first ? t.firstCookTitle : undefined}
        onClose={() => setLogOpen(null)}
        onSaved={async () => {
          const first = logOpen?.first;
          setLogOpen(null);
          await mutate();
          refreshLists();
          if (first) setPickerOpen(true); // a plate is picked after the first cook
        }}
      />
    </main>
  );
}
