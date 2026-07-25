"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { getExerciseById } from "../../../lib/exercises";
import {
  API_URL,
  getUsuarioActual,
  iniciarSesionEntrenamiento,
  finalizarSesionEntrenamiento,
} from "../../../lib/api";

function ActiveSessionContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const ejercicioId = searchParams.get("ejercicio") ?? undefined;
  const exercise = ejercicioId ? getExerciseById(ejercicioId) : undefined;

  const [sesionId, setSesionId] = useState<number | null>(null);
  const [finalizando, setFinalizando] = useState(false);

  useEffect(() => {
    // Sin ejercicio reconocido y disponible no hay nada que entrenar: se
    // manda de vuelta a elegir uno en vez de intentar arrancar una sesión
    // inválida contra el backend.
    if (!exercise || !exercise.available) {
      router.push("/#ejercicios");
      return;
    }

    let cancelado = false;

    getUsuarioActual().then((usuario) => {
      if (cancelado) return;
      if (!usuario) {
        router.push("/login");
        return;
      }
      iniciarSesionEntrenamiento(exercise.id)
        .then((id) => !cancelado && setSesionId(id))
        .catch(() => !cancelado && router.push("/dashboard"));
    });

    return () => {
      cancelado = true;
    };
  }, [router, exercise]);

  async function handleFinalizar() {
    setFinalizando(true);
    if (sesionId !== null) {
      // Se avisa al server explícitamente en vez de confiar en que el
      // navegador cierre la conexión del <img> al desmontarse: los
      // navegadores suelen dejar esa conexión viva por keep-alive un rato,
      // así que el server nunca se enteraría a tiempo de que terminamos.
      await finalizarSesionEntrenamiento(sesionId);
    }
    router.push("/dashboard");
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-muted">Sesión en vivo</p>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            {exercise ? exercise.name : "Ejercicio"}
          </h1>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-muted">
          <span className="h-2 w-2 animate-pulse rounded-full bg-danger" />
          En vivo
        </div>
      </div>

      {/*
        Contenedor para el componente existente de cámara/tracking
        (webcam + MediaPipe). No se modifica esa lógica: solo se monta acá.
        El <img> no se monta hasta tener un sesionId real del server.
      */}
      <div className="mt-6 flex aspect-video w-full items-center justify-center overflow-hidden rounded-2xl border border-border bg-surface-2">
        {sesionId !== null ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={`${API_URL}/video_feed?sesion_id=${sesionId}`}
            alt="Cámara Smart-Gym en vivo"
            className="w-full h-full object-cover"
          />
        ) : (
          <p className="text-sm text-muted">Iniciando sesión...</p>
        )}
      </div>

      <div className="mt-6 grid grid-cols-3 gap-3">
        {[
          { label: "Repeticiones", value: "—" },
          { label: "Errores de forma", value: "—" },
          { label: "Tiempo", value: "—" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-xl border border-border bg-surface px-4 py-3 text-center"
          >
            <p className="font-display text-2xl font-semibold text-foreground">
              {stat.value}
            </p>
            <p className="mt-0.5 text-xs text-muted">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 flex justify-center">
        <button
          type="button"
          onClick={handleFinalizar}
          disabled={finalizando}
          className="w-full max-w-xs rounded-xl border border-danger/40 bg-danger/10 px-8 py-4 text-center text-base font-semibold text-danger transition hover:bg-danger/20 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {finalizando ? "Guardando..." : "Detener y finalizar"}
        </button>
      </div>
    </div>
  );
}

export default function ActiveSessionPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto flex max-w-5xl justify-center px-4 py-8 text-sm text-muted sm:px-6 lg:px-8">
          Cargando sesión...
        </div>
      }
    >
      <ActiveSessionContent />
    </Suspense>
  );
}
