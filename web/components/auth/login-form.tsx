"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export function LoginForm() {
    const router = useRouter();

    const [username, setUsername] = useState("admin");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setError(null);
        setIsSubmitting(true);

        try {
            const response = await fetch("/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ username, password }),
                credentials: "include",
            });

            if (!response.ok) {
                const payload = (await response.json().catch(() => null)) as
                    | { detail?: string }
                    | null;

                setError(payload?.detail ?? "Login failed");
                return;
            }

            router.push("/");
            router.refresh();
        } catch {
            setError("Network error");
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <form onSubmit={handleSubmit} className="auth-card">
            <div className="auth-card-header">
                <h2 className="auth-card-title">Welcome back</h2>
                <p className="auth-card-subtitle">
                    Use your administrator credentials to continue.
                </p>
            </div>

            <div className="auth-fields">
                <label className="auth-label">
                    <span>Username</span>
                    <input
                        className="auth-input"
                        value={username}
                        onChange={(event) => setUsername(event.target.value)}
                        autoComplete="username"
                        placeholder="Enter your username"
                    />
                </label>

                <label className="auth-label">
                    <span>Password</span>
                    <input
                        className="auth-input"
                        type="password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        autoComplete="current-password"
                        placeholder="Enter your password"
                    />
                </label>

                {error ? <div className="auth-error">{error}</div> : null}

                <button className="auth-submit" type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Signing in..." : "Sign in"}
                </button>
            </div>
        </form>
    );
}
