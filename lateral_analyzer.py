# from collections import deque
# import numpy as np
# import mediapipe as mp
 
 
# class LateralRaiseAnalyzer:
#     """Analizador de Elevaciones Laterales (ambos brazos a la vez, de frente).
 
#     Ángulo medido: cadera-hombro-codo (qué tan separado está el brazo del
#     torso). Brazos a los lados ≈ 0-20°, elevados a la altura del hombro ≈ 80-100°.
 
#     Errores de forma que vigila:
#       - "Encogimiento de hombros" (usar el trapecio para ayudar a levantar
#         el peso en vez del deltoides): el hombro sube hacia la oreja.
#       - "Balanceo del torso": inclinar el cuerpo hacia un lado para darle
#         impulso al peso en vez de levantarlo solo con el brazo.
#     """
 
#     UMBRAL_ABAJO = 25        # brazos pegados al cuerpo = reposo
#     UMBRAL_ARRIBA = 70       # brazos a la altura del hombro = arriba
#     UMBRAL_REPOSO_BASELINE = 15  # más estricto: solo aquí se congela la línea base
#     UMBRAL_DRIFT_HOMBRO = 0.035  # cuánto puede "subir" el hombro antes de marcar encogimiento
#     UMBRAL_INCLINACION_TORSO = 20  # grados de inclinación del torso considerados error
 
#     def __init__(self):
#         self.mp_pose = mp.solutions.pose
#         self.estado = "ABAJO"
#         self.contador = 0
 
#         self.historial_izq = deque(maxlen=3)
#         self.historial_der = deque(maxlen=3)
 
#         self.frames_abajo = 0
#         self.frames_arriba = 0
#         self.UMBRAL_ESTADO = 2
 
#         # Posición de "reposo" del hombro, se actualiza en vivo mientras el
#         # brazo está claramente abajo y se congela en cuanto arranca la subida.
#         self.hombro_reposo_izq = None
#         self.hombro_reposo_der = None
 
#         self.frames_error_hombro_rep = 0
#         self.frames_error_torso_rep = 0
#         self.UMBRAL_FRAMES_ERROR = 2
#         self.hombro_reportado = False
#         self.torso_reportado = False
 
#         # ---- Precisión (0-100%) ----
#         self.frames_totales_rep = 0
#         self.frames_error_hombro_precision = 0
#         self.frames_error_torso_precision = 0
#         self.precision_actual = 100
#         self.angulo_maximo_rep = 0
 
#     # ------------------------------------------------------------
#     def analizar(self, results):
#         alerta = "Colócate de frente"
#         color_alerta = (255, 255, 255)
#         evento_voz = None
#         info_repeticion = None
 
#         try:
#             landmarks = results.pose_landmarks.landmark
#             lm = self.mp_pose.PoseLandmark
 
#             lm_cadera_izq = landmarks[lm.LEFT_HIP.value]
#             lm_hombro_izq = landmarks[lm.LEFT_SHOULDER.value]
#             lm_codo_izq = landmarks[lm.LEFT_ELBOW.value]
#             lm_cadera_der = landmarks[lm.RIGHT_HIP.value]
#             lm_hombro_der = landmarks[lm.RIGHT_SHOULDER.value]
#             lm_codo_der = landmarks[lm.RIGHT_ELBOW.value]
 
#             VISIBILIDAD_MINIMA = 0.6
#             visibilidad_min = min(
#                 lm_cadera_izq.visibility, lm_hombro_izq.visibility, lm_codo_izq.visibility,
#                 lm_cadera_der.visibility, lm_hombro_der.visibility, lm_codo_der.visibility,
#             )
#             visibilidad_promedio_total = sum(l.visibility for l in landmarks) / len(landmarks)
 
#             if visibilidad_min < VISIBILIDAD_MINIMA or visibilidad_promedio_total < 0.5:
#                 raise ValueError("Landmarks poco confiables (probablemente no eres tú)")
 
