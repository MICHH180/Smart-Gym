"use client";

import { useEffect, useState } from "react";
import { getUsuarioActual, type Usuario } from "./api";

export function useUsuarioActual() {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelado = false;

    getUsuarioActual()
      .then((u) => !cancelado && setUsuario(u))
      .finally(() => !cancelado && setLoading(false));

    return () => {
      cancelado = true;
    };
  }, []);

  return { usuario, loading };
}
