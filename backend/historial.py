"""Endpoints REST de solo lectura para el futuro dashboard histórico
(frontend Next.js, fuera de este alcance).

Todos los datos se scopean al mismo usuario placeholder de desarrollo que
usa el flujo WebSocket en app.py (ver DEV_USER_EMAIL en backend/db.py) ya
que todavía no hay autenticación real.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .db import DEV_USER_EMAIL, db

router = APIRouter(prefix="/api")


# --- Modelos de respuesta (Pydantic) -----------------------------------


class SesionResumen(BaseModel):
    id: str
    exercise: str
    startedAt: datetime
    endedAt: Optional[datetime] = None
    repCount: int
    formErrorCount: int


class RepEventOut(BaseModel):
    repNumber: int
    timestamp: datetime


class FormErrorEventOut(BaseModel):
    tipo: str
    timestamp: datetime


class SesionDetalle(BaseModel):
    id: str
    exercise: str
    startedAt: datetime
    endedAt: Optional[datetime] = None
    reps: List[RepEventOut]
    formErrors: List[FormErrorEventOut]


class RepsPorDia(BaseModel):
    date: str
    count: int


class EstadisticasGenerales(BaseModel):
    totalSessions: int
    totalReps: int
    errorsByType: Dict[str, int]
    repsByDay: List[RepsPorDia]


# --- Helper interno -----------------------------------------------------


async def _get_dev_user_id() -> Optional[str]:
    """Busca el id del usuario placeholder de desarrollo.

    Devuelve None si todavía no se creó (p. ej. nunca se abrió una sesión
    WebSocket) para que los endpoints de arriba puedan responder con datos
    vacíos en lugar de fallar.
    """
    usuario = await db.user.find_unique(where={"email": DEV_USER_EMAIL})
    return usuario.id if usuario is not None else None


# --- Endpoints ------------------------------------------------------------


@router.get("/sessions", response_model=List[SesionResumen])
async def listar_sesiones(limit: int = 50) -> List[SesionResumen]:
    """Lista las sesiones del usuario dev, más recientes primero."""
    user_id = await _get_dev_user_id()
    if user_id is None:
        return []

    sesiones = await db.workoutsession.find_many(
        where={"userId": user_id},
        order={"startedAt": "desc"},
        take=limit,
        include={"reps": True, "formErrors": True},
    )

    return [
        SesionResumen(
            id=sesion.id,
            exercise=sesion.exercise,
            startedAt=sesion.startedAt,
            endedAt=sesion.endedAt,
            repCount=len(sesion.reps or []),
            formErrorCount=len(sesion.formErrors or []),
        )
        for sesion in sesiones
    ]


@router.get("/sessions/{session_id}", response_model=SesionDetalle)
async def obtener_sesion(session_id: str) -> SesionDetalle:
    """Detalle completo de una sesión: reps y errores de forma ordenados
    cronológicamente."""
    sesion = await db.workoutsession.find_unique(
        where={"id": session_id},
        include={
            "reps": {"order_by": {"timestamp": "asc"}},
            "formErrors": {"order_by": {"timestamp": "asc"}},
        },
    )
    if sesion is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return SesionDetalle(
        id=sesion.id,
        exercise=sesion.exercise,
        startedAt=sesion.startedAt,
        endedAt=sesion.endedAt,
        reps=[
            RepEventOut(repNumber=rep.repNumber, timestamp=rep.timestamp)
            for rep in (sesion.reps or [])
        ],
        formErrors=[
            FormErrorEventOut(tipo=err.tipo, timestamp=err.timestamp)
            for err in (sesion.formErrors or [])
        ],
    )


@router.get("/stats", response_model=EstadisticasGenerales)
async def obtener_estadisticas() -> EstadisticasGenerales:
    """Estadísticas agregadas del usuario dev: totales, errores por tipo y
    reps por día en los últimos 30 días."""
    user_id = await _get_dev_user_id()
    if user_id is None:
        return EstadisticasGenerales(
            totalSessions=0, totalReps=0, errorsByType={}, repsByDay=[]
        )

    total_sessions = await db.workoutsession.count(where={"userId": user_id})
    total_reps = await db.repevent.count(
        where={"session": {"is": {"userId": user_id}}}
    )

    form_errors = await db.formerrorevent.find_many(
        where={"session": {"is": {"userId": user_id}}},
    )
    errors_by_type: Dict[str, int] = {}
    for error_evt in form_errors:
        errors_by_type[error_evt.tipo] = errors_by_type.get(error_evt.tipo, 0) + 1

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    reps_recientes = await db.repevent.find_many(
        where={
            "session": {"is": {"userId": user_id}},
            "timestamp": {"gte": cutoff},
        },
        order={"timestamp": "asc"},
    )
    conteo_por_dia: Dict[str, int] = {}
    for rep in reps_recientes:
        clave_dia = rep.timestamp.date().isoformat()
        conteo_por_dia[clave_dia] = conteo_por_dia.get(clave_dia, 0) + 1
    reps_by_day = [
        RepsPorDia(date=dia, count=cantidad)
        for dia, cantidad in sorted(conteo_por_dia.items())
    ]

    return EstadisticasGenerales(
        totalSessions=total_sessions,
        totalReps=total_reps,
        errorsByType=errors_by_type,
        repsByDay=reps_by_day,
    )
