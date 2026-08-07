"use client";
/**
 * The staleness badge, computed at VIEW time. Rendered server-side it was evaluated once at static
 * export and could structurally never fire — a "freshness" indicator frozen at its freshest moment,
 * which is the exact bug staleness exists to prevent. Server renders the plain date; this upgrades
 * it in the browser, so no-JS readers still see when the figure was measured.
 */
import { useEffect, useState } from "react";
import { freshness } from "@onrecord/engine/staleness";

export function Freshness({ asOf, staleAfterDays }: { asOf: string; staleAfterDays: number }) {
  const [note, setNote] = useState<string | null>(null);
  useEffect(() => {
    const f = freshness(asOf, staleAfterDays, Date.now());
    if (f.state !== "fresh") setNote(f.note);
  }, [asOf, staleAfterDays]);
  if (!note) return <>measured {asOf}</>;
  return <span style={{ color: "var(--c-warn)" }}>{note}</span>;
}
