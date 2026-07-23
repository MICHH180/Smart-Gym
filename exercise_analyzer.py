from abc import ABC, abstractmethod
from collections import deque
import numpy as np
import mediapipe as mp

from rep_counter import RepCounter


class ExerciseAnalyzer(ABC):
    """Base común para el análisis de ejercicios repetitivos: elige el lado
    del cuerpo más visible, suaviza el ángulo que gobierna la máquina de
    estados de repeticiones y orquesta el puntaje de forma. Cada ejercicio
    concreto define qué puntos usa, cómo calcula su ángulo principal y sus
    propias validaciones de técnica."""

    TAMANO_VENTANA_SUAVIZADO = 5
    LIMITE_SALTO_ANGULO = 30
    UMBRAL_CAMBIO_LADO = 10  # frames de histéresis antes de cambiar de lado visible

    def __init__(self):
        self.mp_pose = mp.solutions.pose

        self.historial_angulo = deque(maxlen=self.TAMANO_VENTANA_SUAVIZADO)
        self.rep_counter = RepCounter()
        self.form_scorer = None
        self.ultimo_form_score = None

        self.lado_actual = "LEFT"
        self.frames_lado_alterno = 0

    @abstractmethod
    def puntos_visibilidad(self):
        """Nombres base de landmarks (sin prefijo LEFT_/RIGHT_) usados para puntuar visibilidad de cada lado."""

    @abstractmethod
    def extraer_puntos(self, landmarks, lado):
        """Devuelve un dict de puntos [x, y] con los nombres que necesite este ejercicio."""

    @abstractmethod
    def angulo_principal(self, puntos):
        """Ángulo crudo (antes de suavizar) que alimenta la máquina de estados de RepCounter."""

    @abstractmethod
    def punto_referencia(self, puntos):
        """Punto [x, y] donde el llamador dibuja la etiqueta del ángulo en pantalla."""

    @abstractmethod
    def validar_forma(self, puntos, angulo_suavizado, estado):
        """Validaciones de técnica propias del ejercicio.

        Devuelve (alerta_override, color_override, evento_voz, desviacion_forma, hubo_falla_secundaria).
        """

    @abstractmethod
    def crear_form_scorer(self):
        """Construye el FormScorer configurado con los umbrales de este ejercicio."""

    @abstractmethod
    def resetear_validacion(self):
        """Limpia el estado del validador de forma propio del ejercicio."""

    def _visibilidad_lado(self, landmarks, lado):
        puntos = [
            self.mp_pose.PoseLandmark[f"{lado}_{nombre}"].value
            for nombre in self.puntos_visibilidad()
        ]
        return sum(landmarks[p].visibility for p in puntos) / len(puntos)

    def _elegir_lado(self, landmarks):
        lado_preferido = (
            "LEFT"
            if self._visibilidad_lado(landmarks, "LEFT") >= self._visibilidad_lado(landmarks, "RIGHT")
            else "RIGHT"
        )

        if lado_preferido == self.lado_actual:
            self.frames_lado_alterno = 0
            return

        self.frames_lado_alterno += 1
        if self.frames_lado_alterno >= self.UMBRAL_CAMBIO_LADO:
            self.lado_actual = lado_preferido
            self.frames_lado_alterno = 0
            # Al cambiar de lado las coordenadas "saltan", así que hay que limpiar
            # el estado que compara contra el frame anterior.
            self.resetear_validacion()
            self.historial_angulo.clear()

    def analizar(self, results):
        alerta = "Colócate de perfil"
        color_alerta = (255, 255, 255)
        evento_voz = None

        try:
            landmarks = results.pose_landmarks.landmark
            self._elegir_lado(landmarks)

            puntos = self.extraer_puntos(landmarks, self.lado_actual)

            # Cálculo del ángulo crudo y filtro anti-teletransportes de MediaPipe antes de pasarlo al historial
            angulo_crudo = self.angulo_principal(puntos)

            if self.historial_angulo:
                ultimo = self.historial_angulo[-1]
                diferencia = angulo_crudo - ultimo

                if abs(diferencia) > self.LIMITE_SALTO_ANGULO:
                    angulo_crudo = ultimo + np.sign(diferencia) * self.LIMITE_SALTO_ANGULO

            self.historial_angulo.append(angulo_crudo)
            angulo_suavizado = sum(self.historial_angulo) / len(self.historial_angulo)

            estado, contador, alerta_rc, color_rc, se_completo_repeticion, nueva_bajada = self.rep_counter.actualizar(angulo_suavizado)

            if self.form_scorer is None:
                self.form_scorer = self.crear_form_scorer()

            if nueva_bajada:
                self.form_scorer.iniciar_repeticion()

            if alerta_rc is not None:
                alerta = alerta_rc
                color_alerta = color_rc
            if se_completo_repeticion:
                evento_voz = f"Bien {contador}"

            alerta_ov, color_ov, evento_voz_ov, desviacion_forma, hubo_falla_secundaria = self.validar_forma(
                puntos, angulo_suavizado, estado
            )
            if alerta_ov is not None:
                alerta = alerta_ov
                color_alerta = color_ov
            if evento_voz_ov is not None:
                evento_voz = evento_voz_ov

            self.form_scorer.actualizar(desviacion_forma, estado, hubo_falla_secundaria)
            if se_completo_repeticion:
                self.ultimo_form_score = self.form_scorer.finalizar_repeticion()

            return (
                int(angulo_suavizado),
                contador,
                alerta,
                color_alerta,
                self.punto_referencia(puntos),
                evento_voz,
                self.ultimo_form_score,
            )

        except Exception:
            self.resetear_validacion()
            self.historial_angulo.clear()  # Limpieza del historial si se pierde el esqueleto de vista
            return 0, self.rep_counter.contador, "Alineate con la camara", (0, 0, 255), [0, 0], None, self.ultimo_form_score
