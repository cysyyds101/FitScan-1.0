// useAdaptivePoll — schedule a callback at an interval that changes
// based on a state-derived delay.
//
// Why this exists (per user feedback):
//   - Fixed-interval polling (e.g. always 2s) wastes backend + GPU cycles
//     when the worker is mid-inference
//   - The backend already knows how urgent a poll is; it sends a
//     `next_poll_ms` hint in each response
//   - We read that hint, sleep for that long, then re-poll
//
// Usage:
//   useAdaptivePoll({
//     shouldRun: latest?.status && !TERMINAL.has(latest.status),
//     getDelayMs: () => latest?.next_poll_ms ?? 2000,
//     fire: reload,
//   });
//
// The hook manages a single setTimeout chain: each fire schedules the
// next fire with the delay returned by getDelayMs() AT THE TIME OF FIRE.
// This means delays are re-evaluated on every response (truly adaptive).
import { useEffect, useRef } from "react";

export function useAdaptivePoll({ shouldRun, getDelayMs, fire }) {
  const timerRef = useRef(null);
  const stoppedRef = useRef(false);

  // Keep latest fire/getDelayMs in refs so the timer chain always sees
  // the freshest closure without re-binding.
  const fireRef = useRef(fire);
  const getDelayRef = useRef(getDelayMs);
  fireRef.current = fire;
  getDelayRef.current = getDelayMs;

  useEffect(() => {
    stoppedRef.current = false;

    const tick = async () => {
      if (stoppedRef.current) return;
      try {
        await fireRef.current();
      } catch (e) {
        // Swallow errors so the loop continues
        // eslint-disable-next-line no-console
        console.warn("[useAdaptivePoll] fire failed:", e);
      }
      if (stoppedRef.current) return;
      const next = getDelayRef.current();
      if (next > 0) {
        timerRef.current = setTimeout(tick, next);
      }
    };

    if (shouldRun) {
      // First tick immediately so we don't wait delayMs before the first read
      tick();
    }

    return () => {
      stoppedRef.current = true;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [shouldRun]);
}
