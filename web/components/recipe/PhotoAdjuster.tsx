"use client";

import { useEffect, useRef } from "react";

import { Button } from "@/components/core/Button";
import { centredCrop, clampCrop, imageSize, loadAspect, MAX_ZOOM, MIN_ZOOM, type PhotoCrop } from "@/lib/crop";
import { plateDef } from "@/lib/plates";
import { usePrefs } from "@/lib/prefs";

import { dishAreaFraction, Plate } from "./Plate";

const PREVIEW = 236; // px

/**
 * Position and size the dish photo on its plate.
 * Drag to move; pinch, scroll or use the slider to resize. The photo always
 * covers the whole dish shape (no empty edges).
 */
export function PhotoAdjuster({
  photoUrl,
  plateId,
  crop,
  onChange,
}: {
  photoUrl: string;
  plateId: string | null;
  crop: PhotoCrop | null;
  onChange: (crop: PhotoCrop) => void;
}) {
  const { t } = usePrefs();
  const pointers = useRef(new Map<number, { x: number; y: number }>());
  const gesture = useRef<{ crop: PhotoCrop; x: number; y: number; dist: number } | null>(null);
  const cropRef = useRef(crop);
  cropRef.current = crop;

  // Older photos have no framing yet: start centred, at the photo's real aspect ratio.
  useEffect(() => {
    if (crop) return;
    let live = true;
    loadAspect(photoUrl).then((aspect) => live && onChange(centredCrop(aspect)));
    return () => {
      live = false;
    };
  }, [photoUrl, crop, onChange]);

  // Pixels across the dish area in this preview
  const areaPx = PREVIEW * dishAreaFraction(plateId);

  const centroid = () => {
    const pts = [...pointers.current.values()];
    const x = pts.reduce((s, p) => s + p.x, 0) / pts.length;
    const y = pts.reduce((s, p) => s + p.y, 0) / pts.length;
    const dist = pts.length > 1 ? Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y) : 0;
    return { x, y, dist };
  };
  const startGesture = () => {
    if (!cropRef.current) return;
    gesture.current = { crop: cropRef.current, ...centroid() };
  };

  const onPointerDown = (e: React.PointerEvent) => {
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    startGesture();
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (!pointers.current.has(e.pointerId) || !gesture.current) return;
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const g = gesture.current;
    const now = centroid();
    const zoom = g.dist && now.dist ? g.crop.zoom * (now.dist / g.dist) : g.crop.zoom;
    const { w, h } = imageSize(areaPx, { zoom, aspect: g.crop.aspect });
    // Dragging right moves the photo right, so the centre point moves left.
    onChange(clampCrop({ ...g.crop, zoom, cx: g.crop.cx - (now.x - g.x) / w, cy: g.crop.cy - (now.y - g.y) / h }));
  };
  const onPointerEnd = (e: React.PointerEvent) => {
    pointers.current.delete(e.pointerId);
    gesture.current = null;
    if (pointers.current.size) startGesture();
  };

  // Scroll to zoom on a computer
  const area = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = area.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      const c = cropRef.current;
      if (!c) return;
      e.preventDefault();
      onChange(clampCrop({ ...c, zoom: c.zoom * Math.exp(-e.deltaY * 0.002) }));
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [onChange]);

  return (
    <div className="photo-adjuster">
      <div
        ref={area}
        className={`photo-adjuster__stage cloth cloth--${plateDef(plateId).cloth}`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerEnd}
        onPointerCancel={onPointerEnd}
        role="group"
        aria-label={t.adjustPhoto}
      >
        <Plate size={PREVIEW} plateId={plateId} photoUrl={photoUrl} photoCrop={crop} decorative />
      </div>
      <p className="field__helper photo-adjuster__hint">{t.adjustHint}</p>
      <div className="photo-adjuster__controls">
        <label className="photo-adjuster__zoom">
          <span>{t.photoSize}</span>
          <input
            type="range"
            min={MIN_ZOOM}
            max={MAX_ZOOM}
            step={0.01}
            value={crop?.zoom ?? 1}
            disabled={!crop}
            onChange={(e) => crop && onChange(clampCrop({ ...crop, zoom: Number(e.target.value) }))}
          />
        </label>
        <Button size="sm" variant="ghost" disabled={!crop} onClick={() => crop && onChange(centredCrop(crop.aspect))}>
          {t.resetPhoto}
        </Button>
      </div>
    </div>
  );
}
