import Link from "next/link";
import type { Exercise } from "../lib/exercises";
import ExerciseImage from "./ExerciseImage";

export default function ExerciseCard({ exercise }: { exercise: Exercise }) {
  const thumbnail = (
    <ExerciseImage
      basePath={`/exercises/${exercise.id}/thumbnail`}
      alt={exercise.name}
      className="h-20 w-24 shrink-0 sm:h-[110px] sm:w-40"
    />
  );

  if (!exercise.available) {
    return (
      <div className="flex items-center gap-4 rounded-2xl border border-border bg-surface p-4 opacity-55 sm:gap-5">
        {thumbnail}
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-display text-lg font-semibold text-foreground">
              {exercise.name}
            </span>
            <span className="rounded-full border border-border px-2.5 py-0.5 text-[11px] font-medium text-muted">
              Próximamente
            </span>
          </div>
          <p className="mt-1 text-sm text-muted">{exercise.shortDescription}</p>
        </div>
      </div>
    );
  }

  return (
    <Link
      href={`/ejercicios/${exercise.id}`}
      className="group flex items-center gap-4 rounded-2xl border border-border bg-surface p-4 transition hover:border-brand/50 hover:bg-surface-2 sm:gap-5"
    >
      {thumbnail}
      <div className="flex-1">
        <div className="font-display text-lg font-semibold text-foreground">
          {exercise.name}
        </div>
        <p className="mt-1 text-sm text-muted">{exercise.shortDescription}</p>
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {exercise.muscles.map((muscle) => (
            <span
              key={muscle}
              className="rounded-full bg-surface-2 px-2.5 py-1 text-xs text-muted"
            >
              {muscle}
            </span>
          ))}
        </div>
      </div>
      <span className="shrink-0 text-sm font-semibold text-brand">
        Ver tutorial →
      </span>
    </Link>
  );
}
