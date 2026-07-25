import asyncio
import threading
import time
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from auth import EmailYaRegistradoError, GestorUsuarios, crear_token, verificar_token
from curl_analyzer import CurlAnalyzer
from database import RegistroEntrenamiento
from glute_bridge_analyzer import GluteBridgeAnalyzer
from lateral_analyzer import LateralRaiseAnalyzer
from lunge_analyzer import LungeAnalyzer
from pose_detector import PoseDetector
from push_analyzer import PushUpAnalyzer
from speaker import Speaker
from squat_analyzer import SquatAnalyzer


# El "id" de cada ejercicio acá es el mismo que usa el frontend en sus rutas
# (/ejercicios/<id>, ?ejercicio=<id>) — así no hace falta traducir entre un
# nombre de exhibición y una clave interna en ningún lado.
# `model_complexity` es el mismo parámetro que recibe PoseDetector: los
# desplantes necesitan 1 porque las piernas se cruzan más en la imagen que
# en el resto de los ejercicios. Cada sesión crea su PROPIO PoseDetector
# (ver generar_frames) — NO se comparte una instancia entre sesiones, porque
# el grafo de MediaPipe que hay adentro no está pensado para recibir frames
# de dos streams a la vez (dos sesiones "solapadas" corrompiéndolo es
# justamente el bug que causaba "Packet type mismatch... empty Packet").
EJERCICIOS = {
    "sentadillas": {
        "analyzer_cls": SquatAnalyzer,
        "model_complexity": 0,
        "voz_bienvenida": "Prepárate. Baja para iniciar",
    },
    "desplantes": {
        "analyzer_cls": LungeAnalyzer,
        "model_complexity": 1,
        "voz_bienvenida": "Prepárate. Da un paso para iniciar",
    },
    "curl-biceps": {
        "analyzer_cls": CurlAnalyzer,
        "model_complexity": 0,
        "voz_bienvenida": "Prepárate, de frente a la cámara",
    },
    "elevaciones-laterales": {
        "analyzer_cls": LateralRaiseAnalyzer,
        "model_complexity": 0,
        "voz_bienvenida": "Prepárate, de frente a la cámara",
    },
    "flexiones": {
        "analyzer_cls": PushUpAnalyzer,
        "model_complexity": 0,
        "voz_bienvenida": "Prepárate en posición de plancha",
    },
    "puente-gluteos": {
        "analyzer_cls": GluteBridgeAnalyzer,
        # El prototipo usa el modelo completo: acostado de perfil, el modelo
        # ligero pierde con mayor frecuencia pies y tobillos.
        "model_complexity": 1,
        "voz_bienvenida": "Prepárate, acuéstate de perfil a la cámara",
    },
}


class CamaraEnVivo:
    """Lee la cámara en un hilo aparte y se queda solo con el frame más reciente.

    El problema del retraso de varios segundos casi siempre es esto: si procesar
    un frame (MediaPipe + dibujo) tarda más que el intervalo entre frames de la
    cámara, OpenCV va acumulando un backlog y terminas viendo/reaccionando a
    frames de hace varios segundos. Este hilo descarta los frames viejos y
    siempre entrega el más nuevo disponible.
    """

    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        # En algunos backends (V4L2/Linux) esto ayuda a reducir el buffer interno
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.lock = threading.Lock()
        self.frame = None
        self.ret = False
        self.running = True
        self.thread = threading.Thread(target=self._actualizar, daemon=True)
        self.thread.start()

    def _actualizar(self):
        while self.running:
            ret, frame = self.cap.read()
            with self.lock:
                self.ret = ret
                self.frame = frame

    def read(self):
        with self.lock:
            if self.frame is None:
                return False, None
            return self.ret, self.frame.copy()

    def isOpened(self):
        return self.cap.isOpened()

    def release(self):
        self.running = False
        self.thread.join(timeout=1)
        self.cap.release()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Recursos que dependen del hardware (cámara) o son costosos de crear
    # (modelo de MediaPipe) viven una sola vez por el tiempo de vida del server.
    app.state.speaker = Speaker()
    app.state.registro = RegistroEntrenamiento()
    app.state.usuarios = GestorUsuarios()
    app.state.camara = CamaraEnVivo(0)
    # asyncio solo mantiene referencias débiles a las tasks de create_task():
    # sin guardarlas acá, el watcher de desconexión puede desaparecer en
    # medio de su ejecución antes de detectar que el cliente se fue.
    app.state.tareas_fondo = set()
    # Solo puede haber una sesión "activa" de verdad a la vez (una sola
    # cámara física). Cuando /video_feed arranca una sesión nueva, pisa este
    # valor — así, si la sesión anterior seguía viva de fondo (el navegador
    # no cierra la conexión del <img> anterior de inmediato), su generador
    # se corta solo en la próxima vuelta del loop en vez de seguir
    # procesando frames en paralelo con la nueva.
    app.state.sesion_activa_id = None
    yield
    app.state.camara.release()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SESSION_COOKIE = "smart_gym_session"


