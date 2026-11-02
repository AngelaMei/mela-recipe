"use client";

import { Plate } from "@/components/recipe/Plate";
import { PLATES } from "@/lib/plates";
import { usePrefs } from "@/lib/prefs";

/** /plates: the plate collection on its tablecloths, at the sizes the app uses. */
export function PlateSpecimen() {
  const { lang } = usePrefs();
  return (
    <main className="specimen">
      <div className="specimen__grid">
        {PLATES.map((p) => (
          <figure key={p.id} className="specimen__cell">
            <div className={`specimen__cloth cloth cloth--${p.cloth}`}>
              <Plate size={150} plateId={p.id} label={p.name[lang]} />
            </div>
            <figcaption>
              <span className="specimen__name">{p.name[lang]}</span>
              <span className="specimen__sizes" aria-hidden="true">
                <Plate size={102} plateId={p.id} decorative />
                <Plate size={64} plateId={p.id} decorative />
              </span>
            </figcaption>
          </figure>
        ))}
      </div>
    </main>
  );
}
