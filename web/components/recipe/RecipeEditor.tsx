"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/core/Button";
import { IconButton } from "@/components/core/IconButton";
import { SegmentedControl } from "@/components/forms/SegmentedControl";
import { TextArea, TextField } from "@/components/forms/TextField";
import { TopBar } from "@/components/navigation/TopBar";
import { api } from "@/lib/api";
import { useDebounced } from "@/lib/hooks";
import type { Strings } from "@/lib/i18n";
import { usePrefs } from "@/lib/prefs";
import type { Ingredient, ParseResult, Recipe, Source } from "@/lib/types";

/*
 * New / edit recipe.
 *
 * Ingredients and steps each have two ways in, and you can switch any time:
 *  - "Type a list": a big box, one per line. Ingredient lines are split into
 *    name + amount by the server (POST /api/parse/lines) and previewed live.
 *  - "One by one": a row per item with an "Add" button. For ingredients the
 *    name and amount are separate fields, so nothing is guessed.
 * Amounts are saved exactly as typed.
 */

type Mode = "list" | "rows";
interface IngRow {
  id: number;
  name: string;
  portion: string;
}
interface StepItem {
  id: number;
  text: string;
}

export interface RecipeDraft {
  name: string;
  name_alt: string | null;
  note: string | null;
  source: Source;
  source_url: string | null;
  ingredients: { name: string; portion: string | null }[];
  steps: string[];
}

let nextId = 1;
const newId = () => nextId++;

function detectSource(url: string): Source {
  const s = url.trim().toLowerCase();
  if (!s) return "manual";
  if (s.includes("youtu.be") || s.includes("youtube.com")) return "youtube";
  if (s.includes("instagram.com")) return "instagram";
  return "link";
}

const STEP_PREFIX = /^\s*(?:[-–—•*·▪◦●○→>✓✔]+|(?:step\s*)?\d{1,2}\s*[.)、:：](?!\d)|[①-⑳])\s*/i;

/** One step per line. Leading "1." / "Step 2:" / bullets are removed; blank lines are skipped. */
function stepsFromText(text: string): string[] {
  return text
    .split("\n")
    .map((l) => l.replace(STEP_PREFIX, "").trim())
    .filter(Boolean);
}

const ingLine = (r: { name: string; portion: string | null }) => `${r.name} ${r.portion ?? ""}`.trim();
const toRows = (ings: { name: string; portion: string | null }[]): IngRow[] =>
  ings.map((i) => ({ id: newId(), name: i.name, portion: i.portion ?? "" }));

