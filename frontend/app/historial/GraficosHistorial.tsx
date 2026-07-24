"use client";

import { useRef, useState } from "react";

interface RepsPorDia {
  date: string;
  count: number;
}

interface GraficosHistorialProps {
  repsByDay: RepsPorDia[];
  errorsByType: Record<string, number>;
}

// --- Chart 1: Repeticiones por día -----------------------------------

const VB1_WIDTH = 600;
const VB1_HEIGHT = 200;
const MARGIN1 = { top: 16, right: 16, bottom: 24, left: 32 };

function nicePositiveMax(value: number): number {
  if (value <= 0) return 1;
  const exponent = Math.floor(Math.log10(value));
  const fraction = value / Math.pow(10, exponent);
  let niceFraction: number;
  if (fraction <= 1) niceFraction = 1;
  else if (fraction <= 2) niceFraction = 2;
  else if (fraction <= 5) niceFraction = 5;
  else niceFraction = 10;
  return niceFraction * Math.pow(10, exponent);
}

// Los strings de fecha son "YYYY-MM-DD" (sin hora): los parseamos a mano en
// vez de con `new Date(str)` para no correr riesgo de que el offset UTC
// corra el día en zonas horarias negativas.
function formatFechaCorta(isoDate: string): string {
  const [anio, mes, dia] = isoDate.split("-");
  if (!anio || !mes || !dia) return isoDate;
  return `${dia}/${mes}/${anio}`;
}

function GraficoRepsPorDia({ repsByDay }: { repsByDay: RepsPorDia[] }) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const plotW = VB1_WIDTH - MARGIN1.left - MARGIN1.right;
  const plotH = VB1_HEIGHT - MARGIN1.top - MARGIN1.bottom;
  const baselineY = MARGIN1.top + plotH;

  if (repsByDay.length === 0) {
    return (
      <p className="text-sm text-[var(--text-muted)] py-8 text-center">
        Sin datos de repeticiones todavía.
      </p>
    );
  }

  const maxCount = Math.max(...repsByDay.map((d) => d.count), 0);
  const niceMax = nicePositiveMax(maxCount);

  const xScale = (i: number, n: number) =>
    n <= 1 ? MARGIN1.left + plotW / 2 : MARGIN1.left + (i / (n - 1)) * plotW;
  const yScale = (value: number) =>
    MARGIN1.top + plotH - (value / niceMax) * plotH;

  const points = repsByDay.map((d, i) => ({
    x: xScale(i, repsByDay.length),
    y: yScale(d.count),
    date: d.date,
    count: d.count,
  }));

  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
    .join(" ");
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${baselineY} L ${points[0].x} ${baselineY} Z`;

  const tickCount = 4;
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) => (niceMax * i) / tickCount);

  const last = points[points.length - 1];

  const handlePointerMove = (e: React.PointerEvent<SVGRectElement>) => {
    const svg = svgRef.current;
    if (!svg || points.length === 0) return;
    const rect = svg.getBoundingClientRect();
    if (rect.width === 0) return;
    const scaleX = VB1_WIDTH / rect.width;
    const xInViewBox = (e.clientX - rect.left) * scaleX;
    const ratio = plotW === 0 ? 0 : (xInViewBox - MARGIN1.left) / plotW;
    const idx = Math.round(ratio * (points.length - 1));
    setHoverIdx(Math.max(0, Math.min(points.length - 1, idx)));
  };

  const handlePointerLeave = () => setHoverIdx(null);

  const hovered = hoverIdx !== null ? points[hoverIdx] : null;
  const tooltipLeftPct = hovered ? (hovered.x / VB1_WIDTH) * 100 : 0;
  const tooltipTopPct = hovered ? (hovered.y / VB1_HEIGHT) * 100 : 0;
  const tooltipTranslateX =
    tooltipLeftPct > 80 ? "-100%" : tooltipLeftPct < 20 ? "0%" : "-50%";

  return (
    <div className="relative" style={{ overflowX: "auto" }}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${VB1_WIDTH} ${VB1_HEIGHT}`}
        style={{ width: "100%", height: "auto", display: "block", minWidth: 280 }}
        role="img"
        aria-label="Repeticiones por día en los últimos 30 días"
      >
        {ticks.map((tickValue, i) => {
          const y = yScale(tickValue);
          const isBaseline = i === 0;
          return (
            <g key={tickValue}>
              <line
                x1={MARGIN1.left}
                x2={VB1_WIDTH - MARGIN1.right}
                y1={y}
                y2={y}
                stroke={isBaseline ? "var(--baseline)" : "var(--gridline)"}
                strokeWidth={1}
              />
              <text
                x={MARGIN1.left - 6}
                y={y}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize={10}
                fill="var(--text-muted)"
              >
                {Math.round(tickValue)}
              </text>
            </g>
          );
        })}

        <path d={areaPath} fill="var(--series-1)" fillOpacity={0.1} stroke="none" />
        <path
          d={linePath}
          fill="none"
          stroke="var(--series-1)"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        <circle cx={last.x} cy={last.y} r={6} fill="var(--surface-1)" />
        <circle
          cx={last.x}
          cy={last.y}
          r={4}
          fill="var(--series-1)"
          stroke="var(--surface-1)"
          strokeWidth={2}
        />
        <text
          x={last.x}
          y={last.y - 10}
          textAnchor={last.x > VB1_WIDTH - 60 ? "end" : "middle"}
          fontSize={11}
          fontWeight={600}
          fill="var(--text-primary)"
        >
          {last.count}
        </text>

        {hovered && (
          <line
            x1={hovered.x}
            x2={hovered.x}
            y1={MARGIN1.top}
            y2={baselineY}
            stroke="var(--text-muted)"
            strokeWidth={1}
          />
        )}

        {/* Overlay invisible para hit-testing del hover/crosshair */}
        <rect
          x={MARGIN1.left}
          y={MARGIN1.top}
          width={plotW}
          height={plotH}
          fill="transparent"
          onPointerMove={handlePointerMove}
          onPointerLeave={handlePointerLeave}
        />
      </svg>

      {hovered && (
        <div
          className="pointer-events-none absolute z-10 rounded-md border px-2 py-1 shadow-sm"
          style={{
            left: `${tooltipLeftPct}%`,
            top: `${tooltipTopPct}%`,
            transform: `translate(${tooltipTranslateX}, calc(-100% - 10px))`,
            background: "var(--surface-1)",
            borderColor: "var(--border)",
            whiteSpace: "nowrap",
          }}
        >
          <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            {hovered.count} reps
          </div>
          <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
            {formatFechaCorta(hovered.date)}
          </div>
        </div>
      )}
    </div>
  );
}

