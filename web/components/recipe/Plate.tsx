"use client";

import { useEffect, useState } from "react";

import { loadPlateManifest, plateDef } from "@/lib/plates";

import { Icon } from "../core/Icon";

export interface PlateProps {
  plateId?: string | null;
  size: number;
  photoUrl?: string | null;
  /** Dashed empty plate = "not made yet" */
  empty?: boolean;
  glyph?: string;
  label?: string;
  selected?: boolean;
  decorative?: boolean;
}

/**
 * Four layers: rim (glaze or designer image) → well (inset 13%) → dish photo
 * (inset 22%, circle crop) → 145° light overlay. The drop shadow is CSS.
 */
export function Plate({ plateId, size, photoUrl, empty, glyph, label, selected, decorative }: PlateProps) {
  const [, force] = useState(0);
  useEffect(() => {
    loadPlateManifest().then(() => force((n) => n + 1));
  }, []);

  const a11y = decorative ? { "aria-hidden": true as const } : { role: "img", "aria-label": label };
  const sizeStyle = { "--plate-size": `${size}px` } as React.CSSProperties;

  if (empty) {
    return (
      <span className={`plate plate--empty${selected ? " plate--selected" : ""}`} style={sizeStyle} {...a11y}>
        {glyph && <Icon name={glyph} />}
      </span>
    );
  }

  const def = plateDef(plateId ?? "speckle") ?? plateDef("speckle");
  const id = def?.id ?? "speckle";
  const style = {
    ...sizeStyle,
    "--glaze": `var(--glaze-${id})`,
    "--well": `var(--well-${id})`,
    ...(def?.foodInset ? { "--food-inset": `${def.foodInset}%` } : {}),
  } as React.CSSProperties;

  return (
    <span className={`plate${selected ? " plate--selected" : ""}`} style={style} {...a11y}>
      {def?.image && <img className="plate__rim-img" src={def.image} alt="" />}
      {!def?.image && <span className="plate__well" />}
      {photoUrl && (
        <span className="plate__food">
          <img src={photoUrl} alt="" loading="lazy" />
        </span>
      )}
      <span className="plate__light" />
    </span>
  );
}
