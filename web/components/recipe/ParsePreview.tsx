"use client";

import { Chip } from "@/components/core/Chip";
import { Icon } from "@/components/core/Icon";
import { ingredientQty } from "@/lib/format";
import type { Strings } from "@/lib/i18n";
import type { Ingredient, ParsedStep, SplitOptions } from "@/lib/types";

import { StepRow } from "./StepRow";

export function SplitToggles({ split, onChange, t }: { split: SplitOptions; onChange: (s: SplitOptions) => void; t: Strings }) {
  const opts: { key: keyof SplitOptions; label: string }[] = [
    { key: "line", label: t.splitLine },
    { key: "comma", label: t.splitComma },
    { key: "number", label: t.splitNumber },
    { key: "period", label: t.splitPeriod },
  ];
  return (
    <div>
      <p className="field__label split-label">{t.splitSteps}</p>
      <div className="chip-row chip-row--wrap" role="group" aria-label={t.splitSteps}>
        {opts.map((o) => (
          <Chip key={o.key} selected={split[o.key]} onClick={() => onChange({ ...split, [o.key]: !split[o.key] })}>
            {split[o.key] && <Icon name="check" size={16} />}
            {o.label}
          </Chip>
        ))}
      </div>
    </div>
  );
}

export function ParsePreview({
  ingredients,
  steps,
  onMerge,
  t,
}: {
  ingredients: Ingredient[];
  steps: ParsedStep[];
  onMerge: (i: number) => void;
  t: Strings;
}) {
  if (!ingredients.length && !steps.length) return null;
  return (
    <div>
      <h2 className="overline" style={{ marginBottom: 10 }}>
        {t.preview}
      </h2>
      {ingredients.length > 0 && (
        <div className="group" style={{ marginBottom: 14 }}>
          <div className="group__head">
            <Icon name="check_circle" size={18} />
            {t.ingredients} · {ingredients.length}
          </div>
          {ingredients.map((ing, i) => (
            <div className="group__row" key={i}>
              <span>{ing.name}</span>
              <span className="group__value">{ingredientQty(ing)}</span>
            </div>
          ))}
        </div>
      )}
      {steps.length > 0 && (
        <div className="group" style={{ padding: "0 16px" }}>
          <ol className="list">
            {steps.map((s, i) => (
              <StepRow
                key={`${i}-${s.text}`}
                index={i}
                text={s.text}
                onMerge={s.short && i > 0 ? () => onMerge(i) : undefined}
                mergeLabel={t.merge}
              />
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
