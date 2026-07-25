"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { API_URL } from "../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail ?? "No se pudo iniciar sesión.");
      }

      router.push("/");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No se pudo iniciar sesión."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 0%, color-mix(in srgb, var(--brand) 15%, transparent), transparent 70%)",
        }}
      />

      <div className="w-full max-w-md rounded-2xl border border-border bg-surface p-8 shadow-2xl shadow-black/40">
        <Link href="/" className="flex items-center justify-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-brand text-black">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2.5}
              className="h-4.5 w-4.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.5 6.5v11M17.5 6.5v11M2 9v6M22 9v6M6.5 12h11"
              />
            </svg>
          </span>
          <span className="font-display text-lg font-semibold tracking-tight text-foreground">
            SMART<span className="text-brand">-GYM</span>
          </span>
        </Link>

        <h1 className="font-display mt-6 text-center text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Iniciar sesión
        </h1>
        <p className="mt-1.5 text-center text-sm text-muted">
          Bienvenido de nuevo a Smart-Gym.
        </p>

        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          {error && (
            <p className="rounded-lg border border-danger/40 bg-danger/10 px-3.5 py-2.5 text-sm text-danger">
              {error}
            </p>
          )}

          <div>
            <label
              htmlFor="email"
              className="mb-1.5 block text-sm font-medium text-muted"
            >
              Correo electrónico
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="tu@ejemplo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-border bg-surface-2 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1.5 block text-sm font-medium text-muted"
            >
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded-lg border border-border bg-surface-2 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          ¿No tienes cuenta?{" "}
          <Link href="/registro" className="font-medium text-brand hover:underline">
            Regístrate
          </Link>
        </p>
      </div>
    </div>
  );
}