#             separacion_hombros = abs(lm_hombro_izq.x - lm_hombro_der.x)
#             if separacion_hombros < 0.12:
#                 return (0, self.contador, "Ponte de frente a la cámara",
#                         (255, 255, 0), [0, 0], None, None, self.precision_actual)
 
#             cadera_izq = [lm_cadera_izq.x, lm_cadera_izq.y]
#             hombro_izq = [lm_hombro_izq.x, lm_hombro_izq.y]
#             codo_izq = [lm_codo_izq.x, lm_codo_izq.y]
#             cadera_der = [lm_cadera_der.x, lm_cadera_der.y]
#             hombro_der = [lm_hombro_der.x, lm_hombro_der.y]
#             codo_der = [lm_codo_der.x, lm_codo_der.y]
 
#             self.historial_izq.append(self.calcular_angulo_3puntos(cadera_izq, hombro_izq, codo_izq))
#             self.historial_der.append(self.calcular_angulo_3puntos(cadera_der, hombro_der, codo_der))
#             angulo_izq = sum(self.historial_izq) / len(self.historial_izq)
#             angulo_der = sum(self.historial_der) / len(self.historial_der)
#             angulo_prom = (angulo_izq + angulo_der) / 2
 
#             if angulo_prom > self.angulo_maximo_rep:
#                 self.angulo_maximo_rep = angulo_prom
 
#             # Torso: reusamos el mismo cálculo de inclinación que en sentadillas/desplantes
#             inclinacion_izq = self.calcular_angulo_espalda(hombro_izq, cadera_izq)
#             inclinacion_der = self.calcular_angulo_espalda(hombro_der, cadera_der)
#             inclinacion_torso = (inclinacion_izq + inclinacion_der) / 2
#             if inclinacion_torso > 90:
#                 inclinacion_torso = 180 - inclinacion_torso
 
#             # Congelamos la posición de "reposo" del hombro solo cuando el
#             # brazo está claramente abajo (umbral estricto, con margen para
#             # que el suavizado no alcance a "perseguir" un encogimiento real).
#             if angulo_prom < self.UMBRAL_REPOSO_BASELINE:
#                 self.hombro_reposo_izq = hombro_izq
#                 self.hombro_reposo_der = hombro_der
 
#             # 1. Estado y conteo
#             if angulo_prom > self.UMBRAL_ARRIBA:
#                 self.frames_arriba += 1
#                 self.frames_abajo = 0
 
#                 if self.frames_arriba >= self.UMBRAL_ESTADO:
#                     self.estado = "ARRIBA"
#                     alerta = "Buena altura"
#                     color_alerta = (0, 255, 0)
 
#             elif angulo_prom < self.UMBRAL_ABAJO:
#                 self.frames_abajo += 1
#                 self.frames_arriba = 0
 
#                 if self.frames_abajo >= self.UMBRAL_ESTADO:
#                     if self.estado == "ARRIBA":
#                         self.contador += 1
 
#                         errores_rep = []
#                         if self.frames_error_hombro_rep > 0:
#                             errores_rep.append("hombro")
#                         if self.frames_error_torso_rep > 0:
#                             errores_rep.append("torso")
 
#                         if "hombro" in errores_rep:
#                             alerta = f"Rep {self.contador}: ¡Baja los hombros!"
#                             color_alerta = (0, 0, 255)
#                             evento_voz = "Bien pero baja los hombros"
#                         elif "torso" in errores_rep:
#                             alerta = f"Rep {self.contador}: ¡No te inclines!"
#                             color_alerta = (0, 0, 255)
#                             evento_voz = "Bien pero no te inclines"
#                         else:
#                             alerta = f"¡Bien hecho! ({self.contador})"
#                             evento_voz = f"Bien {self.contador}"
#                             color_alerta = (0, 255, 0)
 
