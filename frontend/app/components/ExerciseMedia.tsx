"use client";

import { useEffect, useRef, useState } from "react";

// Video primero; si no hay MP4/WebM, cae a imagen (misma lógica que ExerciseImage).
const MEDIA_CANDIDATES = [
  "mp4",
  "webm",
  "jpg",
  "png",
  "jpeg",
  "webp",
  "mp4.mp4",
  "jpg.png",
  "png.png",
  "jpeg.png",
  "jpg.jpg",
  "png.jpg",
];

function esVideo(ext: string) {
  return ext === "mp4" || ext === "webm" || ext === "mp4.mp4";
}

function Placeholder({ className }: { className: string }) {
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
        className="h-14 w-14 text-muted"
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

export default function ExerciseMedia({
  basePath,
  alt,
  className = "",
}: {
  /** Ruta sin extensión, ej: "/exercises/sentadillas/1" */
  basePath: string;
  alt: string;
  className?: string;
}) {
  const [index, setIndex] = useState(0);
  const [agotado, setAgotado] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    setIndex(0);
    setAgotado(false);
  }, [basePath]);

  function probarSiguiente() {
    setIndex((i) => {
      if (i + 1 < MEDIA_CANDIDATES.length) return i + 1;
      setAgotado(true);
      return i;
    });
  }

  useEffect(() => {
    const img = imgRef.current;
    if (img && img.complete && img.naturalWidth === 0) {
      probarSiguiente();
    }
  });

  if (agotado) {
    return <Placeholder className={className} />;
  }

  const ext = MEDIA_CANDIDATES[index];
  const src = `${basePath}.${ext}`;

  if (esVideo(ext)) {
    return (
      <video
        key={index}
        src={src}
        controls
        playsInline
        preload="metadata"
        onError={probarSiguiente}
        className={`rounded-xl border border-border object-cover ${className}`}
      >
        {alt}
      </video>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      key={index}
      ref={imgRef}
      src={src}
      alt={alt}
      onError={probarSiguiente}
      className={`rounded-xl border border-border object-cover ${className}`}
    />
  );
}
