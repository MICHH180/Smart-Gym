import Link from "next/link";
import { notFound } from "next/navigation";
import { getExerciseById } from "../../../lib/exercises";
import StreakNudge from "../../../components/StreakNudge";
import ExerciseMedia from "../../../components/ExerciseMedia";

export default async function ExerciseTutorialPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const exercise = getExerciseById(id);

  if (!exercise || !exercise.available) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
      <Link
        href="/#ejercicios"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-muted transition hover:text-foreground"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          className="h-4 w-4"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7M4 12h16" />
        </svg>
        Volver a ejercicios
      </Link>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          {exercise.name}
        </h1>
        <span className="rounded-full border border-border px-3 py-1 text-xs font-medium text-muted">
          {exercise.difficulty}
        </span>
        <span className="rounded-full border border-border px-3 py-1 text-xs font-medium text-muted">
          {exercise.duration}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap gap-1.5">
        {exercise.muscles.map((muscle) => (
          <span
            key={muscle}
            className="rounded-full bg-surface-2 px-2.5 py-1 text-xs text-muted"
          >
            {muscle}
          </span>
        ))}
      </div>

      <p className="mt-6 max-w-2xl text-base leading-relaxed text-muted">
        {exercise.description}
      </p>

      <div className="mt-8">
        <ExerciseMedia
          basePath={`/exercises/${exercise.id}/1`}
          alt={`${exercise.name} - demostración`}
          className="aspect-video w-full min-h-[220px] rounded-2xl sm:min-h-[320px] lg:min-h-[420px]"
        />
      </div>
      <p className="mt-3 text-center text-sm text-muted sm:text-left">
        Video o foto de demostración
      </p>

      <div className="mt-10 rounded-2xl border border-border bg-surface p-6">
        <h2 className="font-display text-lg font-semibold text-foreground">
          Cómo hacerlo bien
        </h2>
        <ul className="mt-4 space-y-3">
          {exercise.tips.map((tip) => (
            <li key={tip} className="flex items-start gap-3 text-sm text-muted">
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand/10 text-brand">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2.5}
                  className="h-3 w-3"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </span>
              {tip}
            </li>
          ))}
        </ul>
      </div>

      <StreakNudge />

      <div className="mt-6 flex justify-center">
        <Link
          href={`/sesiones/activa?ejercicio=${exercise.id}`}
          className="w-full max-w-sm rounded-xl bg-brand px-8 py-4 text-center text-base font-semibold text-black shadow-lg shadow-brand/20 transition hover:bg-brand-dark sm:w-auto"
        >
          Comenzar sesión
        </Link>
      </div>
    </div>
  );
}
