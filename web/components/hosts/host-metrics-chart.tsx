"use client";

import type { HostMetricRead } from "@/lib/types";
import {
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

type HostMetricsChartProps = {
    metrics: HostMetricRead[];
};

type ChartPoint = {
    collectedAt: string;
    cpuUsage: number;
    memoryUsage: number;
};

function buildChartData(metrics: HostMetricRead[]): ChartPoint[] {
    return [...metrics]
        .sort(
            (a, b) =>
                new Date(a.collected_at).getTime() - new Date(b.collected_at).getTime(),
        )
        .map((metric) => ({
            collectedAt: new Date(metric.collected_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
            }),
            cpuUsage: Number(metric.cpu_usage.toFixed(1)),
            memoryUsage: Number(metric.memory_usage.toFixed(1)),
        }));
}

export function HostMetricsChart({ metrics }: HostMetricsChartProps) {
    const data = buildChartData(metrics);

    if (data.length === 0) {
        return <div className="list-item-meta">No metrics available for chart.</div>;
    }

    return (
        <div style={{ width: "100%", height: 320 }}>
            <ResponsiveContainer>
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="collectedAt" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Legend />
                    <Line
                        type="monotone"
                        dataKey="cpuUsage"
                        name="CPU %"
                        stroke="#4aa3ff"
                        strokeWidth={2}
                        dot={false}
                    />
                    <Line
                        type="monotone"
                        dataKey="memoryUsage"
                        name="RAM %"
                        stroke="#2ecc71"
                        strokeWidth={2}
                        dot={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
