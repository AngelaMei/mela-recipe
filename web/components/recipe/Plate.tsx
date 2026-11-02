"use client";

import { useEffect, useId, useState } from "react";

import { loadPlateManifest, plateDef, type PlateDef } from "@/lib/plates";

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
 * A top-down ceramic plate, lit from the top-left.
 * Layers: rim (shape + glaze + decoration) → well (recessed centre) → dish
 * photo (circle crop) → light. The drop shadow is CSS (filter), so it follows
 * the plate's outline.
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

  const def = plateDef(plateId);
  return (
    <span className={`plate${selected ? " plate--selected" : ""}`} style={sizeStyle} {...a11y}>
      {def.image ? (
        <>
          <img className="plate__rim-img" src={def.image} alt="" />
          {photoUrl && (
            <span className="plate__food" style={{ inset: `${def.foodInset ?? 22}%` }}>
              <img src={photoUrl} alt="" loading="lazy" />
            </span>
          )}
        </>
      ) : (
        <PlateSvg def={def} photoUrl={photoUrl} detail={size >= 90} />
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Drawing (viewBox 0 0 200 200, centre 100,100, plate radius 96)
// ---------------------------------------------------------------------------
const C = 100;
const R = 96;

function outline(def: PlateDef, radius: number): string {
  const n = def.lobes ?? 16;
  const pts: string[] = [];
  const steps = 360;
  for (let i = 0; i < steps; i++) {
    const a = (i / steps) * Math.PI * 2;
    let r = radius;
    if (def.shape === "scallop") {
      // soft waves
      r = radius - 2.2 + 2.2 * Math.cos(n * a);
    } else if (def.shape === "petal") {
      // rounded lobes with notches between them
      r = radius - 7 * Math.pow(Math.abs(Math.sin((n * a) / 2)), 3);
    } else if (def.shape === "octagon") {
      // an octagon with softened corners and a fine scallop
      const seg = Math.PI / 4;
      const local = ((a + seg / 2) % seg) - seg / 2;
      const poly = (radius * Math.cos(seg / 2)) / Math.cos(local);
      r = 0.55 * poly + 0.45 * radius - 1.2 + 1.2 * Math.cos(n * a);
      r = Math.min(r, radius);
    }
    pts.push(`${(C + r * Math.cos(a)).toFixed(2)},${(C + r * Math.sin(a)).toFixed(2)}`);
  }
  return `M${pts.join("L")}Z`;
}

/** Deterministic pseudo-random numbers so speckles don't move between renders. */
function seeded(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function PlateSvg({ def, photoUrl, detail }: { def: PlateDef; photoUrl?: string | null; detail: boolean }) {
  const uid = useId().replace(/:/g, "");
  const id = (s: string) => `${uid}-${s}`;
  const path = outline(def, R);
  const wellR = R * def.wellR;
  const foodR = Math.min(wellR * 0.9, 58);

  return (
    <svg className="plate__svg" viewBox="0 0 200 200" aria-hidden="true">
      <defs>
        <clipPath id={id("shape")}>
          <path d={path} />
        </clipPath>
        <clipPath id={id("food")}>
          <circle cx={C} cy={C} r={foodR} />
        </clipPath>
        {/* light from the top-left */}
        <linearGradient id={id("light")} x1="0.15" y1="0.1" x2="0.85" y2="0.95">
          <stop offset="0" stopColor="#fff" stopOpacity="0.38" />
          <stop offset="0.45" stopColor="#fff" stopOpacity="0" />
          <stop offset="0.7" stopColor="#000" stopOpacity="0" />
          <stop offset="1" stopColor="#000" stopOpacity="0.12" />
        </linearGradient>
        {/* the well is recessed: shaded on the top-left, catching light on the bottom-right */}
        <radialGradient id={id("well")} cx="0.56" cy="0.58" r="0.62">
          <stop offset="0.7" stopColor={def.well} />
          <stop offset="1" stopColor={def.well} stopOpacity="0" />
        </radialGradient>
        <linearGradient id={id("wellEdge")} x1="0.2" y1="0.15" x2="0.8" y2="0.9">
          <stop offset="0" stopColor="#000" stopOpacity="0.16" />
          <stop offset="0.5" stopColor="#000" stopOpacity="0.03" />
          <stop offset="1" stopColor="#fff" stopOpacity="0.55" />
        </linearGradient>
        {def.centreGlaze && (
          <radialGradient id={id("glaze")} cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor={def.centreGlaze} />
            <stop offset="0.48" stopColor={def.centreGlaze} />
            <stop offset="0.62" stopColor={def.well} />
            <stop offset="0.7" stopColor={def.rim} stopOpacity="0.6" />
            <stop offset="0.76" stopColor={def.rim} stopOpacity="0" />
          </radialGradient>
        )}
      </defs>

      <g clipPath={`url(#${id("shape")})`}>
        {/* rim */}
        <rect width="200" height="200" fill={def.rim} />
        {def.centreGlaze && <circle cx={C} cy={C} r={R} fill={`url(#${id("glaze")})`} />}
        {def.decor === "speckle" && <Speckles seed={7} />}
        {def.decor === "flutes" && <Flutes from={wellR + 3} to={R} />}
        {def.decor === "band" && (
          <>
            <circle cx={C} cy={C} r={R * 0.87} fill="none" stroke={def.accent} strokeWidth="4.5" />
            <circle cx={C} cy={C} r={R * 0.8} fill="none" stroke={def.accent} strokeWidth="0.8" opacity="0.7" />
          </>
        )}
        {def.decor === "garland" && <Garland r={R * 0.83} color={def.accent ?? "#d9707f"} detail={detail} />}

        {/* well */}
        {!def.centreGlaze && <circle cx={C} cy={C} r={wellR} fill={`url(#${id("well")})`} />}
        <circle cx={C} cy={C} r={wellR} fill="none" stroke={`url(#${id("wellEdge")})`} strokeWidth={def.centreGlaze ? 0.8 : 2.2} />

        {/* dish photo */}
        {photoUrl && (
          <image
            href={photoUrl}
            x={C - foodR}
            y={C - foodR}
            width={foodR * 2}
            height={foodR * 2}
            preserveAspectRatio="xMidYMid slice"
            clipPath={`url(#${id("food")})`}
          />
        )}

        {/* light */}
        <rect width="200" height="200" fill={`url(#${id("light")})`} />
      </g>

      {/* edge */}
      <path d={path} fill="none" stroke={def.edge ?? "rgba(60,45,30,0.16)"} strokeWidth={def.edgeWidth ?? 0.8} />
      {!def.edge && <path d={outline(def, R - 1.2)} fill="none" stroke="#fff" strokeOpacity="0.55" strokeWidth="0.8" />}
    </svg>
  );
}

function Flutes({ from, to }: { from: number; to: number }) {
  const lines = [];
  const n = 64;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const cos = Math.cos(a);
    const sin = Math.sin(a);
    lines.push(
      <line
        key={i}
        x1={C + from * cos}
        y1={C + from * sin}
        x2={C + to * cos}
        y2={C + to * sin}
        stroke={i % 2 ? "#ffffff" : "#000000"}
        strokeOpacity={i % 2 ? 0.7 : 0.07}
        strokeWidth={i % 2 ? 1.6 : 2.4}
        strokeLinecap="round"
      />,
    );
  }
  return <g>{lines}</g>;
}

function Speckles({ seed }: { seed: number }) {
  const rand = seeded(seed);
  const dots = [];
  for (let i = 0; i < 140; i++) {
    const a = rand() * Math.PI * 2;
    const r = Math.sqrt(rand()) * R;
    dots.push(
      <circle
        key={i}
        cx={C + r * Math.cos(a)}
        cy={C + r * Math.sin(a)}
        r={0.4 + rand() * 0.9}
        fill={rand() > 0.3 ? "#3f4238" : "#d9dccf"}
        opacity={0.35 + rand() * 0.35}
      />,
    );
  }
  return <g>{dots}</g>;
}

/** A ring of small roses with leaves, and a fine pink line following the scalloped edge. */
function Garland({ r, color, detail }: { r: number; color: string; detail: boolean }) {
  const items = [];
  const n = 16;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const x = C + r * Math.cos(a);
    const y = C + r * Math.sin(a);
    const deg = (a * 180) / Math.PI;
    items.push(
      <g key={i}>
        <ellipse cx={x} cy={y} rx="3.6" ry="1.6" fill="#6c9658" transform={`rotate(${deg + 90 + 30} ${x} ${y}) translate(-3.6 0)`} />
        <ellipse cx={x} cy={y} rx="3.6" ry="1.6" fill="#6c9658" transform={`rotate(${deg + 90 - 30} ${x} ${y}) translate(3.6 0)`} />
        <circle cx={x} cy={y} r="2.9" fill={color} />
        {detail && <circle cx={x - 0.5} cy={y - 0.5} r="1.2" fill="#b4435a" />}
        {/* small buds between the roses */}
        {[0.33, 0.66].map((f) => (
          <circle
            key={f}
            cx={C + r * Math.cos(a + (f * 2 * Math.PI) / n)}
            cy={C + r * Math.sin(a + (f * 2 * Math.PI) / n)}
            r={detail ? 1.1 : 0.9}
            fill={color}
            opacity="0.8"
          />
        ))}
      </g>,
    );
  }
  return (
    <g>
      <circle cx={C} cy={C} r={r} fill="none" stroke="#6c9658" strokeOpacity="0.5" strokeWidth="0.6" />
      <circle cx={C} cy={C} r={R * 0.955} fill="none" stroke={color} strokeOpacity="0.55" strokeWidth="0.9" />
      {items}
    </g>
  );
}
