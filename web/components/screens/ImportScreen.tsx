"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { useSWRConfig } from "swr";

import { Button } from "@/components/core/Button";
import { Checkbox } from "@/components/forms/Checkbox";
import { TopBar } from "@/components/navigation/TopBar";
import { api, ApiError } from "@/lib/api";
import { usePrefs } from "@/lib/prefs";

interface PreviewRecipe {
  name: string;
  name_alt: string | null;
  ingredients: number;
  steps: number;
  logs: number;
  photos: number;
  has_link: boolean;
  duplicate: boolean;
  warnings: string[];
}

interface ImportResponse {
  kind: "markdown" | "backup" | "json";
  dry_run: boolean;
  recipes: PreviewRecipe[];
  warnings: string[];
  counts: { found: number; new: number; duplicates: number };
  imported: number;
  total_recipes: number;
}

/** Settings › Backup › Import recipes. Choose a file, see the preview, then import. */
export function ImportScreen() {
  const { t } = usePrefs();
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportResponse | null>(null);
  const [includeDuplicates, setIncludeDuplicates] = useState(false);
  const [busy, setBusy] = useState<"reading" | "importing" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<number | null>(null);

  const send = (f: File, dryRun: boolean) => {
    const form = new FormData();
    form.append("file", f, f.name);
    form.append("dry_run", String(dryRun));
    form.append("skip_duplicates", String(!includeDuplicates));
    return api.upload<ImportResponse>("/api/import", form);
  };

  const choose = async (f: File) => {
    setFile(f);
    setPreview(null);
    setDone(null);
    setError(null);
    setBusy("reading");
    try {
      setPreview(await send(f, true));
    } catch (err) {
      // 422 explains what's wrong with the file
      setError(err instanceof ApiError && err.status === 422 ? err.message : t.importRecipesFailed);
    } finally {
      setBusy(null);
    }
  };

  const toImport = preview ? (includeDuplicates ? preview.counts.found : preview.counts.new) : 0;

  const doImport = async () => {
    if (!file) return;
    setBusy("importing");
    setError(null);
    try {
      const res = await send(file, false);
      setDone(res.imported);
      await mutate((k) => typeof k === "string" && (k.startsWith("/api/recipes") || k.startsWith("/api/search")));
    } catch (err) {
      setError(err instanceof ApiError && err.status === 422 ? err.message : t.importRecipesFailed);
    } finally {
      setBusy(null);
    }
  };

  return (
    <main>
      <TopBar title={t.importRecipes} backHref="/settings" />
      <div className="add add__stack import" style={{ paddingTop: 16, paddingBottom: 140 }}>
        <p className="muted import__intro">{t.importIntro}</p>

        <details className="group import__format">
          <summary>{t.importFormatTitle}</summary>
          <ul>
            {t.importFormatBody.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <pre className="import__sample" lang="zh-Hant">{`## 三杯雞
Link: https://youtu.be/…

### 食材
- 雞腿 — 600g
- 九層塔 — 一把

### 步驟
1. 雞腿切塊
2. 麻油煸香薑片

### 紀錄
- 2026-10-24 ★★★★★ (Mei): 收汁剛好`}</pre>
          <a className="link" href="/mela-import-example.md" download>
            {t.downloadExample}
          </a>
        </details>

        <div>
          <Button icon="upload_file" block onClick={() => fileRef.current?.click()} disabled={!!busy}>
            {busy === "reading" ? t.reading : file ? t.chooseAnother : t.chooseFile}
          </Button>
          <input
            ref={fileRef}
            type="file"
            accept=".md,.markdown,.txt,.json,.zip,text/plain,text/markdown,application/json,application/zip"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) choose(f);
              e.target.value = "";
            }}
          />
          {file && <p className="field__helper">{file.name}</p>}
        </div>

        {error && <p className="error-text">{error}</p>}

        {done !== null && (
          <div className="notice import__done" aria-live="polite">
            <span className="icon" aria-hidden="true" style={{ color: "var(--success)" }}>
              check_circle
            </span>
            <div>
              <strong style={{ color: "var(--text-primary)" }}>{t.importedN(done)}</strong>
              <div className="notice__actions">
                <Button size="sm" variant="secondary" onClick={() => router.push("/recipes")}>
                  {t.seeRecipes}
                </Button>
              </div>
            </div>
          </div>
        )}

        {preview && done === null && (
          <section aria-live="polite">
            <h2 className="overline" style={{ marginBottom: 10 }}>
              {t.foundSummary(preview.counts.found, preview.counts.new, preview.counts.duplicates)}
            </h2>
            {preview.warnings.map((w) => (
              <p key={w} className="field__helper">
                {w}
              </p>
            ))}
            <ul className="list">
              {preview.recipes.map((r, i) => (
                <li key={i} className={`row import__row${r.duplicate && !includeDuplicates ? " import__row--skip" : ""}`}>
                  <span className="row__main">
                    <span className="row__title" style={{ display: "block" }}>
                      {r.name}
                      {r.name_alt && <span className="muted"> · {r.name_alt}</span>}
                    </span>
                    <span className="row__sub" style={{ display: "block" }}>
                      {t.recipeCounts(r.ingredients, r.steps, r.logs, r.photos)}
                      {r.has_link && ` · ${t.linkOnlyShort}`}
                    </span>
                    {r.warnings.map((w) => (
                      <span key={w} className="row__sub import__warning" style={{ display: "block" }}>
                        {w}
                      </span>
                    ))}
                  </span>
                  {r.duplicate && <span className="import__badge">{t.alreadyInMela}</span>}
                </li>
              ))}
            </ul>
            {preview.counts.duplicates > 0 && (
              <button
                type="button"
                role="checkbox"
                aria-checked={includeDuplicates}
                className="row"
                style={{ borderBottom: 0 }}
                onClick={() => setIncludeDuplicates((v) => !v)}
              >
                <Checkbox checked={includeDuplicates} />
                <span className="row__main">{t.importDuplicates}</span>
              </button>
            )}
          </section>
        )}
      </div>

      {preview && done === null && (
        <div className="sticky-cta">
          <Button variant="primary" block onClick={doImport} disabled={!!busy || toImport === 0}>
            {busy === "importing" ? t.importingRecipes : t.importN(toImport)}
          </Button>
        </div>
      )}
      {done !== null && (
        <div className="sticky-cta">
          <Link href="/recipes" className="btn btn--primary btn--block">
            {t.seeRecipes}
          </Link>
        </div>
      )}
    </main>
  );
}