// --- Chart 2: Errores de forma por tipo -------------------------------

const VB2_WIDTH = 440;
const VB2_HEIGHT = 84;
const BAR_HEIGHT = 24;
const BAR_GAP = 2;
const LABEL_WIDTH = 76;
const VALUE_GAP = 8;
const VALUE_WIDTH = 32;
const ROW_TOP_PADDING = 8;

interface CategoriaError {
  key: "cadera" | "espalda";
  label: string;
  color: string;
  value: number;
}

function GraficoErroresPorTipo({ errorsByType }: { errorsByType: Record<string, number> }) {
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);

  const categorias: CategoriaError[] = [
    { key: "cadera", label: "Cadera", color: "var(--series-1)", value: errorsByType.cadera ?? 0 },
    { key: "espalda", label: "Espalda", color: "var(--series-2)", value: errorsByType.espalda ?? 0 },
  ];

  const sinDatos = categorias.every((c) => c.value === 0);

  const plotW = VB2_WIDTH - LABEL_WIDTH - VALUE_GAP - VALUE_WIDTH;
  const barMax = Math.max(...categorias.map((c) => c.value), 1);

  return (
    <div>
      {/* Color-key inline: satisface "legend siempre presente para ≥2 series" */}
      <div className="flex flex-wrap items-center gap-4 mb-2">
        {categorias.map((c) => (
          <span key={c.key} className="inline-flex items-center gap-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
            <span
              className="inline-block rounded-full"
              style={{ width: 8, height: 8, background: c.color }}
            />
            {c.label}
          </span>
        ))}
      </div>

      {sinDatos ? (
        <p className="text-sm text-[var(--text-muted)] py-8 text-center">
          Sin errores de postura registrados — ¡buen trabajo!
        </p>
      ) : (
        <div className="relative" style={{ overflowX: "auto" }}>
          <svg
            viewBox={`0 0 ${VB2_WIDTH} ${VB2_HEIGHT}`}
            style={{ width: "100%", height: "auto", display: "block", minWidth: 260 }}
            role="img"
            aria-label="Errores de forma por tipo: cadera y espalda"
          >
            {categorias.map((c, i) => {
              const y = ROW_TOP_PADDING + i * (BAR_HEIGHT + BAR_GAP);
              const barWidth = (c.value / barMax) * plotW;
              const isHovered = hoveredKey === c.key;
              return (
                <g
                  key={c.key}
                  tabIndex={0}
                  role="img"
                  aria-label={`${c.label}: ${c.value} errores`}
                  onPointerEnter={() => setHoveredKey(c.key)}
                  onPointerLeave={() => setHoveredKey(null)}
                  onFocus={() => setHoveredKey(c.key)}
                  onBlur={() => setHoveredKey(null)}
                  style={{ cursor: "pointer", outline: "none" }}
                >
                  <text
                    x={LABEL_WIDTH - 8}
                    y={y + BAR_HEIGHT / 2}
                    textAnchor="end"
                    dominantBaseline="middle"
                    fontSize={12}
                    fill="var(--text-secondary)"
                  >
                    {c.label}
                  </text>
                  <rect
                    x={LABEL_WIDTH}
                    y={y}
                    width={Math.max(barWidth, c.value > 0 ? 4 : 0)}
                    height={BAR_HEIGHT}
                    rx={4}
                    ry={4}
                    fill={c.color}
                    fillOpacity={isHovered ? 0.85 : 1}
                  />
                  <text
                    x={LABEL_WIDTH + Math.max(barWidth, c.value > 0 ? 4 : 0) + VALUE_GAP}
                    y={y + BAR_HEIGHT / 2}
                    dominantBaseline="middle"
                    fontSize={12}
                    fontWeight={600}
                    fill="var(--text-primary)"
                  >
                    {c.value}
                  </text>
                  {isHovered && (
                    <rect
                      x={LABEL_WIDTH}
                      y={y}
                      width={Math.max(barWidth, c.value > 0 ? 4 : 0)}
                      height={BAR_HEIGHT}
                      rx={4}
                      ry={4}
                      fill="none"
                      stroke="var(--surface-1)"
                      strokeWidth={1.5}
                    />
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      )}
    </div>
  );
}

// --- Componente contenedor ---------------------------------------------

export default function GraficosHistorial({ repsByDay, errorsByType }: GraficosHistorialProps) {
  return (
    <div className="viz-historial grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
      <style>{`
        .viz-historial {
          --surface-1: #fcfcfb;
          --text-primary: #0b0b0b;
          --text-secondary: #52514e;
          --text-muted: #898781;
          --gridline: #e1e0d9;
          --baseline: #c3c2b7;
          --series-1: #2a78d6; /* azul: reps por día, "Cadera" */
          --series-2: #eb6834; /* naranja: "Espalda" */
          --border: rgba(11, 11, 11, 0.1);
        }
        @media (prefers-color-scheme: dark) {
          .viz-historial {
            --surface-1: #1a1a19;
            --text-primary: #ffffff;
            --text-secondary: #c3c2b7;
            --text-muted: #898781;
            --gridline: #2c2c2a;
            --baseline: #383835;
            --series-1: #3987e5;
            --series-2: #d95926;
            --border: rgba(255, 255, 255, 0.1);
          }
        }
      `}</style>

      <div className="rounded-lg bg-gray-100 dark:bg-white/5 p-4">
        <h2 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
          Repeticiones por día (últimos 30 días)
        </h2>
        <GraficoRepsPorDia repsByDay={repsByDay} />
      </div>

      <div className="rounded-lg bg-gray-100 dark:bg-white/5 p-4">
        <h2 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
          Errores de forma por tipo
        </h2>
        <GraficoErroresPorTipo errorsByType={errorsByType} />
      </div>
    </div>
  );
}
