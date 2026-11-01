"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useSWRConfig } from "swr";

import { TextArea, TextField } from "@/components/forms/TextField";
import { TopBar } from "@/components/navigation/TopBar";
import { ParsePreview, SplitToggles } from "@/components/recipe/ParsePreview";
import { api } from "@/lib/api";
import { usePrefs } from "@/lib/prefs";
import type { Recipe, SplitOptions } from "@/lib/types";
import { DEFAULT_SPLIT, useParse } from "@/lib/useParse";

function detect(text: string): "youtube" | "instagram" | "link" | "text" {
  const s = text.trim();
  if (!s || /\s/.test(s)) return "text";
  const low = s.toLowerCase();
  if (low.includes("youtu.be") || low.includes("youtube.com")) return "youtube";
  if (low.includes("instagram.com")) return "instagram";
  if (/^(https?:\/\/)?([\w-]+\.)+[a-z]{2,}([/?#]\S*)?$/i.test(s)) return "link";
  return "text";
}

export function AddScreen() {
  const { t, lang } = usePrefs();
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const [input, setInput] = useState("");
  const [caption, setCaption] = useState("");
  const [name, setName] = useState("");
  const [nameAlt, setNameAlt] = useState("");
  const [note, setNote] = useState("");
  const [split, setSplit] = useState<SplitOptions>(DEFAULT_SPLIT);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const source = detect(input);
  const { result, steps, loading, merge, ensure } = useParse(input, source === "text" ? "" : caption, split);
  const current = result && result.source === source ? result : null;
  const ingredients = current?.ingredients ?? [];

  // Helper under the paste field
  let helper: React.ReactNode = null;
  let helperTone: "default" | "success" = "default";
  let helperIcon: string | undefined;
  let showCaption = false;
  let captionHelper: string | null = null;

  if (source === "youtube") {
    showCaption = !!caption.trim() || (!!current && current.status !== "ok");
    if (caption.trim()) {
      if (current?.status === "ok") {
        helper = t.textFound(ingredients.length, steps.length);
        helperTone = "success";
        helperIcon = "check_circle";
      }
    } else if (!current || loading) {
      helper = t.ytReading;
      helperIcon = "play_circle";
    } else if (current.status === "ok") {
      helper = t.ytFound(ingredients.length, steps.length);
      helperTone = "success";
      helperIcon = "check_circle";
    } else if (current.status === "fetch_failed") {
      helper = t.ytFailed;
      helperIcon = "play_circle";
    } else {
      helper = t.ytEmpty;
      helperIcon = "play_circle";
    }
  } else if (source === "instagram") {
    helper = t.igHelper;
    helperIcon = "photo_camera";
    showCaption = true;
    if (!caption.trim()) captionHelper = t.linkOnly;
    else if (current?.status === "empty") captionHelper = t.postNoRecipe;
    else if (current?.status === "ok") captionHelper = t.textFound(ingredients.length, steps.length);
  } else if (source === "link") {
    helper = t.linkOnly;
    helperIcon = "open_in_new";
  } else if (input.trim() && current) {
    if (current.status === "ok") {
      helper = t.textFound(ingredients.length, steps.length);
      helperTone = "success";
      helperIcon = "check_circle";
    } else {
      helper = t.textNothing;
    }
  }

  const canSave = !!input.trim() && !saving && (source !== "text" || ingredients.length + steps.length > 0 || loading);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const fresh = await ensure();
      const r = fresh.result;
      if (!r) throw new Error("parse failed");
      const recipe = await api.post<Recipe>("/api/recipes", {
        name: name.trim() || null,
        name_alt: nameAlt.trim() || null,
        note: note.trim() || null,
        source: r.source === "text" ? "manual" : r.source,
        source_url: r.url,
        ingredients: r.ingredients,
        steps: fresh.steps.map((s) => s.text),
      });
      await mutate((k) => typeof k === "string" && k.startsWith("/api/recipes"));
      router.replace(`/recipes/${recipe.id}`);
    } catch {
      setError(t.genericError);
      setSaving(false);
    }
  };

  return (
    <main>
      <TopBar
        title={t.newRecipe}
        start={
          <button type="button" className="topbar__link" onClick={() => router.back()}>
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
        <TextArea
          id="paste"
          label={t.pasteLabel}
          icon="content_paste"
          placeholder={t.pastePlaceholder}
          value={input}
          rows={source === "text" ? 4 : 1}
          autoFocus
          onChange={(e) => setInput(e.target.value)}
          helper={helper}
          helperTone={helperTone}
          helperIcon={helperIcon}
        />

        {showCaption && (
          <TextArea
            id="caption"
            label={source === "instagram" ? t.captionLabel : t.recipeTextLabel}
            placeholder={t.captionPlaceholder}
            value={caption}
            rows={3}
            onChange={(e) => setCaption(e.target.value)}
            helper={captionHelper}
          />
        )}

        <TextField
          id="name"
          label={t.nameLabel}
          placeholder={t.namePlaceholder}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <TextField
          id="name-alt"
          label={t.altNameLabel}
          value={nameAlt}
          lang={lang === "en" ? "zh-Hant" : "en"}
          onChange={(e) => setNameAlt(e.target.value)}
        />
        <TextField
          id="note"
          label={t.savedNoteLabel}
          placeholder={t.savedNotePlaceholder}
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />

        {(source === "text" || source === "youtube" || (source === "instagram" && caption.trim())) && input.trim() && (
          <SplitToggles split={split} onChange={setSplit} t={t} />
        )}

        {error && <p className="error-text">{error}</p>}

        <ParsePreview ingredients={ingredients} steps={current ? steps : []} onMerge={merge} t={t} />
      </div>
    </main>
  );
}
