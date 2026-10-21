// useClothing — fetch /api/clothing and expose as a hook.
// Refreshes on demand (no polling) since the clothing list rarely changes.

import { useCallback, useEffect, useState } from "react";
import { clothingApi } from "../api/client";

export function useClothing() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await clothingApi.list();
      setItems(data?.items ?? []);
    } catch (e) {
      setError(e);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return { items, loading, error, reload };
}
