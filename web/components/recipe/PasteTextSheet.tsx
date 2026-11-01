"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/core/Button";
import { TextArea } from "@/components/forms/TextField";
import { Sheet } from "@/components/overlays/Sheet";
import { usePrefs } from "@/lib/prefs";
import type { Ingredient, SplitOptions } from "@/lib/types";
import { DEFAULT_SPLIT, useParse } from "@/lib/useParse";

import { ParsePreview, SplitToggles } from "./ParsePreview";

/** For link-only recipes: paste the text later and save the parsed ingredients and steps. */
export function PastePreviewSheet({
  open,
  onClose,
  onSave,
}: {
  open: boolean;
  onClose: () => void;
  onSave: (ingredients: Ingredient[], steps: string[]) => Promise<void>;
}) {
  const { t } = usePrefs();
  const [text, setText] = useState("");
  const [split, setSplit] = useState<SplitOptions>(DEFAULT_SPLIT);
  const [saving, setSaving] = useState(false);
  const { result, steps, merge, ensure } = useParse(text, "", split);

  useEffect(() => {
    if (open) setText("");
  }, [open]);

  const ingredients = result?.ingredients ?? [];
  const found = ingredients.length + steps.length > 0;

  return (
    <Sheet open={open} title={t.pasteSheetTitle} onClose={onClose}>
      <div className="add__stack">
        <TextArea
          id="paste-later"
          label={t.recipeTextLabel}
          hideLabel
          icon="content_paste"
          rows={4}
          placeholder={t.captionPlaceholder}
          value={text}
          onChange={(e) => setText(e.target.value)}
          helper={text.trim() && result ? (found ? t.textFound(ingredients.length, steps.length) : t.textNothing) : null}
          helperTone={found ? "success" : "default"}
          helperIcon={found ? "check_circle" : undefined}
        />
        {text.trim() && <SplitToggles split={split} onChange={setSplit} t={t} />}
        <ParsePreview ingredients={ingredients} steps={steps} onMerge={merge} t={t} />
        <Button
          variant="primary"
          block
          disabled={!text.trim() || saving}
          onClick={async () => {
            setSaving(true);
            try {
              const fresh = await ensure();
              if (fresh.result) await onSave(fresh.result.ingredients, fresh.steps.map((s) => s.text));
            } finally {
              setSaving(false);
            }
          }}
        >
          {t.saveRecipeText}
        </Button>
      </div>
    </Sheet>
  );
}
