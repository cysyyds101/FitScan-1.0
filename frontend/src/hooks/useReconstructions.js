// useReconstructions — fetch reconstructions for a given upload_id and
// use adaptive polling (driven by backend's next_poll_ms hint) to track
// the latest one to a terminal state.

import { useCallback, useEffect, useState } from "react";
import { reconstructionsApi } from "../api/client";
import { useAdaptivePoll } from "./useAdaptivePoll";

const TERMINAL = new Set(["done", "failed"]);

export function useReconstructions(uploadId) {
  const [items, setItems] = useState([]);
  const [latest, setLatest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(async () => {
    if (!uploadId) {
      setItems([]);
      setLatest(null);
      setLoading(false);
      return;
    }
    try {
      const list = await reconstructionsApi.list({ uploadId, limit: 50 });
      setItems(list ?? []);
      const sorted = [...(list ?? [])].sort((a, b) =>
        String(b.created_at).localeCompare(String(a.created_at))
      );
      setLatest(sorted[0] ?? null);
      setError(null);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  // Initial load + reset on uploadId change
  useEffect(() => {
    setLoading(true);
    reload();
  }, [reload]);

  // Adaptive polling: re-evaluate delay from latest.next_poll_ms on every
  // response. Backend decides the cadence.
  useAdaptivePoll({
    shouldRun: Boolean(latest) && !TERMINAL.has(latest.status),
    getDelayMs: () => {
      if (!latest) return 0;
      // Honor server's hint, with a safety floor.
      const hint = Number(latest.next_poll_ms);
      if (Number.isFinite(hint) && hint > 0) return Math.max(hint, 250);
      return 2000;
    },
    fire: reload,
  });

  return { items, latest, loading, error, reload };
}
