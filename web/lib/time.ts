export function parsePossiblyUtc(value: string): Date {
    if (value.endsWith("Z") || value.includes("+")) {
        return new Date(value);
    }

    return new Date(`${value}Z`);
}

export function formatRelativeTime(value: string): string {
    const now = Date.now();
    const then = parsePossiblyUtc(value).getTime();
    const diffSeconds = Math.max(0, Math.floor((now - then) / 1000));

    if (diffSeconds < 60) {
        return `${diffSeconds}s ago`;
    }

    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) {
        return `${diffMinutes}m ago`;
    }

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) {
        return `${diffHours}h ago`;
    }

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
}

export function isOlderThan(value: string, seconds: number): boolean {
    const now = Date.now();
    const then = parsePossiblyUtc(value).getTime();
    const diffSeconds = Math.max(0, Math.floor((now - then) / 1000));

    return diffSeconds > seconds;
}

export function formatLocalDateTime(value: string): string {
    return parsePossiblyUtc(value).toLocaleString();
}
