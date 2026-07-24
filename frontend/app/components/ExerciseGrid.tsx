import { exercises } from "../lib/exercises";
import ExerciseCard from "./ExerciseCard";

export default function ExerciseGrid() {
  return (
    <section id="ejercicios" className="scroll-mt-16">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Elegí tu ejercicio
          </h2>
          <p className="mt-4 text-muted">
            Cada ejercicio incluye un tutorial guiado antes de arrancar la
            sesión con cámara.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {exercises.map((exercise) => (
            <ExerciseCard key={exercise.id} exercise={exercise} />
          ))}
        </div>
      </div>
    </section>
  );
}
