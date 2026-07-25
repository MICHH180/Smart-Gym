const FEATURES = [
  {
    title: "Detección de postura en vivo",
    description:
      "Un modelo de pose estimation ubica tus articulaciones en cada frame de la cámara, sin necesidad de sensores ni wearables.",
  },
  {
    title: "Corrección de forma en tiempo real",
    description:
      "Comparamos los ángulos de tu movimiento contra el rango correcto del ejercicio y te avisamos al instante si algo se desvía.",
  },
  {
    title: "Conteo automático de repeticiones",
    description:
      "Cada repetición válida se cuenta sola, así te concentras en la técnica y no en llevar la cuenta.",
  },
];

export default function About() {
  return (
    <section className="border-b border-border bg-surface/40">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Tu entrenador de forma, potenciado por IA
          </h2>
          <p className="mt-4 text-muted">
            SMART-GYM usa visión por computadora para leer tu cuerpo en cada
            frame y darte feedback inmediato, como si tuvieras un coach
            mirando cada repetición.
          </p>
        </div>

        <div className="mt-14 grid gap-6 sm:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="rounded-2xl border border-border bg-surface p-6"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  className="h-5 w-5"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 2l2.6 6.2L21 9l-5 4.4L17.5 20 12 16.5 6.5 20 8 13.4 3 9l6.4-.8L12 2z"
                  />
                </svg>
              </div>
              <h3 className="font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
