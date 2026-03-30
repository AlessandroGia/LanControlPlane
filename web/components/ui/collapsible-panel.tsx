"use client";

import { useState } from "react";

type CollapsiblePanelProps = {
    title: string;
    count?: number;
    defaultOpen?: boolean;
    children: React.ReactNode;
};

export function CollapsiblePanel({
    title,
    count,
    defaultOpen = false,
    children,
}: CollapsiblePanelProps) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <section className="panel">
            <button
                type="button"
                className="collapsible-panel-header"
                onClick={() => setIsOpen((current) => !current)}
                aria-expanded={isOpen}
            >
                <div className="collapsible-panel-title-wrap">
                    <span className="collapsible-panel-chevron">{isOpen ? "▾" : "▸"}</span>
                    <h2 className="collapsible-panel-title">
                        {title}
                        {typeof count === "number" ? (
                            <span className="collapsible-panel-count">({count})</span>
                        ) : null}
                    </h2>
                </div>
            </button>

            {isOpen ? <div className="collapsible-panel-content">{children}</div> : null}
        </section>
    );
}
