"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

type HostDetailAutoRefreshProps = {
    intervalMs?: number;
};

export function HostDetailAutoRefresh({
    intervalMs = 10000,
}: HostDetailAutoRefreshProps) {
    const router = useRouter();

    useEffect(() => {
        const intervalId = window.setInterval(() => {
            router.refresh();
        }, intervalMs);

        return () => {
            window.clearInterval(intervalId);
        };
    }, [router, intervalMs]);

    return null;
}
