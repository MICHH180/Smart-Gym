export const API_URL = "http://localhost:8000";

export type Usuario = {
  id: number;
  nombre: string;
  email: string;
};

export async function getUsuarioActual(): Promise<Usuario | null> {
  try {
    const res = await fetch(`${API_URL}/api/auth/me`, {
      credentials: "include",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    // Backend inalcanzable (caído, reiniciando, sin red): tratamos como
    // "no hay sesión" en vez de tirar abajo la página con un error de runtime.
    return null;
  }
}

export async function cerrarSesion(): Promise<void> {
  try {
    await fetch(`${API_URL}/api/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // Si el backend no responde, igual limpiamos el estado del lado del cliente.
  }
}

export async function iniciarSesionEntrenamiento(): Promise<number> {
  const res = await fetch(`${API_URL}/api/sesiones/iniciar`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error("No se pudo iniciar la sesión de entrenamiento.");
  const data = await res.json();
  return data.sesionId;
}

export async function finalizarSesionEntrenamiento(sesionId: number): Promise<void> {
  try {
    await fetch(`${API_URL}/api/sesiones/${sesionId}/finalizar`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // Best-effort: si esto falla, el watcher de desconexión del server
    // igual va a intentar cerrar la sesión más tarde.
  }
}