#                         info_repeticion = {
#                             "numero_rep": self.contador,
#                             "angulo_minimo": int(self.angulo_maximo_rep),
#                             "correcta": len(errores_rep) == 0,
#                             "errores": errores_rep,
#                             "precision": self.precision_actual,
#                         }
#                         self.angulo_maximo_rep = 0
#                         self.frames_totales_rep = 0
#                         self.frames_error_hombro_precision = 0
#                         self.frames_error_torso_precision = 0
#                     else:
#                         alerta = "Listo, sube"
#                         color_alerta = (0, 255, 0)
 
#                     self.estado = "ABAJO"
#                     self.frames_error_hombro_rep = 0
#                     self.frames_error_torso_rep = 0
 
#             else:
#                 self.frames_abajo = 0
#                 self.frames_arriba = 0
#                 if self.estado == "ABAJO":
#                     alerta = "Subiendo..."
#                     color_alerta = (255, 255, 0)
#                 else:
#                     alerta = "Bajando..."
#                     color_alerta = (0, 255, 255)
 
#             # 2. Validación de encogimiento de hombros
#             detecto_error_hombro_frame = False
#             if angulo_prom >= self.UMBRAL_REPOSO_BASELINE and self.hombro_reposo_izq is not None:
#                 drift_izq = np.linalg.norm(np.array(hombro_izq) - np.array(self.hombro_reposo_izq))
#                 drift_der = np.linalg.norm(np.array(hombro_der) - np.array(self.hombro_reposo_der))
#                 if drift_izq > self.UMBRAL_DRIFT_HOMBRO or drift_der > self.UMBRAL_DRIFT_HOMBRO:
#                     detecto_error_hombro_frame = True
 
#             if detecto_error_hombro_frame:
#                 self.frames_error_hombro_rep += 1
#                 if self.frames_error_hombro_rep >= self.UMBRAL_FRAMES_ERROR and not self.hombro_reportado:
#                     alerta = "¡Baja los hombros!"
#                     color_alerta = (0, 0, 255)
#                     evento_voz = "Baja los hombros"
#                     self.hombro_reportado = True
#             else:
#                 if self.frames_error_hombro_rep == 0:
#                     self.hombro_reportado = False
 
#             # 3. Validación de inclinación del torso
#             detecto_error_torso_frame = inclinacion_torso > self.UMBRAL_INCLINACION_TORSO
#             if detecto_error_torso_frame:
#                 self.frames_error_torso_rep += 1
#                 if self.frames_error_torso_rep >= self.UMBRAL_FRAMES_ERROR and not self.torso_reportado:
#                     if evento_voz is None:
#                         alerta = "¡No te inclines!"
#                         color_alerta = (0, 0, 255)
#                         evento_voz = "No te inclines"
#                     self.torso_reportado = True
#             else:
#                 if self.frames_error_torso_rep == 0:
#                     self.torso_reportado = False
 
#             # ---- Precisión en vivo ----
#             if angulo_prom >= self.UMBRAL_REPOSO_BASELINE:
#                 self.frames_totales_rep += 1
#                 if detecto_error_hombro_frame:
#                     self.frames_error_hombro_precision += 1
#                 if detecto_error_torso_frame:
#                     self.frames_error_torso_precision += 1
 
#             if self.frames_totales_rep > 0:
#                 fraccion_hombro = self.frames_error_hombro_precision / self.frames_totales_rep
#                 fraccion_torso = self.frames_error_torso_precision / self.frames_totales_rep
#                 self.precision_actual = round(100 - 30 * fraccion_hombro - 30 * fraccion_torso)
#                 self.precision_actual = max(0, min(100, self.precision_actual))
#             else:
#                 self.precision_actual = 100
 
#             return (int(angulo_prom), self.contador, alerta, color_alerta,
#                     codo_izq, evento_voz, info_repeticion, self.precision_actual)
 
