from collections import deque
import numpy as np
import mediapipe as mp


class PushUpAnalyzer:
    """Analizador de Lagartijas (Push-ups) de perfil.
    Detecta automáticamente el perfil visible y valida la postura horizontal.
    """

    UMBRAL_ARRIBA = 150       # Brazos extendidos arriba
    UMBRAL_ABAJO = 95         # Flexión profunda abajo

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.estado = "ARRIBA"
        self.contador = 0

        self.historial_perfil = deque(maxlen=3)
        self.frames_abajo = 0
        self.frames_arriba = 0
        self.UMBRAL_ESTADO = 2

        # Precisión
        self.frames_totales_rep = 0
        self.precision_actual = 100
        self.angulo_minimo_rep = 180

    def analizar(self, results):
        alerta = "Colócate de perfil"
        color_alerta = (255, 255, 255)
        evento_voz = None
        info_repeticion = None

        try:
            landmarks = results.pose_landmarks.landmark
            lm = self.mp_pose.PoseLandmark

            # Verificamos visibilidad de ambos lados para elegir el que esté más visible (perfil)
            vis_izq = (landmarks[lm.LEFT_SHOULDER.value].visibility + 
                       landmarks[lm.LEFT_ELBOW.value].visibility + 
                       landmarks[lm.LEFT_WRIST.value].visibility) / 3
                       
            vis_der = (landmarks[lm.RIGHT_SHOULDER.value].visibility + 
                       landmarks[lm.RIGHT_ELBOW.value].visibility + 
                       landmarks[lm.RIGHT_WRIST.value].visibility) / 3

            VISIBILIDAD_MINIMA = 0.6
            if vis_izq < VISIBILIDAD_MINIMA and vis_der < VISIBILIDAD_MINIMA:
                raise ValueError("Perfil no detectado con claridad")

            # Seleccionamos el lado que esté mejor orientado hacia la cámara
            if vis_izq > vis_der:
                hombro = [landmarks[lm.LEFT_SHOULDER.value].x, landmarks[lm.LEFT_SHOULDER.value].y]
                codo = [landmarks[lm.LEFT_ELBOW.value].x, landmarks[lm.LEFT_ELBOW.value].y]
                muneca = [landmarks[lm.LEFT_WRIST.value].x, landmarks[lm.LEFT_WRIST.value].y]
                cadera = [landmarks[lm.LEFT_HIP.value].x, landmarks[lm.LEFT_HIP.value].y]
            else:
                hombro = [landmarks[lm.RIGHT_SHOULDER.value].x, landmarks[lm.RIGHT_SHOULDER.value].y]
                codo = [landmarks[lm.RIGHT_ELBOW.value].x, landmarks[lm.RIGHT_ELBOW.value].y]
                muneca = [landmarks[lm.RIGHT_WRIST.value].x, landmarks[lm.RIGHT_WRIST.value].y]
                cadera = [landmarks[lm.RIGHT_HIP.value].x, landmarks[lm.RIGHT_HIP.value].y]

            # --- ANTIFALSOS POSITIVOS: Validación de Plancha / Posición Horizontal ---
            # En una lagartija de perfil, la diferencia de altura (Y) entre el hombro 
            # y la cadera debe ser pequeña (están a niveles similares horizontalmente).
            # Si estás parado, la cadera está muy abajo del hombro (diferencia Y grande).
            diferencia_altura_cuerpo = abs(hombro[1] - cadera[1])
            
            # Si la diferencia vertical es mayor a 0.35 (estás muy inclinado o parado), se bloquea
            if diferencia_altura_cuerpo > 0.35:
                return (0, self.contador, "Colócate en posición horizontal (plancha)", 
                        (0, 0, 255), codo, None, None, self.precision_actual)

            # Cálculo del ángulo del codo para el perfil seleccionado
            angulo_actual = self.calcular_angulo_3puntos(hombro, codo, muneca)
            self.historial_perfil.append(angulo_actual)
            angulo_suavizado = sum(self.historial_perfil) / len(self.historial_perfil)

            if angulo_suavizado < self.angulo_minimo_rep:
                self.angulo_minimo_rep = angulo_suavizado

            # Máquina de estados
            if angulo_suavizado > self.UMBRAL_ARRIBA:
                self.frames_arriba += 1
                self.frames_abajo = 0

                if self.frames_arriba >= self.UMBRAL_ESTADO:
                    if self.estado == "ABAJO":
                        self.contador += 1
                        alerta = f"¡Bien hecha! ({self.contador})"
                        evento_voz = f"Bien {self.contador}"
                        color_alerta = (0, 255, 0)

                        info_repeticion = {
                            "numero_rep": self.contador,
                            "angulo_minimo": int(self.angulo_minimo_rep),
                            "correcta": True,
                            "errores": [],
                            "precision": 100,
                        }
                        self.angulo_minimo_rep = 180
                    else:
                        alerta = "Arriba - Baja flexionando"
                        color_alerta = (0, 255, 0)

                    self.estado = "ARRIBA"

            elif angulo_suavizado < self.UMBRAL_ABAJO:
                self.frames_abajo += 1
                self.frames_arriba = 0

                if self.frames_abajo >= self.UMBRAL_ESTADO:
                    self.estado = "ABAJO"
                    alerta = "¡Sube!"
                    color_alerta = (0, 0, 255)
            else:
                if self.estado == "ARRIBA":
                    alerta = "Bajando..."
                    color_alerta = (255, 255, 0)
                else:
                    alerta = "Subiendo..."
                    color_alerta = (0, 255, 0)

            return (int(angulo_suavizado), self.contador, alerta, color_alerta,
                    codo, evento_voz, info_repeticion, self.precision_actual)

        except Exception:
            self.historial_perfil.clear()
            return 0, self.contador, "Párate completamente de perfil", (0, 0, 255), [0, 0], None, None, self.precision_actual

    def calcular_angulo_3puntos(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360.0 - angle
        return angle
