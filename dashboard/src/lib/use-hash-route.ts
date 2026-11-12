import { useSyncExternalStore } from "react";

function subscribe(onChange: () => void): () => void {
  window.addEventListener("hashchange", onChange);
  return () => {
    window.removeEventListener("hashchange", onChange);
  };
}

function current(): string {
  return window.location.hash.slice(1) || "/";
}

/** The page named in the URL's hash, such as "/claims/CLM-1001". */
export function useHashRoute(): string {
  return useSyncExternalStore(subscribe, current);
}