#         except Exception:
#             self.historial_izq.clear()
#             self.historial_der.clear()
#             self.hombro_reposo_izq = None
#             self.hombro_reposo_der = None
#             return 0, self.contador, "Alineate con la camara", (0, 0, 255), [0, 0], None, None, self.precision_actual
 
#     # ------------------------------------------------------------
#     def calcular_angulo_3puntos(self, a, b, c):
#         a = np.array(a)
#         b = np.array(b)
#         c = np.array(c)
#         radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
#         angle = np.abs(radians * 180.0 / np.pi)
#         if angle > 180.0:
#             angle = 360.0 - angle
#         return angle
 
#     def calcular_angulo_espalda(self, hombro, cadera):
#         hombro = np.array(hombro)
#         cadera = np.array(cadera)
#         vertical = np.array([cadera[0], cadera[1] + 1.0])
#         return self.calcular_angulo_3puntos(hombro, cadera, vertical)
 
from collections import deque
import numpy as np
import mediapipe as mp
 
 
class LateralRaiseAnalyzer:
    """Analizador de Elevaciones Laterales (ambos brazos a la vez, de frente).
 
    Ángulo medido: cadera-hombro-codo (qué tan separado está el brazo del
    torso). Brazos a los lados ≈ 0-20°, elevados a la altura del hombro ≈ 80-100°.
 
    Errores de forma que vigila:
      - "Encogimiento de hombros" (usar el trapecio para ayudar a levantar
        el peso en vez del deltoides): el hombro sube hacia la oreja.
      - "Balanceo del torso": inclinar el cuerpo hacia un lado para darle
        impulso al peso en vez de levantarlo solo con el brazo.
    """
 
    UMBRAL_ABAJO = 25        # brazos pegados al cuerpo = reposo
    UMBRAL_ARRIBA = 70       # brazos a la altura del hombro = arriba
    UMBRAL_MAXIMO = 110      # brazos muy por encima del hombro = sobre-elevación
    UMBRAL_REPOSO_BASELINE = 15  # más estricto: solo aquí se congela la línea base
    UMBRAL_DRIFT_HOMBRO = 0.035  # cuánto puede "subir" el hombro antes de marcar encogimiento
    UMBRAL_INCLINACION_TORSO = 20  # grados de inclinación del torso considerados error
    UMBRAL_DESNIVEL_HOMBROS = 0.12  # diferencia de altura entre hombros (normalizada por separación)
 
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.estado = "ABAJO"
        self.contador = 0
 
        self.historial_izq = deque(maxlen=3)
        self.historial_der = deque(maxlen=3)
 
        self.frames_abajo = 0
        self.frames_arriba = 0
        self.UMBRAL_ESTADO = 2
 
        # Posición de "reposo" del hombro, se actualiza en vivo mientras el
        # brazo está claramente abajo y se congela en cuanto arranca la subida.
        self.hombro_reposo_izq = None
        self.hombro_reposo_der = None
 
        self.frames_error_hombro_rep = 0
        self.frames_error_torso_rep = 0
        self.frames_error_desnivel_rep = 0
        self.frames_error_altura_rep = 0
        self.UMBRAL_FRAMES_ERROR = 2
        self.hombro_reportado = False
        self.torso_reportado = False
        self.desnivel_reportado = False
        self.altura_reportada = False
 
        # ---- Precisión (0-100%) ----
        self.frames_totales_rep = 0
        self.frames_error_hombro_precision = 0
        self.frames_error_torso_precision = 0
        self.frames_error_desnivel_precision = 0
        self.frames_error_altura_precision = 0
        self.precision_actual = 100
        self.angulo_maximo_rep = 0
 
    # ------------------------------------------------------------
    def analizar(self, results):
        alerta = "Colócate de frente"
        color_alerta = (255, 255, 255)
        evento_voz = None
        info_repeticion = None
 
        try:
            landmarks = results.pose_landmarks.landmark
            lm = self.mp_pose.PoseLandmark
 
            lm_cadera_izq = landmarks[lm.LEFT_HIP.value]
            lm_hombro_izq = landmarks[lm.LEFT_SHOULDER.value]
            lm_codo_izq = landmarks[lm.LEFT_ELBOW.value]
            lm_cadera_der = landmarks[lm.RIGHT_HIP.value]
            lm_hombro_der = landmarks[lm.RIGHT_SHOULDER.value]
            lm_codo_der = landmarks[lm.RIGHT_ELBOW.value]
 
            VISIBILIDAD_MINIMA = 0.6
            visibilidad_min = min(
                lm_cadera_izq.visibility, lm_hombro_izq.visibility, lm_codo_izq.visibility,
                lm_cadera_der.visibility, lm_hombro_der.visibility, lm_codo_der.visibility,
            )
            visibilidad_promedio_total = sum(l.visibility for l in landmarks) / len(landmarks)
 
            if visibilidad_min < VISIBILIDAD_MINIMA or visibilidad_promedio_total < 0.5:
                raise ValueError("Landmarks poco confiables (probablemente no eres tú)")
 
            separacion_hombros = abs(lm_hombro_izq.x - lm_hombro_der.x)
            if separacion_hombros < 0.12:
                return (0, self.contador, "Ponte de frente a la cámara",
                        (255, 255, 0), [0, 0], None, None, self.precision_actual)
 
            cadera_izq = [lm_cadera_izq.x, lm_cadera_izq.y]
            hombro_izq = [lm_hombro_izq.x, lm_hombro_izq.y]
            codo_izq = [lm_codo_izq.x, lm_codo_izq.y]
            cadera_der = [lm_cadera_der.x, lm_cadera_der.y]
            hombro_der = [lm_hombro_der.x, lm_hombro_der.y]
            codo_der = [lm_codo_der.x, lm_codo_der.y]
 
            self.historial_izq.append(self.calcular_angulo_3puntos(cadera_izq, hombro_izq, codo_izq))
            self.historial_der.append(self.calcular_angulo_3puntos(cadera_der, hombro_der, codo_der))
            angulo_izq = sum(self.historial_izq) / len(self.historial_izq)
            angulo_der = sum(self.historial_der) / len(self.historial_der)
            angulo_prom = (angulo_izq + angulo_der) / 2
 
            if angulo_prom > self.angulo_maximo_rep:
                self.angulo_maximo_rep = angulo_prom
 
            # Torso: reusamos el mismo cálculo de inclinación que en sentadillas/desplantes
            inclinacion_izq = self.calcular_angulo_espalda(hombro_izq, cadera_izq)
            inclinacion_der = self.calcular_angulo_espalda(hombro_der, cadera_der)
            inclinacion_torso = (inclinacion_izq + inclinacion_der) / 2
            if inclinacion_torso > 90:
                inclinacion_torso = 180 - inclinacion_torso
 
            # Desnivel de hombros (te vas "chueco" hacia un lado): comparamos
            # la altura (y) de un hombro contra el otro, normalizado por la
            # separación entre hombros para que no dependa de qué tan cerca
            # estés de la cámara.
            desnivel_hombros = abs(hombro_izq[1] - hombro_der[1]) / separacion_hombros
 
            # Congelamos la posición de "reposo" del hombro solo cuando el
            # brazo está claramente abajo (umbral estricto, con margen para
            # que el suavizado no alcance a "perseguir" un encogimiento real).
            if angulo_prom < self.UMBRAL_REPOSO_BASELINE:
                self.hombro_reposo_izq = hombro_izq
                self.hombro_reposo_der = hombro_der
 
            # 1. Estado y conteo
            if angulo_prom > self.UMBRAL_ARRIBA:
                self.frames_arriba += 1
                self.frames_abajo = 0
 
                if self.frames_arriba >= self.UMBRAL_ESTADO:
                    self.estado = "ARRIBA"
                    alerta = "Buena altura"
                    color_alerta = (0, 255, 0)
 
            elif angulo_prom < self.UMBRAL_ABAJO:
                self.frames_abajo += 1
                self.frames_arriba = 0
 
                if self.frames_abajo >= self.UMBRAL_ESTADO:
                    if self.estado == "ARRIBA":
                        self.contador += 1
 
                        errores_rep = []
                        if self.frames_error_hombro_rep > 0:
                            errores_rep.append("hombro")
                        if self.frames_error_torso_rep > 0:
                            errores_rep.append("torso")
                        if self.frames_error_desnivel_rep > 0:
                            errores_rep.append("desnivel")
                        if self.frames_error_altura_rep > 0:
                            errores_rep.append("altura")
 
                        if "hombro" in errores_rep:
                            alerta = f"Rep {self.contador}: ¡Baja los hombros!"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero baja los hombros"
                        elif "torso" in errores_rep:
                            alerta = f"Rep {self.contador}: ¡No te inclines!"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero no te inclines"
                        elif "desnivel" in errores_rep:
                            alerta = f"Rep {self.contador}: ¡Nivela los hombros!"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero nivela los hombros"
                        elif "altura" in errores_rep:
                            alerta = f"Rep {self.contador}: No subas tanto"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero no subas tanto"
                        else:
                            alerta = f"¡Bien hecho! ({self.contador})"
                            evento_voz = f"Bien {self.contador}"
                            color_alerta = (0, 255, 0)
 
                        info_repeticion = {
                            "numero_rep": self.contador,
                            "angulo_minimo": int(self.angulo_maximo_rep),
                            "correcta": len(errores_rep) == 0,
                            "errores": errores_rep,
                            "precision": self.precision_actual,
                        }
                        self.angulo_maximo_rep = 0
                        self.frames_totales_rep = 0
                        self.frames_error_hombro_precision = 0
                        self.frames_error_torso_precision = 0
                        self.frames_error_desnivel_precision = 0
                        self.frames_error_altura_precision = 0
                    else:
                        alerta = "Listo, sube"
                        color_alerta = (0, 255, 0)
 
                    self.estado = "ABAJO"
                    self.frames_error_hombro_rep = 0
                    self.frames_error_torso_rep = 0
                    self.frames_error_desnivel_rep = 0
                    self.frames_error_altura_rep = 0
 
            else:
                self.frames_abajo = 0
                self.frames_arriba = 0
                if self.estado == "ABAJO":
                    alerta = "Subiendo..."
                    color_alerta = (255, 255, 0)
                else:
                    alerta = "Bajando..."
                    color_alerta = (0, 255, 255)
 
            # 2. Validación de encogimiento de hombros
            detecto_error_hombro_frame = False
            if angulo_prom >= self.UMBRAL_REPOSO_BASELINE and self.hombro_reposo_izq is not None:
                drift_izq = np.linalg.norm(np.array(hombro_izq) - np.array(self.hombro_reposo_izq))
                drift_der = np.linalg.norm(np.array(hombro_der) - np.array(self.hombro_reposo_der))
                if drift_izq > self.UMBRAL_DRIFT_HOMBRO or drift_der > self.UMBRAL_DRIFT_HOMBRO:
                    detecto_error_hombro_frame = True
 
            if detecto_error_hombro_frame:
                self.frames_error_hombro_rep += 1
                if self.frames_error_hombro_rep >= self.UMBRAL_FRAMES_ERROR and not self.hombro_reportado:
                    alerta = "¡Baja los hombros!"
                    color_alerta = (0, 0, 255)
                    evento_voz = "Baja los hombros"
                    self.hombro_reportado = True
            else:
                if self.frames_error_hombro_rep == 0:
                    self.hombro_reportado = False
 
            # 3. Validación de inclinación del torso
            detecto_error_torso_frame = inclinacion_torso > self.UMBRAL_INCLINACION_TORSO
            if detecto_error_torso_frame:
                self.frames_error_torso_rep += 1
                if self.frames_error_torso_rep >= self.UMBRAL_FRAMES_ERROR and not self.torso_reportado:
                    if evento_voz is None:
                        alerta = "¡No te inclines!"
                        color_alerta = (0, 0, 255)
                        evento_voz = "No te inclines"
                    self.torso_reportado = True
            else:
                if self.frames_error_torso_rep == 0:
                    self.torso_reportado = False
 
            # 4. Validación de desnivel entre hombros (te vas "chueco")
            detecto_error_desnivel_frame = desnivel_hombros > self.UMBRAL_DESNIVEL_HOMBROS
            if detecto_error_desnivel_frame:
                self.frames_error_desnivel_rep += 1
                if self.frames_error_desnivel_rep >= self.UMBRAL_FRAMES_ERROR and not self.desnivel_reportado:
                    if evento_voz is None:
                        alerta = "¡Nivela los hombros!"
                        color_alerta = (0, 0, 255)
                        evento_voz = "Hombro"
                    self.desnivel_reportado = True
            else:
                if self.frames_error_desnivel_rep == 0:
                    self.desnivel_reportado = False
 
            # 5. Validación de altura máxima (subir de más el brazo)
            detecto_error_altura_frame = angulo_prom > self.UMBRAL_MAXIMO
            if detecto_error_altura_frame:
                self.frames_error_altura_rep += 1
                if self.frames_error_altura_rep >= self.UMBRAL_FRAMES_ERROR and not self.altura_reportada:
                    if evento_voz is None:
                        alerta = "No subas tanto el brazo"
                        color_alerta = (0, 0, 255)
                        evento_voz = "No subas tanto"
                    self.altura_reportada = True
            else:
                if self.frames_error_altura_rep == 0:
                    self.altura_reportada = False
 
            # ---- Precisión en vivo ----
            if angulo_prom >= self.UMBRAL_REPOSO_BASELINE:
                self.frames_totales_rep += 1
                if detecto_error_hombro_frame:
                    self.frames_error_hombro_precision += 1
                if detecto_error_torso_frame:
                    self.frames_error_torso_precision += 1
                if detecto_error_desnivel_frame:
                    self.frames_error_desnivel_precision += 1
                if detecto_error_altura_frame:
                    self.frames_error_altura_precision += 1
 
            if self.frames_totales_rep > 0:
                fraccion_hombro = self.frames_error_hombro_precision / self.frames_totales_rep
                fraccion_torso = self.frames_error_torso_precision / self.frames_totales_rep
                fraccion_desnivel = self.frames_error_desnivel_precision / self.frames_totales_rep
                fraccion_altura = self.frames_error_altura_precision / self.frames_totales_rep
                self.precision_actual = round(
                    100
                    - 25 * fraccion_hombro
                    - 25 * fraccion_torso
                    - 25 * fraccion_desnivel
                    - 25 * fraccion_altura
                )
                self.precision_actual = max(0, min(100, self.precision_actual))
            else:
                self.precision_actual = 100
 
            return (int(angulo_prom), self.contador, alerta, color_alerta,
                    codo_izq, evento_voz, info_repeticion, self.precision_actual)
 
        except Exception:
            self.historial_izq.clear()
            self.historial_der.clear()
            self.hombro_reposo_izq = None
            self.hombro_reposo_der = None
            return 0, self.contador, "Alineate con la camara", (0, 0, 255), [0, 0], None, None, self.precision_actual
 
    # ------------------------------------------------------------
    def calcular_angulo_3puntos(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360.0 - angle
        return angle
 
    def calcular_angulo_espalda(self, hombro, cadera):
        hombro = np.array(hombro)
        cadera = np.array(cadera)
        vertical = np.array([cadera[0], cadera[1] + 1.0])
        return self.calcular_angulo_3puntos(hombro, cadera, vertical)
 