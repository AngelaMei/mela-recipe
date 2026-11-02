"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/core/Button";
import { Sheet } from "@/components/overlays/Sheet";
import type { PhotoCrop } from "@/lib/crop";
import { DEFAULT_PLATE, PLATES, plateDef } from "@/lib/plates";
import { usePrefs } from "@/lib/prefs";

import { Plate } from "./Plate";

export interface PlatePickerProps {
  open: boolean;
  current: string | null;
  photoUrl: string | null;
  photoCrop: PhotoCrop | null;
  onClose: () => void;
  onChoose: (plateId: string) => Promise<void> | void;
}

/** "Choose a plate": 160px preview, plate name, 4×2 grid, "Use this plate". */
export function PlatePicker({ open, current, photoUrl, photoCrop, onClose, onChoose }: PlatePickerProps) {
  const { t, lang } = usePrefs();
  const [selected, setSelected] = useState(plateDef(current ?? DEFAULT_PLATE).id);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) setSelected(plateDef(current ?? DEFAULT_PLATE).id);
  }, [open, current]);

  const plate = PLATES.find((p) => p.id === selected) ?? PLATES[0];

  return (
    <Sheet open={open} title={t.choosePlate} onClose={onClose}>
      <div className={`picker__preview cloth cloth--${plate.cloth}`}>
        <Plate size={150} plateId={plate.id} photoUrl={photoUrl} photoCrop={photoCrop} decorative />
      </div>
      <p className="picker__name" aria-live="polite">
        {plate.name[lang]}
      </p>
      <div className="picker__grid" role="radiogroup" aria-label={t.choosePlate}>
        {PLATES.map((p) => (
          <button
            key={p.id}
            type="button"
            role="radio"
            aria-checked={p.id === selected}
            aria-label={p.name[lang]}
            className="pressable"
            onClick={() => setSelected(p.id)}
          >
            <Plate size={72} plateId={p.id} selected={p.id === selected} decorative />
          </button>
        ))}
      </div>
      <Button
        variant="primary"
        block
        disabled={saving}
        onClick={async () => {
          setSaving(true);
          try {
            await onChoose(selected);
          } finally {
            setSaving(false);
          }
        }}
      >
        {t.usePlate}
      </Button>
    </Sheet>
  );
}