def _setear_cookie_sesion(response: Response, usuario: dict):
    response.set_cookie(
        key=SESSION_COOKIE,
        value=crear_token(usuario),
        httponly=True,
        samesite="lax",
        secure=False,  # dev sobre http; en producción con HTTPS esto debe ser True
        max_age=7 * 24 * 60 * 60,
        path="/",
    )


class RegistroRequest(BaseModel):
    nombre: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/registro", status_code=201)
def registrar_usuario(payload: RegistroRequest, response: Response):
    try:
        usuario = app.state.usuarios.crear_usuario(payload.nombre, payload.email, payload.password)
    except EmailYaRegistradoError:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese email")

    _setear_cookie_sesion(response, usuario)
    return usuario


@app.post("/api/auth/login")
def iniciar_sesion_usuario(payload: LoginRequest, response: Response):
    usuario = app.state.usuarios.verificar_credenciales(payload.email, payload.password)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    _setear_cookie_sesion(response, usuario)
    return usuario


def _usuario_desde_request(request: Request):
    """Valida la cookie de sesión y devuelve {id, nombre, email}, o None si no hay sesión."""
    token = request.cookies.get(SESSION_COOKIE)
    payload = verificar_token(token) if token else None
    if payload is None:
        return None
    return {"id": payload["sub"], "nombre": payload["nombre"], "email": payload["email"]}


def _requerir_usuario(request: Request):
    usuario = _usuario_desde_request(request)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Necesitas iniciar sesión")
    return usuario


@app.get("/api/auth/me")
def usuario_actual(request: Request):
    usuario = _usuario_desde_request(request)
    if usuario is None:
        raise HTTPException(status_code=401, detail="No hay sesión activa")
    racha = app.state.registro.obtener_racha_dias(usuario["id"])
    return {**usuario, "racha": racha}


