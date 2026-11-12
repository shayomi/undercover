import { useEffect, useState } from "react";

export interface Refresh<T> {
  everyMs: number;
  while: (data: T) => boolean;
}

export interface Resource<T> {
  data: T | null;
  error: string | null;
  reload: () => void;
}

/** Load data, refresh it while `refresh.while` holds, and reload on demand. */
export function useResource<T>(
  load: () => Promise<T>,
  refresh?: Refresh<T>,
): Resource<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let live = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const fetchData = () => {
      load().then(
        (result) => {
          if (!live) return;
          setData(result);
          setError(null);
          if (refresh?.while(result)) {
            timer = setTimeout(fetchData, refresh.everyMs);
          }
        },
        (reason: unknown) => {
          if (live) setError(String(reason));
        },
      );
    };
    fetchData();
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [load, refresh, version]);

  return {
    data,
    error,
    reload: () => {
      setVersion((v) => v + 1);
    },
  };
}
