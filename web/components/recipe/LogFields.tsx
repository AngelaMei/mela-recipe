"use client";

import { useCallback, useRef, useState } from "react";

import { Button } from "@/components/core/Button";
import { TextArea, TextField } from "@/components/forms/TextField";
import { api } from "@/lib/api";
import type { PhotoCrop } from "@/lib/crop";
import { resizeImage } from "@/lib/image";
import { usePrefs } from "@/lib/prefs";
import type { CookLog } from "@/lib/types";

import { PhotoAdjuster } from "./PhotoAdjuster";

/** One cook, as edited in a form. */
export interface LogDraft {
  cooked_on: string; // YYYY-MM-DD
  rating: number | null;
  note: string;
  tweaks: string;
  photo_id: string | null;
  photo_url: string | null;
  photo_crop: PhotoCrop | null;
}

export function today(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function emptyLog(): LogDraft {
  return { cooked_on: today(), rating: null, note: "", tweaks: "", photo_id: null, photo_url: null, photo_crop: null };
}

export function logDraft(log: CookLog): LogDraft {
  return {
    cooked_on: log.cooked_on,
    rating: log.rating,
    note: log.note ?? "",
    tweaks: log.tweaks ?? "",
    photo_id: log.photo_id,
    photo_url: log.photo_url,
    photo_crop: log.photo_crop,
  };
}

/** The request body for POST /api/recipes/{id}/logs or PATCH /api/logs/{id}. */
export function logBody(d: LogDraft) {
  return {
    cooked_on: d.cooked_on || today(),
    rating: d.rating,
    note: d.note,
    tweaks: d.tweaks,
    photo_id: d.photo_id,
    photo_crop: d.photo_id ? d.photo_crop : null,
  };
}

/** Date, rating, note, tweaks and a photo framed on the plate. */
export function LogFields({
  idPrefix,
  value,
  onChange,
  plateId,
  onUploading,
}: {
  idPrefix: string;
  value: LogDraft;
  onChange: (patch: Partial<LogDraft>) => void;
  /** The plate the photo will sit on, for framing. */
  plateId: string | null;
  onUploading?: (busy: boolean) => void;
}) {
  const { t } = usePrefs();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const onCrop = useCallback((c: PhotoCrop) => onChange({ photo_crop: c }), [onChange]);

  const upload = async (file: File) => {
    setUploading(true);
    onUploading?.(true);
    setError(null);
    try {
      const blob = await resizeImage(file);
      const form = new FormData();
      form.append("file", blob, "photo.jpg");
      const res = await api.upload<{ id: string; url: string }>("/api/photos", form);
      onChange({ photo_id: res.id, photo_url: res.url, photo_crop: null }); // the adjuster starts it centred
    } catch {
      setError(t.genericError);
    } finally {
      setUploading(false);
      onUploading?.(false);
    }
  };

  return (
    <>
      <TextField
        id={`${idPrefix}-date`}
        label={t.date}
        type="date"
        value={value.cooked_on}
        max={today()}
        onChange={(e) => onChange({ cooked_on: e.target.value })}
      />

      <div>
        <span className="field__label" id={`${idPrefix}-rating`}>
          {t.rating}
        </span>
        <div className="rating-input" role="radiogroup" aria-labelledby={`${idPrefix}-rating`}>
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              role="radio"
              aria-checked={value.rating === n}
              aria-label={t.ratingOf(n)}
              onClick={() => onChange({ rating: value.rating === n ? null : n })}
            >
              {value.rating !== null && n <= value.rating ? "★" : "☆"}
            </button>
          ))}
        </div>
      </div>

      <TextArea
        id={`${idPrefix}-note`}
        label={t.note}
        placeholder={t.notePlaceholder}
        rows={2}
        value={value.note}
        onChange={(e) => onChange({ note: e.target.value })}
      />
      <TextArea
        id={`${idPrefix}-tweaks`}
        label={t.tweaks}
        placeholder={t.tweaksPlaceholder}
        rows={2}
        value={value.tweaks}
        onChange={(e) => onChange({ tweaks: e.target.value })}
      />

      <div>
        <span className="field__label">{t.photo}</span>
        {value.photo_url && (
          <PhotoAdjuster photoUrl={value.photo_url} plateId={plateId} crop={value.photo_crop} onChange={onCrop} />
        )}
        <div className="photo-input">
          <Button size="sm" icon="photo_camera" disabled={uploading} onClick={() => fileRef.current?.click()}>
            {uploading ? t.uploading : value.photo_url ? t.changePhoto : t.addPhoto}
          </Button>
          {value.photo_url && (
            <Button size="sm" variant="ghost" onClick={() => onChange({ photo_id: null, photo_url: null, photo_crop: null })}>
              {t.removePhoto}
            </Button>
          )}
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) upload(f);
              e.target.value = "";
            }}
          />
        </div>
        {error && <p className="error-text">{error}</p>}
      </div>
    </>
  );
}
