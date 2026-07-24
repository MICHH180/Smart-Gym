import Link from "next/link";
import type { Exercise } from "../lib/exercises";

export default function ExerciseCard({ exercise }: { exercise: Exercise }) {
  const cardContent = (
    <>
      <div className="flex aspect-video items-center justify-center rounded-xl border border-border bg-surface-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          className="h-10 w-10 text-muted"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6.5 6.5v11M17.5 6.5v11M2 9v6M22 9v6M6.5 12h11"
          />
        </svg>
      </div>

      <div className="mt-4 flex items-start justify-between gap-2">
        <h3 className="font-display text-lg font-semibold text-foreground">
          {exercise.name}
        </h3>
        {!exercise.available && (
          <span className="shrink-0 rounded-full border border-border px-2.5 py-0.5 text-[11px] font-medium text-muted">
            Próximamente
          </span>
        )}
      </div>
      <p className="mt-1.5 text-sm text-muted">{exercise.shortDescription}</p>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {exercise.muscles.map((muscle) => (
          <span
            key={muscle}
            className="rounded-full bg-surface-2 px-2.5 py-1 text-xs text-muted"
          >
            {muscle}
          </span>
        ))}
      </div>
    </>
  );

  if (!exercise.available) {
    return (
      <div className="cursor-not-allowed rounded-2xl border border-border bg-surface p-5 opacity-60">
        {cardContent}
      </div>
    );
  }

  return (
    <Link
      href={`/ejercicios/${exercise.id}`}
      className="group rounded-2xl border border-border bg-surface p-5 transition hover:border-brand/50 hover:bg-surface-2"
    >
      {cardContent}
      <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand">
        Ver tutorial
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          className="h-4 w-4 transition group-hover:translate-x-0.5"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      </span>
    </Link>
  );
}
