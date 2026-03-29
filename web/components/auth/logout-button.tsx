"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LogoutButton() {
    const router = useRouter();
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleLogout() {
        setIsSubmitting(true);
        try {
            await fetch("/auth/logout", {
                method: "POST",
                credentials: "include",
            });
            router.push("/login");
            router.refresh();
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <button onClick={handleLogout} disabled={isSubmitting}>
            {isSubmitting ? "Signing out..." : "Logout"}
        </button>
    );
}
