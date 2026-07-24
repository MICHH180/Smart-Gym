import type { SessionRecord } from "../lib/dashboard";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "short",
  });
}

export default function SessionHistoryTable({
  sessions,
}: {
  sessions: SessionRecord[];
}) {
  if (sessions.length === 0) {
    return (
      <div className="rounded-2xl border border-border bg-surface p-10 text-center text-sm text-muted">
        Todavía no completaste ninguna sesión.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-surface">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-muted">
              <th className="px-5 py-3 font-medium">Ejercicio</th>
              <th className="px-5 py-3 font-medium">Fecha</th>
              <th className="px-5 py-3 font-medium">Repeticiones</th>
              <th className="px-5 py-3 font-medium">Errores de forma</th>
              <th className="px-5 py-3 font-medium">Duración</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {sessions.map((session) => (
              <tr key={session.id} className="transition hover:bg-surface-2">
                <td className="px-5 py-3.5 font-medium text-foreground">
                  {session.exerciseName}
                </td>
                <td className="px-5 py-3.5 text-muted">
                  {formatDate(session.date)}
                </td>
                <td className="px-5 py-3.5 text-muted">{session.reps}</td>
                <td className="px-5 py-3.5">
                  <span
                    className={
                      session.formErrors === 0
                        ? "text-brand"
                        : "text-danger"
                    }
                  >
                    {session.formErrors}
                  </span>
                </td>
                <td className="px-5 py-3.5 text-muted">
                  {session.durationMinutes} min
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
