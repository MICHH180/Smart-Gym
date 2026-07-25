"use client";

import Link from "next/link";
import { useUsuarioActual } from "../lib/useUsuarioActual";

export default function Hero() {
  const { usuario } = useUsuarioActual();
  const racha = usuario?.racha ?? 0;

  return (
    <section className="relative overflow-hidden border-b border-border">
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 0%, color-mix(in srgb, var(--brand) 18%, transparent), transparent 70%)",
        }}
      />

      <div className="mx-auto flex max-w-6xl flex-col items-center px-4 py-24 text-center sm:px-6 sm:py-32 lg:px-8">
        <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-1.5 text-xs font-medium text-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-brand" />
          Visión por computadora en tiempo real
        </span>

        <h1 className="font-display max-w-3xl text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-6xl">
          Entrena con la forma correcta, en cada repetición.
        </h1>

        <p className="mt-6 max-w-xl text-balance text-base text-muted sm:text-lg">
          SMART-GYM analiza tu técnica con la cámara de tu computadora y te
          corrige en vivo, para que entrenes más seguro y aproveches cada
          serie al máximo.
        </p>

        {racha >= 1 && (
          <div className="mt-5 flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-2 text-sm">
            <span className="font-semibold text-brand">
              🔥 {racha} día{racha !== 1 ? "s" : ""} seguidos
            </span>
            — no rompas la racha hoy
          </div>
        )}

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link
            href="#ejercicios"
            className="rounded-lg bg-brand px-6 py-3 text-sm font-semibold text-black transition hover:bg-brand-dark"
          >
            Elegir un ejercicio
          </Link>
          <Link
            href="/dashboard"
            className="rounded-lg border border-border px-6 py-3 text-sm font-semibold text-foreground transition hover:bg-surface"
          >
            Ver mi progreso
          </Link>
        </div>
      </div>
    </section>
  );
}
