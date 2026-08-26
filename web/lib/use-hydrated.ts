"use client";

import { useSyncExternalStore } from "react";

const subscribe = (): (() => void) => () => undefined;

export function useHydrated(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
}
