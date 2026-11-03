"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/core/Button";
import { Sheet } from "@/components/overlays/Sheet";
import { api } from "@/lib/api";
import { usePrefs } from "@/lib/prefs";
import type { CookLog } from "@/lib/types";

import { emptyLog, logBody, logDraft, LogFields, type LogDraft } from "./LogFields";

export interface LogFormProps {
  open: boolean;
  recipeId: string;
  /** The recipe's plate, so the photo is framed on the plate it will appear on. */
  plateId: string | null;
  log: CookLog | null; // null = new cook
  /** Sheet title; defaults to "Log a cook" / "Edit cook". */
  title?: string;
  onClose: () => void;
  onSaved: () => void;
}

/** Log sheet: date, rating, note, tweaks, photo. Also edits / deletes an existing log. */
export function LogForm({ open, recipeId, plateId, log, title, onClose, onSaved }: LogFormProps) {
  const { t } = usePrefs();
  const [draft, setDraft] = useState<LogDraft>(emptyLog());
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const update = useCallback((patch: Partial<LogDraft>) => setDraft((d) => ({ ...d, ...patch })), []);

  useEffect(() => {
    if (!open) return;
    setDraft(log ? logDraft(log) : emptyLog());
    setError(null);
  }, [open, log]);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      if (log) await api.patch(`/api/logs/${log.id}`, { ...logBody(draft), clear_photo: !draft.photo_id });
      else await api.post(`/api/recipes/${recipeId}/logs`, logBody(draft));
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
    <Sheet open={open} title={title ?? (log ? t.editLogTitle : t.logTitle)} onClose={onClose}>
      <div className="add__stack">
        <LogFields idPrefix="log" value={draft} onChange={update} plateId={plateId} onUploading={setUploading} />
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
