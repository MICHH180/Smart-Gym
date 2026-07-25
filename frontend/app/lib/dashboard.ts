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

export type Achievement = {
  id: string;
  emoji: string;
  label: string;
  unlocked: boolean;
};

export type DashboardData = {
  stats: DashboardStats;
  sessions: SessionRecord[];
  streak: number;
  achievements: Achievement[];
};

export async function getDashboardData(): Promise<DashboardData> {
  const res = await fetch(`${API_URL}/api/dashboard`, {
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error("No se pudo cargar el progreso.");
  }

  return res.json();
}
