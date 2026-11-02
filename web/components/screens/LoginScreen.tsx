"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import useSWR, { useSWRConfig } from "swr";

import { Button } from "@/components/core/Button";
import { TextField } from "@/components/forms/TextField";
import { SegmentedControl } from "@/components/forms/SegmentedControl";
import { api, ApiError } from "@/lib/api";
import { usePrefs } from "@/lib/prefs";
import type { Household } from "@/lib/types";

export function LoginScreen() {
  const { t, lang } = usePrefs();
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const { data: household } = useSWR<Household>("/api/auth/household");
  const [member, setMember] = useState("");
  const [passcode, setPasscode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (household && !member) setMember(household.members[0]?.name ?? "");
  }, [household, member]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post("/api/auth/login", { member, passcode });
      await mutate(() => true, undefined, { revalidate: true });
      router.replace("/");
    } catch (err) {
      // 401: wrong passcode. Any other HTTP error: the server answered but failed. No response: offline.
      setError(err instanceof ApiError ? (err.status === 401 ? t.wrongPasscode : t.genericError) : t.offline);
      setBusy(false);
    }
  };

  return (
    <main className="login">
      <h1 className="wordmark">Mela</h1>
      <p className="subtitle" style={{ marginBottom: 32 }}>
        {household ? (lang === "zh" ? household.name_zh : household.name) : " "}
      </p>
      <form className="add__stack" onSubmit={submit}>
        {household && household.members.length > 0 && (
          <div>
            <span className="field__label">{t.whoIsCooking}</span>
            <SegmentedControl
              label={t.whoIsCooking}
              value={member}
              onChange={setMember}
              options={household.members.map((m) => ({ value: m.name, label: lang === "zh" ? m.name_zh : m.name }))}
            />
          </div>
        )}
        <TextField
          id="passcode"
          label={t.passcode}
          type="password"
          autoComplete="current-password"
          value={passcode}
          onChange={(e) => setPasscode(e.target.value)}
        />
        {error && <p className="error-text">{error}</p>}
        <Button variant="primary" block type="submit" disabled={!member || !passcode || busy}>
          {t.signIn}
        </Button>
      </form>
    </main>
  );
}