/** Live split of the ingredient box into name + amount, from the server. */
function useIngredientLines(text: string) {
  const debounced = useDebounced(text, 250);
  const [parsed, setParsed] = useState<{ text: string; items: Ingredient[] }>({ text: "", items: [] });

  const parse = useCallback(async (value: string): Promise<Ingredient[]> => {
    if (!value.trim()) return [];
    const res = await api.post<{ ingredients: Ingredient[] }>("/api/parse/lines", { text: value });
    return res.ingredients;
  }, []);

  useEffect(() => {
    let live = true;
    parse(debounced)
      .then((items) => live && setParsed({ text: debounced, items }))
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [debounced, parse]);

  /** The split for exactly this text (parses now if the preview is behind). */
  const ensure = useCallback(
    async (value: string) => (parsed.text === value ? parsed.items : parse(value)),
    [parsed, parse],
  );
  return { preview: parsed.text === text ? parsed.items : null, ensure };
}

export function RecipeEditor({
  title,
  initial,
  onCancel,
  onSave,
}: {
  title: string;
  initial?: Recipe;
  onCancel: () => void;
  onSave: (draft: RecipeDraft) => Promise<void>;
}) {
  const { t, lang } = usePrefs();
  const editing = !!initial;

  const [name, setName] = useState(initial?.name === "Untitled recipe" ? "" : initial?.name ?? "");
  const [nameAlt, setNameAlt] = useState(initial?.name_alt ?? "");
  const [note, setNote] = useState(initial?.note ?? "");
  const [url, setUrl] = useState(initial?.source_url ?? "");

  // Editing an existing recipe opens one-by-one; a new one opens with the big boxes.
  const initialIngs = (initial?.ingredients ?? []).map((i) => ({ name: i.name, portion: i.portion ?? null }));
  const [ingMode, setIngMode] = useState<Mode>(editing && initialIngs.length ? "rows" : "list");
  const [ingText, setIngText] = useState(initialIngs.map(ingLine).join("\n"));
  const [ingRows, setIngRows] = useState<IngRow[]>(toRows(initialIngs));
  const [stepMode, setStepMode] = useState<Mode>(editing && initial?.steps.length ? "rows" : "list");
  const [stepText, setStepText] = useState((initial?.steps ?? []).join("\n"));
  const [stepRows, setStepRows] = useState<StepItem[]>((initial?.steps ?? []).map((s) => ({ id: newId(), text: s })));

  const [importState, setImportState] = useState<"idle" | "busy" | { msg: string; ok: boolean }>("idle");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const focusId = useRef<number | null>(null);

  const { preview, ensure } = useIngredientLines(ingText);
  const source = detectSource(url);
  const listSteps = stepsFromText(stepText);

  // Focus a row that was just added
  useEffect(() => {
    if (focusId.current === null) return;
    const el = document.querySelector<HTMLElement>(`[data-row="${focusId.current}"]`);
    el?.focus();
    focusId.current = null;
  });

  // ----- mode switches keep the content -----
  const switchIngMode = async (mode: Mode) => {
    if (mode === ingMode) return;
    if (mode === "rows") {
      const items = await ensure(ingText);
      const rows = toRows(items);
      setIngRows(rows.length ? rows : [{ id: newId(), name: "", portion: "" }]);
    } else {
      setIngText(ingRows.filter((r) => r.name.trim()).map(ingLine).join("\n"));
    }
    setIngMode(mode);
  };
  const switchStepMode = (mode: Mode) => {
    if (mode === stepMode) return;
    if (mode === "rows") {
      const rows = listSteps.map((s) => ({ id: newId(), text: s }));
      setStepRows(rows.length ? rows : [{ id: newId(), text: "" }]);
    } else {
      setStepText(stepRows.map((s) => s.text.trim()).filter(Boolean).join("\n"));
    }
    setStepMode(mode);
  };

  // ----- one-by-one editing -----
  const addIngRow = (after?: number) => {
    const row = { id: newId(), name: "", portion: "" };
    focusId.current = row.id;
    setIngRows((rows) => {
      const i = after === undefined ? rows.length : rows.findIndex((r) => r.id === after) + 1;
      return [...rows.slice(0, i), row, ...rows.slice(i)];
    });
  };
  const updateIngRow = (id: number, patch: Partial<IngRow>) =>
    setIngRows((rows) => rows.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  const removeIngRow = (id: number) => setIngRows((rows) => rows.filter((r) => r.id !== id));

  const addStepRow = (after?: number) => {
    const row = { id: newId(), text: "" };
    focusId.current = row.id;
    setStepRows((rows) => {
      const i = after === undefined ? rows.length : rows.findIndex((r) => r.id === after) + 1;
      return [...rows.slice(0, i), row, ...rows.slice(i)];
    });
  };
  const updateStepRow = (id: number, text: string) =>
    setStepRows((rows) => rows.map((r) => (r.id === id ? { ...r, text } : r)));
  const removeStepRow = (id: number) => setStepRows((rows) => rows.filter((r) => r.id !== id));

  // ----- import from a YouTube description -----
  const hasContent = !!ingText.trim() || ingRows.some((r) => r.name.trim()) || !!stepText.trim() || stepRows.some((s) => s.text.trim());
  const importFromVideo = async () => {
    if (hasContent && !window.confirm(t.replaceConfirm)) return;
    setImportState("busy");
    try {
      const r = await api.post<ParseResult>("/api/parse", { input: url.trim() });
      if (r.status === "fetch_failed") return setImportState({ msg: t.importFailed, ok: false });
      if (r.status !== "ok") return setImportState({ msg: t.importEmpty, ok: false });
      setIngText(r.ingredients.map(ingLine).join("\n"));
      setIngRows(toRows(r.ingredients));
      setStepText(r.steps.map((s) => s.text).join("\n"));
      setStepRows(r.steps.map((s) => ({ id: newId(), text: s.text })));
      setIngMode("list");
      setStepMode("list");
      setImportState({ msg: t.imported(r.ingredients.length, r.steps.length), ok: true });
    } catch {
      setImportState({ msg: t.importFailed, ok: false });
    }
  };

  // ----- save -----
  const ingCount = ingMode === "list" ? (preview?.length ?? ingText.split("\n").filter((l) => l.trim()).length) : ingRows.filter((r) => r.name.trim()).length;
  const stepCount = stepMode === "list" ? listSteps.length : stepRows.filter((s) => s.text.trim()).length;
  const canSave = !saving && (!!name.trim() || !!url.trim() || ingCount > 0 || stepCount > 0);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const ingredients =
        ingMode === "list"
          ? (await ensure(ingText)).map((i) => ({ name: i.name, portion: i.portion }))
          : ingRows
              .filter((r) => r.name.trim())
              .map((r) => ({ name: r.name.trim(), portion: r.portion.trim() || null }));
      const steps = stepMode === "list" ? listSteps : stepRows.map((s) => s.text.trim()).filter(Boolean);
      await onSave({
        name: name.trim(),
        name_alt: nameAlt.trim() || null,
        note: note.trim() || null,
        source,
        source_url: url.trim() || null,
        ingredients,
        steps,
      });
    } catch {
      setError(t.genericError);
      setSaving(false);
    }
  };

  const modeOptions = [
    { value: "list" as Mode, label: t.modeList },
    { value: "rows" as Mode, label: t.modeRows },
  ];

  return (
    <main>
      <TopBar
        title={title}
        start={
          <button type="button" className="topbar__link" onClick={onCancel}>
            {t.cancel}
          </button>
        }
        end={
          <button type="button" className="topbar__link topbar__link--accent" onClick={save} disabled={!canSave}>
            {saving ? t.saving : t.save}
          </button>
        }
      />

      <div className="add add__stack">
        <TextField id="name" label={t.nameLabel} placeholder={t.namePlaceholder} value={name} onChange={(e) => setName(e.target.value)} />
        <TextField
          id="name-alt"
          label={t.altNameLabel}
          value={nameAlt}
          lang={lang === "en" ? "zh-Hant" : "en"}
          onChange={(e) => setNameAlt(e.target.value)}
        />

        <div>
          <TextField
            id="link"
            label={t.linkLabel}
            icon="open_in_new"
            type="url"
            inputMode="url"
            autoComplete="off"
            placeholder={t.linkPlaceholder}
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              setImportState("idle");
            }}
            helper={source === "instagram" ? t.igHelper : source !== "manual" && source !== "youtube" ? t.linkHelper : null}
            helperIcon={source === "instagram" ? "photo_camera" : undefined}
          />
          {source === "youtube" && (
            <div style={{ marginTop: 10 }}>
              <Button size="sm" icon="play_circle" onClick={importFromVideo} disabled={importState === "busy"}>
                {importState === "busy" ? t.importing : t.importFromVideo}
              </Button>
              {typeof importState === "object" && (
                <p className={`field__helper${importState.ok ? " field__helper--success" : ""}`} aria-live="polite">
                  {importState.msg}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Ingredients */}
        <section className="editor-section" aria-labelledby="ing-head">
          <div className="editor-section__head">
            <h2 id="ing-head" className="heading">
              {t.ingredients}
            </h2>
            <span className="muted editor-section__count">{ingCount > 0 ? t.ingCount(ingCount) : ""}</span>
          </div>
          <SegmentedControl label={`${t.ingredients}: ${t.inputMode}`} value={ingMode} onChange={switchIngMode} options={modeOptions} />

          {ingMode === "list" ? (
            <>
              <TextArea
                id="ing-list"
                className="editor-box"
                label={t.ingListLabel}
                hideLabel
                rows={6}
                placeholder={t.ingListPlaceholder}
                value={ingText}
                onChange={(e) => setIngText(e.target.value)}
                helper={t.ingListHelper}
              />
              {preview && preview.length > 0 && <IngredientPreview items={preview} t={t} />}
            </>
          ) : (
            <>
              <ul className="list editor-rows">
                {ingRows.map((row, i) => (
                  <li className="editor-row" key={row.id}>
                    <input
                      data-row={row.id}
                      className="editor-input editor-input--name"
                      aria-label={`${t.ingName} ${i + 1}`}
                      placeholder={t.ingNamePlaceholder}
                      value={row.name}
                      enterKeyHint="next"
                      onChange={(e) => updateIngRow(row.id, { name: e.target.value })}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                          e.preventDefault();
                          (e.currentTarget.nextElementSibling as HTMLElement | null)?.focus();
                        }
                      }}
                    />
                    <input
                      className="editor-input editor-input--portion"
                      aria-label={`${t.portion} ${i + 1}`}
                      placeholder={t.portionPlaceholder}
                      value={row.portion}
                      enterKeyHint="next"
                      onChange={(e) => updateIngRow(row.id, { portion: e.target.value })}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                          e.preventDefault();
                          addIngRow(row.id);
                        }
                      }}
                    />
                    <IconButton icon="close" variant="plain" iconSize={20} label={t.removeIngredient(row.name)} onClick={() => removeIngRow(row.id)} />
                  </li>
                ))}
              </ul>
              <Button block icon="add" onClick={() => addIngRow()}>
                {t.addIngredient}
              </Button>
            </>
          )}
        </section>

        {/* Steps */}
        <section className="editor-section" aria-labelledby="step-head">
          <div className="editor-section__head">
            <h2 id="step-head" className="heading">
              {t.stepsTitle}
            </h2>
            <span className="muted editor-section__count">{stepCount > 0 ? t.stepCount(stepCount) : ""}</span>
          </div>
          <SegmentedControl label={`${t.stepsTitle}: ${t.inputMode}`} value={stepMode} onChange={switchStepMode} options={modeOptions} />

          {stepMode === "list" ? (
            <>
              <TextArea
                id="step-list"
                className="editor-box"
                label={t.stepListLabel}
                hideLabel
                rows={6}
                placeholder={t.stepListPlaceholder}
                value={stepText}
                onChange={(e) => setStepText(e.target.value)}
                helper={t.stepListHelper}
              />
              {listSteps.length > 0 && (
                <ol className="group editor-preview">
                  {listSteps.map((s, i) => (
                    <li className="editor-preview__step" key={i}>
                      <span className="step-row__num">{i + 1}</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ol>
              )}
            </>
          ) : (
            <>
              <ol className="list editor-rows">
                {stepRows.map((row, i) => (
                  <li className="editor-step" key={row.id}>
                    <span className="step-row__num editor-step__num">{i + 1}</span>
                    <AutoTextArea
                      dataRow={row.id}
                      label={t.stepPlaceholder(i + 1)}
                      value={row.text}
                      onChange={(v) => updateStepRow(row.id, v)}
                      onEnter={() => addStepRow(row.id)}
                    />
                    <IconButton icon="close" variant="plain" iconSize={20} label={t.removeStep(i + 1)} onClick={() => removeStepRow(row.id)} />
                  </li>
                ))}
              </ol>
              <Button block icon="add" onClick={() => addStepRow()}>
                {t.addStep}
              </Button>
            </>
          )}
        </section>

        <TextField id="note" label={t.savedNoteLabel} placeholder={t.savedNotePlaceholder} value={note} onChange={(e) => setNote(e.target.value)} />

        {error && <p className="error-text">{error}</p>}
        {!canSave && !saving && <p className="field__helper">{t.nothingToSave}</p>}
      </div>
    </main>
  );
}

function IngredientPreview({ items, t }: { items: Ingredient[]; t: Strings }) {
  return (
    <ul className="group editor-preview" aria-label={t.ingredients}>
      {items.map((ing, i) => (
        <li className="group__row" key={i}>
          <span>{ing.name}</span>
          {ing.portion ? <span className="group__value">{ing.portion}</span> : <span className="editor-preview__none">{t.noAmount}</span>}
        </li>
      ))}
    </ul>
  );
}

/** A step: grows with its text. Enter adds the next step; Shift+Enter makes a new line. */
function AutoTextArea({
  dataRow,
  label,
  value,
  onChange,
  onEnter,
}: {
  dataRow: number;
  label: string;
  value: string;
  onChange: (v: string) => void;
  onEnter: () => void;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);
  return (
    <textarea
      ref={ref}
      data-row={dataRow}
      className="editor-input editor-input--step"
      rows={1}
      aria-label={label}
      placeholder={label}
      value={value}
      enterKeyHint="next"
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
          e.preventDefault();
          onEnter();
        }
      }}
    />
  );
}
