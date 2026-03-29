import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
    return (
        <main className="auth-page">
            <div className="auth-shell">
                <div className="auth-brand">
                    <div className="auth-kicker">LAN Management</div>
                    <h1 className="auth-title">LAN Control Plane</h1>
                    <p className="auth-description">
                        Sign in to access your host dashboard, jobs, and audit activity.
                    </p>
                </div>

                <LoginForm />
            </div>
        </main>
    );
}
