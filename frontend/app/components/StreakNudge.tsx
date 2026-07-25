"use client";

import { useUsuarioActual } from "../lib/useUsuarioActual";

export default function StreakNudge() {
  const { usuario } = useUsuarioActual();
  if (!usuario) return null;

  const proximaRacha = usuario.racha + 1;

  return (
    <div className="mt-5 flex justify-center">
      <span className="rounded-full border border-border bg-surface px-4.5 py-2 text-sm text-muted">
        🔥 Completa hoy y llega a{" "}
        <span className="font-semibold text-brand">
          {proximaRacha} día{proximaRacha !== 1 ? "s" : ""}
        </span>{" "}
        de racha
      </span>
    </div>
  );
}
