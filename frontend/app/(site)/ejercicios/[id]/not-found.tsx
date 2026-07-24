import Link from "next/link";

export default function ExerciseNotFound() {
  return (
    <div className="mx-auto flex max-w-4xl flex-col items-center px-4 py-24 text-center sm:px-6">
      <h1 className="font-display text-3xl font-semibold text-foreground">
        No encontramos ese ejercicio
      </h1>
      <p className="mt-3 max-w-md text-muted">
        Puede que el ejercicio no exista o todavía no esté disponible.
      </p>
      <Link
        href="/#ejercicios"
        className="mt-8 rounded-lg bg-brand px-6 py-3 text-sm font-semibold text-black transition hover:bg-brand-dark"
      >
        Ver ejercicios disponibles
      </Link>
    </div>
  );
}
