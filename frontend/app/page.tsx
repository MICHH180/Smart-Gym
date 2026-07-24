"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type ConnectionState =
  | "idle"
  | "pidiendo-camara"
  | "conectando"
  | "en-vivo"
  | "error";

interface StatsMensaje {
  angulo: number;
  contador: number;
  alerta: string;
  // Orden RGB: el backend ya invierte el BGR nativo de OpenCV en el límite de la API.
  color_alerta: [number, number, number];
  evento_voz: string | null;
  form_score: number | null;
  landmarks: { x: number; y: number }[] | null;
}

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/session";

// Conexiones del esqueleto MediaPipe BlazePose (33 puntos): solo torso/brazos/piernas,
// sin detalle de cara, manos ni pies.
const CONEXIONES_ESQUELETO: [number, number][] = [
  [11, 12], // hombros
  [11, 13], [13, 15], // brazo izquierdo
  [12, 14], [14, 16], // brazo derecho
  [11, 23], [12, 24], // torso
  [23, 24], // cadera
  [23, 25], [25, 27], // pierna izquierda
  [24, 26], [26, 28], // pierna derecha
];

export default function Home() {
  const [estado, setEstado] = useState<ConnectionState>("idle");
  const [errorMensaje, setErrorMensaje] = useState("");
  const [stats, setStats] = useState<StatsMensaje | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const detenidoManualRef = useRef(false);

  const limpiarRecursos = useCallback(() => {
    detenidoManualRef.current = true;

    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  // No dejar la luz de la cámara prendida ni el socket abierto si el usuario navega fuera.
  useEffect(() => {
    return () => {
      limpiarRecursos();
    };
  }, [limpiarRecursos]);

  const capturarYEnviar = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ws = wsRef.current;
    if (!video || !canvas || !ws || ws.readyState !== WebSocket.OPEN) return;
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        const socket = wsRef.current;
        if (!blob || !socket || socket.readyState !== WebSocket.OPEN) return;
        blob.arrayBuffer().then((buffer) => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(buffer);
          }
        });
      },
      "image/jpeg",
      0.8
    );
  }, []);

  const dibujarEsqueleto = useCallback(
    (landmarks: { x: number; y: number }[] | null) => {
      const canvas = overlayRef.current;
      const video = videoRef.current;
      if (!canvas || !video) return;

      if (
        video.videoWidth > 0 &&
        video.videoHeight > 0 &&
        (canvas.width !== video.videoWidth ||
          canvas.height !== video.videoHeight)
      ) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
      }

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (!landmarks || landmarks.length === 0) return;

      ctx.strokeStyle = "#39FF14";
      ctx.lineWidth = 3;
      ctx.lineCap = "round";

      for (const [a, b] of CONEXIONES_ESQUELETO) {
        const pa = landmarks[a];
        const pb = landmarks[b];
        if (!pa || !pb) continue;
        ctx.beginPath();
        ctx.moveTo(pa.x * canvas.width, pa.y * canvas.height);
        ctx.lineTo(pb.x * canvas.width, pb.y * canvas.height);
        ctx.stroke();
      }
    },
    []
  );

  const iniciar = useCallback(async () => {
    // Warm-up síncrono del motor de voz, disparado directamente dentro del
    // gesto de click: los navegadores con políticas estrictas de autoplay
    // (Chrome/Edge) bloquean speechSynthesis.speak() si nunca se llamó desde
    // una interacción real del usuario. Sin esto, el primer evento_voz que
    // llegue de forma asíncrona por el WebSocket (ej. "Bien 1") puede quedar
    // mudo. Esta llamada "desbloquea" el motor para todos los speak() futuros.
    const warmup = new SpeechSynthesisUtterance("Cámara activada");
    warmup.lang = "es-MX";
    window.speechSynthesis.speak(warmup);

    detenidoManualRef.current = false;
    setErrorMensaje("");
    setStats(null);
    setEstado("pidiendo-camara");

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
    } catch {
      setEstado("error");
      setErrorMensaje(
        "No se pudo acceder a la cámara. Revisá los permisos del navegador e intentá de nuevo."
      );
      return;
    }

    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
    }

    setEstado("conectando");

    const ws = new WebSocket(WS_URL);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    // Pacing estricto request/response: el backend procesa un frame por vez
    // (receive_bytes -> send_json en loop), así que solo pedimos el siguiente
    // frame cuando llega la respuesta del anterior. Nunca a intervalo fijo.
    ws.onopen = () => {
      setEstado("en-vivo");
      capturarYEnviar();
    };

    ws.onmessage = (event) => {
      try {
        const data: StatsMensaje = JSON.parse(event.data as string);
        setStats(data);
        dibujarEsqueleto(data.landmarks);
        if (data.evento_voz) {
          window.speechSynthesis.speak(
            new SpeechSynthesisUtterance(data.evento_voz)
          );
        }
      } catch {
        // Mensaje no parseable: no rompemos el loop, seguimos pidiendo frames.
      }
      capturarYEnviar();
    };

    ws.onclose = () => {
      if (!detenidoManualRef.current) {
        setEstado("error");
        setErrorMensaje(
          "Se perdió la conexión con el servidor. ¿Está corriendo el backend (uvicorn backend.app:app)?"
        );
      }
    };
  }, [capturarYEnviar, dibujarEsqueleto]);

  const detener = useCallback(() => {
    limpiarRecursos();
    setEstado("idle");
    setStats(null);
  }, [limpiarRecursos]);

  const reintentar = useCallback(() => {
    setEstado("idle");
    setErrorMensaje("");
  }, []);

  const colorEstado = stats
    ? `rgb(${stats.color_alerta[0]}, ${stats.color_alerta[1]}, ${stats.color_alerta[2]})`
    : undefined;

  const mostrarVideo =
    estado === "pidiendo-camara" || estado === "conectando" || estado === "en-vivo";

  return (
    <main className="flex-1 flex flex-col items-center gap-6 px-4 py-10 sm:py-16">
      <header className="text-center">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
          Smart Gym
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Sentadillas en vivo — seguimiento por webcam
        </p>
      </header>

      <div className="w-full max-w-2xl flex flex-col items-center gap-6">
        {/* Video: montado siempre para que el ref esté listo antes de que resuelva getUserMedia */}
        <div
          className={`relative w-full aspect-video rounded-xl overflow-hidden bg-black border border-black/10 dark:border-white/10 ${
            mostrarVideo ? "" : "hidden"
          }`}
        >
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
            style={{ transform: "scaleX(-1)" }}
          />
          <canvas
            ref={overlayRef}
            className="absolute inset-0 w-full h-full pointer-events-none"
            style={{ transform: "scaleX(-1)" }}
          />
        </div>
        <canvas ref={canvasRef} className="hidden" />

        {estado === "idle" && (
          <button
            onClick={iniciar}
            className="px-6 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors"
          >
            Comenzar
          </button>
        )}

        {estado === "pidiendo-camara" && (
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Solicitando acceso a la cámara…
          </p>
        )}

        {estado === "conectando" && (
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Conectando con el servidor…
          </p>
        )}

        {estado === "error" && (
          <div className="w-full flex flex-col items-center gap-3 text-center">
            <p className="text-sm font-medium text-red-600 dark:text-red-400">
              {errorMensaje}
            </p>
            <button
              onClick={reintentar}
              className="px-6 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors"
            >
              Reintentar
            </button>
          </div>
        )}

        {estado === "en-vivo" && (
          <div className="w-full flex flex-col gap-4">
            <div className="grid grid-cols-3 gap-3 w-full">
              <div className="flex flex-col items-center gap-1 rounded-lg bg-gray-100 dark:bg-white/5 py-4 px-2">
                <span className="text-xs font-semibold tracking-wide text-gray-500 dark:text-gray-400 uppercase">
                  Reps
                </span>
                <span className="text-4xl font-bold tabular-nums">
                  {stats?.contador ?? 0}
                </span>
              </div>

              <div className="flex flex-col items-center gap-1 rounded-lg bg-gray-100 dark:bg-white/5 py-4 px-2">
                <span className="text-xs font-semibold tracking-wide text-gray-500 dark:text-gray-400 uppercase">
                  Estado
                </span>
                <span
                  className="text-lg font-bold text-center leading-tight"
                  style={{ color: colorEstado }}
                >
                  {stats?.alerta ?? "--"}
                </span>
              </div>

              <div className="flex flex-col items-center gap-1 rounded-lg bg-gray-100 dark:bg-white/5 py-4 px-2">
                <span className="text-xs font-semibold tracking-wide text-gray-500 dark:text-gray-400 uppercase">
                  Forma
                </span>
                <span className="text-4xl font-bold tabular-nums">
                  {stats?.form_score ?? "--"}
                </span>
              </div>
            </div>

            <button
              onClick={detener}
              className="self-center px-6 py-3 rounded-lg bg-red-600 text-white font-semibold hover:bg-red-700 transition-colors"
            >
              Detener
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