@app.post("/api/auth/logout")
def cerrar_sesion_usuario(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@app.get("/api/dashboard")
def dashboard(request: Request):
    usuario = _requerir_usuario(request)
    registro = app.state.registro
    return {
        "stats": registro.obtener_resumen_usuario(usuario["id"]),
        "sessions": registro.obtener_sesiones_usuario(usuario["id"]),
        "streak": registro.obtener_racha_dias(usuario["id"]),
        "achievements": registro.obtener_logros(usuario["id"]),
    }


def generar_frames(sesion_id, ejercicio):
    """Reemplaza el loop de cv2.imshow: en vez de dibujar en una ventana nativa,
    codifica cada frame como JPEG y lo entrega como una parte de un stream
    multipart MJPEG. FastAPI/Starlette corren este generador sync en un
    threadpool, así que los bloqueos de cv2/mediapipe no frenan el event loop.

    Genérico para cualquier ejercicio de EJERCICIOS: el analizador y el
    detector (según model_complexity) se resuelven según `ejercicio`. Tanto
    el analizador como el PoseDetector se crean nuevos por cada conexión:
    cada vez que el frontend arranca una sesión (GET /video_feed), el
    contador de reps empieza de cero, y el grafo de MediaPipe es propio de
    esta sesión (no compartido con ninguna otra, ver el comentario en
    EJERCICIOS sobre por qué compartirlo corrompía el grafo).

    Importante: `sesion_id` ya viene creada desde el endpoint (no se crea acá).
    El cierre de la sesión (fecha_fin) NO se puede confiar solo al `finally`
    de este generador: cuando el cliente corta la conexión (ej. navega a otra
    página), Starlette deja de llamarle next() a este generador para siempre
    -el error de socket ocurre en su capa, no en la nuestra- así que el
    `finally` puede tardar en correr o no correr nunca, dependiendo de cuándo
    el garbage collector junte el objeto. El cierre confiable lo hace el
    watcher `vigilar_desconexion` en el endpoint /video_feed, en paralelo.
    Este `finally` de acá queda como respaldo para cuando el generador sí
    llega a terminar solo (ej. se cierra la cámara, o lo reemplaza una
    sesión más nueva vía sesion_activa_id).
    """
    config = EJERCICIOS[ejercicio]
    camara = app.state.camara
    detector = PoseDetector(model_complexity=config["model_complexity"])
    speaker = app.state.speaker
    registro = app.state.registro
    analyzer = config["analyzer_cls"]()

    speaker.speak_unique(config["voz_bienvenida"])

    try:
        while camara.isOpened() and app.state.sesion_activa_id == sesion_id:
            success, frame = camara.read()
            if not success:
                # El hilo de la cámara puede tardar un instante en entregar el primer frame
                time.sleep(0.01)
                continue

            frame = cv2.flip(frame, 1)
            image, results = detector.procesar_frame(frame)

            # Analizar postura y obtener métricas a través del módulo escalable
            # de este ejercicio. Todos los analizadores (sentadillas, desplantes,
            # curl, elevaciones laterales) devuelven la misma forma de tupla.
            angulo, contador, alerta, color_alerta, punto_referencia, evento_voz, info_repeticion, precision_actual = analyzer.analizar(results)

            # Cada vez que se cuenta una repetición nueva, se guarda en la base de datos
            # (incluyendo la precisión: % del movimiento que estuvo en buena forma).
            # Desplantes informa la pierna en `info_repeticion`. Sentadillas
            # conserva su fallback histórico con `lado_bloqueado`; en ejercicios
            # bilaterales (como puente de glúteos), ese lado solo sirve para medir
            # la postura y no debe persistirse como una pierna entrenada.
            if info_repeticion:
                pierna_fallback = (
                    getattr(analyzer, "lado_bloqueado", None)
                    if ejercicio == "sentadillas"
                    else None
                )
                registro.registrar_repeticion(
                    sesion_id,
                    numero_rep=info_repeticion["numero_rep"],
                    pierna=info_repeticion.get("pierna", pierna_fallback),
                    angulo_minimo=info_repeticion["angulo_minimo"],
                    correcta=info_repeticion["correcta"],
                    errores=info_repeticion["errores"],
                    precision=info_repeticion["precision"],
                )

            if evento_voz:
                print(time.time(), "MAIN ->", evento_voz)
                speaker.speak_unique(evento_voz)

            if results.pose_landmarks:
                # Mostrar el ángulo numérico en pantalla, junto a la
                # articulación de referencia del ejercicio (rodilla o codo)
                cv2.putText(image, str(angulo),
                               tuple(np.multiply(punto_referencia, [640, 480]).astype(int)),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

            # Dibujar panel visual de estadísticas en pantalla
            cv2.rectangle(image, (0, 0), (640, 73), (245, 117, 16), -1)

            # Texto de Repeticiones
            cv2.putText(image, 'REPS', (15, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(contador), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)

            # Texto de Alerta / Estado
            cv2.putText(image, 'ESTADO', (130, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, alerta, (130, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_alerta, 2, cv2.LINE_AA)

            # Precisión en vivo (% del movimiento en buena forma en la bajada actual)
            color_precision = (0, 255, 0) if precision_actual >= 90 else (0, 255, 255) if precision_actual >= 70 else (0, 0, 255)
            cv2.putText(image, 'PRECISION', (420, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, f"{precision_actual}%", (420, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color_precision, 2, cv2.LINE_AA)

            # Dibujar malla de esqueleto encima
            detector.dibujar_esqueleto(image, results)

            ok, buffer = cv2.imencode(".jpg", image)
            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )
    finally:
        registro.cerrar_sesion(sesion_id)


async def _vigilar_desconexion(request: Request, sesion_id: int):
    """Respaldo best-effort para cuando el usuario cierra la pestaña o el
    navegador entero sin pasar por el botón "Detener y finalizar" (ese caso
    SÍ tiene un endpoint explícito, /api/sesiones/{id}/finalizar — ver ahí
    el motivo de por qué es la vía principal). Este watcher sondea si el
    socket se cerró; en la práctica los navegadores no cierran la conexión
    TCP de un <img> desmontado de inmediato (la dejan viva por keep-alive
    un rato), así que esto puede tardar o directamente no dispararse antes
    de que el usuario ya se haya ido — por eso es solo un respaldo, no la
    forma principal de cerrar la sesión."""
    registro = app.state.registro
    try:
        while True:
            if await request.is_disconnected():
                registro.cerrar_sesion(sesion_id)
                break
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass


class IniciarSesionRequest(BaseModel):
    ejercicio: str


@app.post("/api/sesiones/iniciar", status_code=201)
def iniciar_sesion_entrenamiento(payload: IniciarSesionRequest, request: Request):
    usuario = _requerir_usuario(request)
    if payload.ejercicio not in EJERCICIOS:
        raise HTTPException(status_code=400, detail="Ejercicio no reconocido")
    sesion_id = app.state.registro.iniciar_sesion(payload.ejercicio, usuario_id=usuario["id"])
    return {"sesionId": sesion_id}


@app.post("/api/sesiones/{sesion_id}/finalizar")
def finalizar_sesion_entrenamiento(sesion_id: int, request: Request):
    usuario = _requerir_usuario(request)
    sesion = app.state.registro.obtener_sesion(sesion_id)
    if sesion is None or sesion["usuario_id"] != usuario["id"]:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    # Cerrar la fila en la base de datos no detiene por sí solo el generador
    # MJPEG. Al limpiar el ID activo, su condición del while deja de cumplirse
    # en la siguiente vuelta y MediaPipe deja de procesar/registrar repeticiones.
    if app.state.sesion_activa_id == sesion_id:
        app.state.sesion_activa_id = None
    app.state.registro.cerrar_sesion(sesion_id)
    return {"ok": True}


@app.get("/video_feed")
async def video_feed(sesion_id: int, request: Request):
    usuario = _requerir_usuario(request)
    sesion = app.state.registro.obtener_sesion(sesion_id)
    if sesion is None or sesion["usuario_id"] != usuario["id"]:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if sesion["ejercicio"] not in EJERCICIOS:
        raise HTTPException(status_code=400, detail="Ejercicio no reconocido")

    # Esta sesión pasa a ser la activa. Si había otra corriendo de fondo
    # (el navegador anterior no cerró la conexión a tiempo), su generador
    # ve este cambio en la próxima vuelta del loop y se corta solo.
    app.state.sesion_activa_id = sesion_id

    tarea = asyncio.create_task(_vigilar_desconexion(request, sesion_id))
    app.state.tareas_fondo.add(tarea)
    tarea.add_done_callback(app.state.tareas_fondo.discard)

    return StreamingResponse(
        generar_frames(sesion_id, sesion["ejercicio"]),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
