"use client";

import { useEffect, useRef, useState } from "react";

// Prueba estas extensiones en orden antes de rendirse y mostrar el ícono.
// Cubre el caso típico de Windows: el Explorador oculta la extensión real
// por default, así que "renombrar" una foto a .jpg a veces deja archivos
// como thumbnail.jpg.png en disco.
const EXTENSIONS = [
  "jpg",
  "png",
  "jpeg",
  "webp",
  "jpg.png",
  "png.png",
  "jpeg.png",
  "jpg.jpg",
  "png.jpg",
];

export default function ExerciseImage({
  basePath,
  alt,
  className = "",
}: {
  /** Ruta sin extensión, ej: "/exercises/sentadillas/thumbnail" */
  basePath: string;
  alt: string;
  className?: string;
}) {
  const [extIndex, setExtIndex] = useState(0);
  const [agotado, setAgotado] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    setExtIndex(0);
    setAgotado(false);
  }, [basePath]);

  function probarSiguienteExtension() {
    setExtIndex((i) => {
      if (i + 1 < EXTENSIONS.length) return i + 1;
      setAgotado(true);
      return i;
    });
  }

  useEffect(() => {
    // El servidor ya renderiza el <img>, así que el navegador puede
    // intentar cargarlo (y fallar) mientras parsea el HTML, antes de que
    // React termine de hidratar y conectar el onError de abajo. Sin este
    // chequeo, un 404 que ya pasó antes de hidratar queda sin detectar.
    const img = imgRef.current;
    if (img && img.complete && img.naturalWidth === 0) {
      probarSiguienteExtension();
    }
  });

  if (agotado) {
    return (
      <div
        className={`flex items-center justify-center rounded-xl border border-border bg-surface-2 ${className}`}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          className="h-8 w-8 text-muted"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6.5 6.5v11M17.5 6.5v11M2 9v6M22 9v6M6.5 12h11"
          />
        </svg>
      </div>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      key={extIndex}
      ref={imgRef}
      src={`${basePath}.${EXTENSIONS[extIndex]}`}
      alt={alt}
      onError={probarSiguienteExtension}
      className={`rounded-xl border border-border bg-surface-2 object-contain ${className}`}
    />
  );
}
