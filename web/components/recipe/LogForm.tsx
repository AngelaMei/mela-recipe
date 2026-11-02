"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/core/Button";
import { TextArea, TextField } from "@/components/forms/TextField";
import { Sheet } from "@/components/overlays/Sheet";
import { api } from "@/lib/api";
import type { PhotoCrop } from "@/lib/crop";
import { resizeImage } from "@/lib/image";
import { usePrefs } from "@/lib/prefs";
import type { CookLog } from "@/lib/types";

import { PhotoAdjuster } from "./PhotoAdjuster";

function today(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export interface LogFormProps {
  open: boolean;
  recipeId: string;
  /** The recipe's plate, so the photo is framed on the plate it will appear on. */
  plateId: string | null;
  log: CookLog | null; // null = new cook
  onClose: () => void;
  onSaved: () => void;
}

/** Log form: date, rating, note, photo, tweaks. Also edits/deletes an existing log. */
export function LogForm({ open, recipeId, plateId, log, onClose, onSaved }: LogFormProps) {
  const { t } = usePrefs();
  const [date, setDate] = useState(today());
  const [rating, setRating] = useState<number | null>(null);
  const [note, setNote] = useState("");
  const [tweaks, setTweaks] = useState("");
  const [photoId, setPhotoId] = useState<string | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [crop, setCrop] = useState<PhotoCrop | null>(null);
  const onCrop = useCallback((c: PhotoCrop) => setCrop(c), []);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setDate(log?.cooked_on ?? today());
    setRating(log?.rating ?? null);
    setNote(log?.note ?? "");
    setTweaks(log?.tweaks ?? "");
    setPhotoId(log?.photo_id ?? null);
    setPhotoUrl(log?.photo_url ?? null);
    setCrop(log?.photo_crop ?? null);
    setError(null);
  }, [open, log]);

  const upload = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const blob = await resizeImage(file);
      const form = new FormData();
      form.append("file", blob, "photo.jpg");
      const res = await api.upload<{ id: string; url: string }>("/api/photos", form);
      setPhotoId(res.id);
      setPhotoUrl(res.url);
      setCrop(null); // the adjuster starts it centred
    } catch {
      setError(t.genericError);
    } finally {
      setUploading(false);
    }
  };

  const save = async () => {
    setSaving(true);
    setError(null);
    const body = { cooked_on: date || today(), rating, note, tweaks, photo_id: photoId, photo_crop: photoId ? crop : null };
    try {
      if (log) await api.patch(`/api/logs/${log.id}`, { ...body, clear_photo: !photoId });
      else await api.post(`/api/recipes/${recipeId}/logs`, body);
      onSaved();
    } catch {
      setError(t.genericError);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!log || !window.confirm(t.confirmDeleteLog)) return;
    await api.del(`/api/logs/${log.id}`);
    onSaved();
  };

  return (
    <Sheet open={open} title={log ? t.editLogTitle : t.logTitle} onClose={onClose}>
      <div className="add__stack">
        <TextField id="log-date" label={t.date} type="date" value={date} max={today()} onChange={(e) => setDate(e.target.value)} />

        <div>
          <span className="field__label" id="rating-label">
            {t.rating}
          </span>
          <div className="rating-input" role="radiogroup" aria-labelledby="rating-label">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                role="radio"
                aria-checked={rating === n}
                aria-label={t.ratingOf(n)}
                onClick={() => setRating(rating === n ? null : n)}
              >
                {rating !== null && n <= rating ? "★" : "☆"}
              </button>
            ))}
          </div>
        </div>

        <TextArea id="log-note" label={t.note} placeholder={t.notePlaceholder} rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
        <TextArea id="log-tweaks" label={t.tweaks} placeholder={t.tweaksPlaceholder} rows={2} value={tweaks} onChange={(e) => setTweaks(e.target.value)} />

        <div>
          <span className="field__label">{t.photo}</span>
          {photoUrl && <PhotoAdjuster photoUrl={photoUrl} plateId={plateId} crop={crop} onChange={onCrop} />}
          <div className="photo-input">
            <Button size="sm" icon="photo_camera" disabled={uploading} onClick={() => fileRef.current?.click()}>
              {uploading ? t.uploading : photoUrl ? t.changePhoto : t.addPhoto}
            </Button>
            {photoUrl && (
              <Button size="sm" variant="ghost" onClick={() => { setPhotoId(null); setPhotoUrl(null); setCrop(null); }}>
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
        </div>

        {error && <p className="error-text">{error}</p>}
        <Button variant="primary" block onClick={save} disabled={saving || uploading}>
          {t.saveLog}
        </Button>
        {log && (
          <button type="button" className="danger-link" style={{ marginTop: 4 }} onClick={remove}>
            {t.deleteLog}
          </button>
        )}
      </div>
    </Sheet>
  );
}
