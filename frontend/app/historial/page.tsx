import Link from "next/link";
import GraficosHistorial from "./GraficosHistorial";

interface RepsPorDia {
  date: string;
  count: number;
}

interface EstadisticasGenerales {
  totalSessions: number;
  totalReps: number;
  errorsByType: Record<string, number>;
  repsByDay: RepsPorDia[];
}

interface SesionResumen {
  id: string;
  exercise: string;
  startedAt: string;
  endedAt: string | null;
  repCount: number;
  formErrorCount: number;
}

const BACKEND_HTTP_URL = process.env.BACKEND_HTTP_URL ?? "http://localhost:8000";

const ESTADISTICAS_VACIAS: EstadisticasGenerales = {
  totalSessions: 0,
  totalReps: 0,
  errorsByType: {},
  repsByDay: [],
};

async function obtenerDatosHistorial(): Promise<{
  stats: EstadisticasGenerales;
  sesiones: SesionResumen[];
  error: string | null;
}> {
  try {
    const [statsRes, sesionesRes] = await Promise.all([
      fetch(`${BACKEND_HTTP_URL}/api/stats`, { cache: "no-store" }),
      fetch(`${BACKEND_HTTP_URL}/api/sessions?limit=20`, { cache: "no-store" }),
    ]);

    if (!statsRes.ok || !sesionesRes.ok) {
      throw new Error("Respuesta no exitosa del backend");
    }

    const [stats, sesiones] = await Promise.all([
      statsRes.json() as Promise<EstadisticasGenerales>,
      sesionesRes.json() as Promise<SesionResumen[]>,
    ]);

    return { stats, sesiones, error: null };
  } catch {
    return {
      stats: ESTADISTICAS_VACIAS,
      sesiones: [],
      error:
        "No se pudo conectar con el servidor. ¿Está corriendo el backend (uvicorn backend.app:app)?",
    };
  }
}

// startedAt/endedAt llegan como datetime ISO completo (con hora y offset),
// así que `new Date(...)` es seguro acá (a diferencia de las fechas sueltas
// "YYYY-MM-DD" de repsByDay, que se parsean a mano en GraficosHistorial).
function formatFechaHora(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return iso;
  const dia = String(fecha.getDate()).padStart(2, "0");
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const anio = fecha.getFullYear();
  const horas = String(fecha.getHours()).padStart(2, "0");
  const minutos = String(fecha.getMinutes()).padStart(2, "0");
  return `${dia}/${mes}/${anio} ${horas}:${minutos}`;
}

function formatDuracion(startedAt: string, endedAt: string | null): string {
  if (!endedAt) return "En curso";
  const inicio = new Date(startedAt).getTime();
  const fin = new Date(endedAt).getTime();
  if (Number.isNaN(inicio) || Number.isNaN(fin) || fin < inicio) return "—";

  const totalMinutos = Math.round((fin - inicio) / 60000);
  if (totalMinutos < 60) return `${totalMinutos} min`;
  const horas = Math.floor(totalMinutos / 60);
  const minutosRestantes = totalMinutos % 60;
  return minutosRestantes === 0 ? `${horas}h` : `${horas}h ${minutosRestantes}min`;
}

export default async function HistorialPage() {
  const { stats, sesiones, error } = await obtenerDatosHistorial();

  return (
    <main className="flex-1 flex flex-col items-center gap-8 px-4 py-10 sm:py-16">
      <header className="w-full max-w-4xl text-center">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
          Historial de Entrenamiento
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Estadísticas y sesiones pasadas —{" "}
          <Link href="/" className="underline hover:no-underline">
            volver a la vista en vivo
          </Link>
        </p>
      </header>

      <div className="w-full max-w-4xl flex flex-col gap-8">
        {error && (
          <p className="text-sm font-medium text-red-600 dark:text-red-400 text-center">
            {error}
          </p>
        )}

        {/* KPIs */}
        <div className="grid grid-cols-2 gap-3 w-full">
          <div className="flex flex-col items-center gap-1 rounded-lg bg-gray-100 dark:bg-white/5 py-4 px-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Sesiones totales
            </span>
            <span className="text-3xl sm:text-4xl font-semibold">
              {stats.totalSessions}
            </span>
          </div>

          <div className="flex flex-col items-center gap-1 rounded-lg bg-gray-100 dark:bg-white/5 py-4 px-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Repeticiones totales
            </span>
            <span className="text-3xl sm:text-4xl font-semibold">
              {stats.totalReps}
            </span>
          </div>
        </div>

        {/* Gráficos */}
        <GraficosHistorial repsByDay={stats.repsByDay} errorsByType={stats.errorsByType} />

        {/* Tabla de sesiones */}
        <div className="w-full">
          <h2 className="text-lg font-semibold mb-3">Sesiones recientes</h2>

          {sesiones.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              Todavía no completaste ninguna sesión — probá{" "}
              <Link href="/" className="underline hover:no-underline">
                la vista en vivo
              </Link>{" "}
              primero.
            </p>
          ) : (
            <div className="w-full overflow-x-auto rounded-lg border border-black/10 dark:border-white/10">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-100 dark:bg-white/5">
                  <tr>
                    <th className="px-3 py-2 font-semibold">Fecha</th>
                    <th className="px-3 py-2 font-semibold">Duración</th>
                    <th className="px-3 py-2 font-semibold tabular-nums">Reps</th>
                    <th className="px-3 py-2 font-semibold tabular-nums">Errores</th>
                  </tr>
                </thead>
                <tbody>
                  {sesiones.map((sesion) => (
                    <tr
                      key={sesion.id}
                      className="border-t border-black/10 dark:border-white/10"
                    >
                      <td className="px-3 py-2">{formatFechaHora(sesion.startedAt)}</td>
                      <td className="px-3 py-2">
                        {formatDuracion(sesion.startedAt, sesion.endedAt)}
                      </td>
                      <td className="px-3 py-2 tabular-nums">{sesion.repCount}</td>
                      <td className="px-3 py-2 tabular-nums">{sesion.formErrorCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
