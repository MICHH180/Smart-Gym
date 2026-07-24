from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Import relativo: backend/ es un namespace package (sin __init__.py) importado
# como "backend.app" desde la raíz del proyecto (ver "uvicorn backend.app:app").
from .workout_session import WorkoutSession
from .db import DEV_USER_EMAIL, db
from .historial import router as historial_router

# Alias explícito: prisma.models.WorkoutSession es el MODELO DE BASE DE DATOS
# (una fila de sesión persistida). No confundir con .workout_session.WorkoutSession,
# que es el wrapper de UNA sesión de análisis CV en vivo (PoseDetector + SquatAnalyzer).
# Son dos conceptos distintos que comparten nombre por coincidencia de dominio.
from prisma.models import WorkoutSession as SesionDB

app = FastAPI()
app.include_router(historial_router)


@app.on_event("startup")
async def startup() -> None:
    await db.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    await db.disconnect()


@app.get("/health")
def health():
    return {"status": "ok"}


async def registrar_evento_db(sesion_db: SesionDB, resultado: dict) -> None:
    """Persiste (si corresponde) el evento de voz de UN frame como RepEvent
    o FormErrorEvent.

    La mayoría de los frames no disparan ningún evento (30fps de stream) y
    no deben generar escritura en la base de datos: solo se persiste en
    reps completadas o errores de forma detectados.
    """
    evento_voz = resultado.get("evento_voz") or ""

    if evento_voz.startswith("Bien "):
        await db.repevent.create(
            data={
                "sessionId": sesion_db.id,
                "repNumber": resultado["contador"],
            }
        )
    elif evento_voz == "Cadera":
        await db.formerrorevent.create(
            data={"sessionId": sesion_db.id, "tipo": "cadera"}
        )
    elif evento_voz == "Endereza":
        await db.formerrorevent.create(
            data={"sessionId": sesion_db.id, "tipo": "espalda"}
        )


@app.websocket("/ws/session")
async def ws_session(websocket: WebSocket):
    await websocket.accept()
    session = WorkoutSession()  # estado propio de esta conexión, no compartido

    usuario_dev = await db.user.upsert(
        where={"email": DEV_USER_EMAIL},
        data={
            "create": {"email": DEV_USER_EMAIL},
            "update": {},
        },
    )
    sesion_db = await db.workoutsession.create(
        data={"userId": usuario_dev.id, "exercise": "squat"}
    )

    try:
        while True:
            frame_bytes = await websocket.receive_bytes()
            resultado = session.procesar_frame_bytes(frame_bytes)
            await registrar_evento_db(sesion_db, resultado)
            await websocket.send_json(resultado)
    except WebSocketDisconnect:
        await db.workoutsession.update(
            where={"id": sesion_db.id},
            data={"endedAt": datetime.now(timezone.utc)},
        )
