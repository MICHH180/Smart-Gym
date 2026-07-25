"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getDashboardData, type DashboardData } from "../../lib/dashboard";
import { getUsuarioActual } from "../../lib/api";
import StatCard from "../../components/StatCard";
import SessionHistoryTable from "../../components/SessionHistoryTable";

const ICONS = {
  sessions: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3M4 11h16M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z" />
    </svg>
  ),
  reps: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6.5 6.5v11M17.5 6.5v11M2 9v6M22 9v6M6.5 12h11" />
    </svg>
  ),
  errors: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.3 3.86 1.82 18a1 1 0 0 0 .86 1.5h18.64a1 1 0 0 0 .86-1.5L13.7 3.86a1 1 0 0 0-1.72 0Z" />
    </svg>
  ),
  time: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  ),
};

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;

    getUsuarioActual().then((usuario) => {
      if (cancelado) return;

      if (!usuario) {
        router.push("/login");
        return;
      }

      getDashboardData()
        .then((d) => !cancelado && setData(d))
        .catch(() => !cancelado && setError("No se pudo cargar tu progreso."));
    });

    return () => {
      cancelado = true;
    };
  }, [router]);

  if (error) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10 text-center sm:px-6 lg:px-8">
        <p className="text-danger">{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <p className="text-muted">Cargando tu progreso...</p>
      </div>
    );
  }

  const { stats, sessions, achievements } = data;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground">
          Tu progreso
        </h1>
        <p className="mt-1 text-muted">
          Resumen de tus sesiones de entrenamiento.
        </p>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Sesiones totales" value={stats.totalSessions} icon={ICONS.sessions} />
        <StatCard label="Repeticiones totales" value={stats.totalReps} icon={ICONS.reps} />
        <StatCard label="Errores de forma" value={stats.totalFormErrors} icon={ICONS.errors} />
        <StatCard label="Minutos entrenados" value={stats.totalMinutes} icon={ICONS.time} />
      </div>

      <div className="mt-9">
        <h2 className="font-display text-xl font-semibold text-foreground">
          Logros recientes
        </h2>
        <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-3">
          {achievements.map((logro) => (
            <div
              key={logro.id}
              className={`rounded-2xl border bg-surface p-4 text-center ${
                logro.unlocked ? "border-border" : "border-dashed border-border opacity-50"
              }`}
            >
              <div className="text-2xl">{logro.emoji}</div>
              <div
                className={`mt-1.5 text-sm ${logro.unlocked ? "text-foreground" : "text-muted"}`}
              >
                {logro.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-10">
        <h2 className="font-display text-xl font-semibold text-foreground">
          Historial de sesiones
        </h2>
        <div className="mt-4">
          <SessionHistoryTable sessions={sessions} />
        </div>
      </div>
    </div>
  );
}
