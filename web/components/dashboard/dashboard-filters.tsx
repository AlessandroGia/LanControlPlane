"use client";

type HostFilterValue = "all" | "online" | "offline" | "waking" | "stale";

type DashboardFiltersProps = {
    search: string;
    statusFilter: HostFilterValue;
    onSearchChange: (value: string) => void;
    onStatusFilterChange: (value: HostFilterValue) => void;
};

export function DashboardFilters({
    search,
    statusFilter,
    onSearchChange,
    onStatusFilterChange,
}: DashboardFiltersProps) {
    return (
        <section className="dashboard-filters">
            <input
                className="dashboard-search"
                type="text"
                placeholder="Search hosts..."
                value={search}
                onChange={(event) => onSearchChange(event.target.value)}
            />

            <select
                className="dashboard-filter-select"
                value={statusFilter}
                onChange={(event) =>
                    onStatusFilterChange(event.target.value as HostFilterValue)
                }
            >
                <option value="all">All hosts</option>
                <option value="online">Online</option>
                <option value="offline">Offline</option>
                <option value="waking">Waking</option>
                <option value="stale">Stale</option>
            </select>
        </section>
    );
}

export type { HostFilterValue };
