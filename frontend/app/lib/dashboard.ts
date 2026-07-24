import { API_URL } from "./api";

export type DashboardStats = {
  totalSessions: number;
  totalReps: number;
  totalFormErrors: number;
  totalMinutes: number;
};

export type SessionRecord = {
  id: string;
  exerciseName: string;
  date: string;
  reps: number;
  formErrors: number;
  durationMinutes: number;
};

export async function getDashboardData(): Promise<{
  stats: DashboardStats;
  sessions: SessionRecord[];
}> {
  const res = await fetch(`${API_URL}/api/dashboard`, {
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error("No se pudo cargar el progreso.");
  }

  return res.json();
}
