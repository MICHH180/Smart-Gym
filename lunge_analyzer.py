# from collections import deque
# import numpy as np
# import mediapipe as mp
 
 
# class LungeAnalyzer:
#     """Analizador de Desplantes / Zancadas (Lunges).
 
#     Igual que en sentadillas, ponte DE PERFIL a la cámara (el programa
#     elige solo el lado que mejor se vea, izquierdo o derecho).
 
#     Diferencias clave contra la sentadilla:
#       - El fondo es más profundo (la rodilla trasera casi toca el piso),
#         así que el umbral de "abajo" es más exigente.
#       - El error de forma más común no es la cadera, es el TORSO
#         inclinándose hacia adelante en vez de mantenerse recto.
#       - Aquí sí importa registrar CUÁL pierna trabajó (para la base de
#         datos / futura UI), cosa que en la sentadilla no aplicaba.
#     """
 
#     UMBRAL_ABAJO = 100   # rodilla muy doblada = fondo del desplante
#     UMBRAL_ARRIBA = 155  # pierna casi extendida = de pie
#     UMBRAL_TORSO = 30    # grados de inclinación del torso considerados error
 
#     def __init__(self):
#         self.mp_pose = mp.solutions.pose
#         self.estado = "ARRIBA"
#         self.contador = 0
 
#         self.historial_rodilla = deque(maxlen=3)
 
#         self.frames_abajo = 0
#         self.frames_arriba = 0
#         self.UMBRAL_ESTADO = 2
 
#         self.frames_error_espalda = 0
#         self.UMBRAL_FRAMES_ERROR = 2
#         self.espalda_reportada = False
 
#         # Lado del cuerpo que se está usando para medir (se autodetecta)
#         self.lado_bloqueado = None
 
#         # Para guardar en la base de datos: qué tan profundo llegó esta repetición
#         self.angulo_minimo_rep = 180
 
#     # ------------------------------------------------------------
#     def _elegir_landmarks(self, landmarks):
#         """Elige el lado del cuerpo con mejor visibilidad para la cámara
#         y lo mantiene fijo durante el movimiento (mismo criterio que en
#         sentadillas)."""
#         izq = (
#             landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
#             landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value],
#             landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value],
#             landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value],
#         )
#         der = (
#             landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
#             landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value],
#             landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value],
#             landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value],
#         )
#         vis_izq = sum(p.visibility for p in izq)
#         vis_der = sum(p.visibility for p in der)
 
#         # Si ya habíamos elegido un lado, nos quedamos con él salvo que el
#         # otro sea MUY claramente mejor. En el desplante las piernas se
#         # cruzan/se encima en la imagen más que en la sentadilla, así que
#         # aquí necesitamos más resistencia al cambio para no confundirnos
#         # a media repetición.
#         if self.lado_bloqueado == "izquierda" and vis_izq >= vis_der - 1.2:
#             return izq, "izquierda"
#         if self.lado_bloqueado == "derecha" and vis_der >= vis_izq - 1.2:
#             return der, "derecha"
 
#         if vis_izq >= vis_der:
#             self.lado_bloqueado = "izquierda"
#             return izq, "izquierda"
#         else:
#             self.lado_bloqueado = "derecha"
#             return der, "derecha"
 
#     # ------------------------------------------------------------
#     def analizar(self, results):
#         """Devuelve: angulo, contador, alerta, color_alerta, punto_rodilla,
#         evento_voz, info_repeticion
 
#         info_repeticion es None casi siempre, y solo trae datos (dict) el
#         frame exacto en que se cuenta una repetición nueva -- pensado para
#         guardarse directo en la base de datos en ese mismo frame.
#         """
#         alerta = "Colócate de perfil"
#         color_alerta = (255, 255, 255)
#         evento_voz = None
#         info_repeticion = None
 
#         try:
#             landmarks = results.pose_landmarks.landmark
#             (lm_hombro, lm_cadera, lm_rodilla, lm_tobillo), pierna = self._elegir_landmarks(landmarks)
 
#             VISIBILIDAD_MINIMA = 0.6
#             visibilidad_min = min(
#                 lm_hombro.visibility, lm_cadera.visibility,
#                 lm_rodilla.visibility, lm_tobillo.visibility
#             )
#             visibilidad_promedio_total = sum(lm.visibility for lm in landmarks) / len(landmarks)
 
#             if visibilidad_min < VISIBILIDAD_MINIMA or visibilidad_promedio_total < 0.5:
#                 raise ValueError("Landmarks poco confiables (probablemente no eres tú)")
 
#             hombro = [lm_hombro.x, lm_hombro.y]
#             cadera = [lm_cadera.x, lm_cadera.y]
#             rodilla = [lm_rodilla.x, lm_rodilla.y]
#             tobillo = [lm_tobillo.x, lm_tobillo.y]
 
#             # Ángulo de rodilla con filtro anti-teletransportes + suavizado
#             angulo_crudo = self.calcular_angulo_3puntos(cadera, rodilla, tobillo)
#             if self.historial_rodilla:
#                 ultimo = self.historial_rodilla[-1]
#                 diferencia = angulo_crudo - ultimo
#                 if abs(diferencia) > 30:
#                     angulo_crudo = ultimo + np.sign(diferencia) * 30
#             self.historial_rodilla.append(angulo_crudo)
#             angulo_rodilla = sum(self.historial_rodilla) / len(self.historial_rodilla)
 
#             # Ángulo de torso respecto a la vertical
#             inclinacion_torso = self.calcular_angulo_espalda(hombro, cadera)
#             if inclinacion_torso > 90:
#                 inclinacion_torso = 180 - inclinacion_torso
 
#             if angulo_rodilla < self.angulo_minimo_rep:
#                 self.angulo_minimo_rep = angulo_rodilla
 
#             # 0. Validación de POSTURA: un desplante tiene los pies separados
#             # uno adelante y otro atrás (postura en tijera). Sin este chequeo,
#             # doblar la rodilla en CUALQUIER postura -incluida una sentadilla
#             # con los pies juntos- se contaba igual como desplante.
#             lm_tobillo_izq = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
#             lm_tobillo_der = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
#             separacion_tobillos = abs(lm_tobillo_izq.x - lm_tobillo_der.x)
 
#             UMBRAL_SEPARACION_MINIMA = 0.15  # ajusta este número si hace falta calibrar
#             if separacion_tobillos < UMBRAL_SEPARACION_MINIMA:
#                 # Pies juntos / en paralelo: no es postura de desplante (parece sentadilla).
#                 # No acumulamos frames de estado para no contar nada en esta postura.
#                 self.frames_abajo = 0
#                 self.frames_arriba = 0
#                 return (int(angulo_rodilla), self.contador,
#                         "Da un paso: separa los pies (adelante/atrás)",
#                         (255, 255, 0), rodilla, None, None)
 
#             # 1. Estado y conteo
#             if angulo_rodilla > self.UMBRAL_ARRIBA:
#                 self.frames_arriba += 1
#                 self.frames_abajo = 0
 
#                 if self.frames_arriba >= self.UMBRAL_ESTADO:
#                     if self.estado == "ABAJO":
#                         self.contador += 1
#                         error_torso = inclinacion_torso > self.UMBRAL_TORSO
 
#                         if error_torso:
#                             alerta = f"Rep {self.contador}: ¡Mantén el torso recto!"
#                             color_alerta = (0, 0, 255)
#                             evento_voz = "Bien pero endereza el torso"
#                         else:
#                             alerta = f"¡Bien hecho! ({self.contador})"
#                             evento_voz = f"Bien {self.contador}"
#                             color_alerta = (0, 255, 0)
 
#                         info_repeticion = {
#                             "numero_rep": self.contador,
#                             "pierna": pierna,
#                             "angulo_minimo": int(self.angulo_minimo_rep),
#                             "correcta": not error_torso,
#                             "errores": ["torso"] if error_torso else [],
#                         }
#                         self.angulo_minimo_rep = 180
#                     else:
#                         alerta = "Correcto: Sube"
#                         color_alerta = (0, 255, 0)
 
#                     self.estado = "ARRIBA"
 
#             elif angulo_rodilla <= self.UMBRAL_ABAJO:
#                 self.frames_abajo += 1
#                 self.frames_arriba = 0
 
#                 if self.frames_abajo >= self.UMBRAL_ESTADO:
#                     self.estado = "ABAJO"
#                     alerta = "Buena profundidad"
#                     color_alerta = (0, 255, 0)
 
#             else:
#                 self.frames_abajo = 0
#                 self.frames_arriba = 0
#                 if self.estado == "ARRIBA":
#                     alerta = "Bajando..."
#                     color_alerta = (255, 255, 0)
#                 elif self.estado == "ABAJO":
#                     alerta = "Subiendo..."
#                     color_alerta = (0, 255, 255)
 
#             # 2. Validación de torso (aviso mientras bajas, no solo al final)
#             detecto_error_torso_frame = (
#                 inclinacion_torso > self.UMBRAL_TORSO and self.estado == "ABAJO"
#             )
#             if detecto_error_torso_frame:
#                 self.frames_error_espalda += 1
#                 if self.frames_error_espalda >= self.UMBRAL_FRAMES_ERROR and not self.espalda_reportada:
#                     if evento_voz is None:
#                         alerta = "¡Mantén el torso recto!"
#                         color_alerta = (0, 0, 255)
#                         evento_voz = "Endereza"
#                     self.espalda_reportada = True
#             else:
#                 self.frames_error_espalda = max(0, self.frames_error_espalda - 1)
#                 if self.frames_error_espalda == 0:
#                     self.espalda_reportada = False
 
#             return int(angulo_rodilla), self.contador, alerta, color_alerta, rodilla, evento_voz, info_repeticion
 
#         except Exception:
#             self.historial_rodilla.clear()
#             self.lado_bloqueado = None
#             return 0, self.contador, "Alineate con la camara", (0, 0, 255), [0, 0], None, None
 
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
 
 
class LungeAnalyzer:
    """Analizador de Desplantes / Zancadas (Lunges).
 
    Igual que en sentadillas, ponte DE PERFIL a la cámara (el programa
    elige solo el lado que mejor se vea, izquierdo o derecho).
 
    Diferencias clave contra la sentadilla:
      - El fondo es más profundo (la rodilla trasera casi toca el piso),
        así que el umbral de "abajo" es más exigente.
      - El error de forma más común no es la cadera, es el TORSO
        inclinándose hacia adelante en vez de mantenerse recto.
      - Aquí sí importa registrar CUÁL pierna trabajó (para la base de
        datos / futura UI), cosa que en la sentadilla no aplicaba.
    """
 
    UMBRAL_ABAJO = 100   # rodilla muy doblada = fondo del desplante
    UMBRAL_ARRIBA = 155  # pierna casi extendida = de pie
    UMBRAL_TORSO = 30    # grados de inclinación del torso considerados error
 
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.estado = "ARRIBA"
        self.contador = 0
 
        self.historial_rodilla = deque(maxlen=3)
 
        self.frames_abajo = 0
        self.frames_arriba = 0
        self.UMBRAL_ESTADO = 2
 
        self.frames_error_espalda = 0
        self.UMBRAL_FRAMES_ERROR = 2
        self.espalda_reportada = False
 
        # Lado del cuerpo que se está usando para medir (se autodetecta)
        self.lado_bloqueado = None
 
        # Para guardar en la base de datos: qué tan profundo llegó esta repetición
        self.angulo_minimo_rep = 180
 
        # ---- Sistema de precisión (0-100%) ----
        # En el desplante solo hay un tipo de error (torso), así que pesa más
        # que en la sentadilla: una rep con error todo el tiempo cae a 40%.
        self.frames_totales_rep = 0
        self.frames_error_torso_rep = 0
        self.precision_actual = 100
 
    # ------------------------------------------------------------
    def _elegir_landmarks(self, landmarks):
        """Elige el lado del cuerpo con mejor visibilidad para la cámara
        y lo mantiene fijo durante el movimiento (mismo criterio que en
        sentadillas)."""
        izq = (
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value],
        )
        der = (
            landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value],
        )
        vis_izq = sum(p.visibility for p in izq)
        vis_der = sum(p.visibility for p in der)
 
        # Si ya habíamos elegido un lado, nos quedamos con él salvo que el
        # otro sea MUY claramente mejor. En el desplante las piernas se
        # cruzan/se encima en la imagen más que en la sentadilla, así que
        # aquí necesitamos más resistencia al cambio para no confundirnos
        # a media repetición.
        if self.lado_bloqueado == "izquierda" and vis_izq >= vis_der - 1.2:
            return izq, "izquierda"
        if self.lado_bloqueado == "derecha" and vis_der >= vis_izq - 1.2:
            return der, "derecha"
 
        if vis_izq >= vis_der:
            self.lado_bloqueado = "izquierda"
            return izq, "izquierda"
        else:
            self.lado_bloqueado = "derecha"
            return der, "derecha"
 
    # ------------------------------------------------------------
    def analizar(self, results):
        """Devuelve: angulo, contador, alerta, color_alerta, punto_rodilla,
        evento_voz, info_repeticion
 
        info_repeticion es None casi siempre, y solo trae datos (dict) el
        frame exacto en que se cuenta una repetición nueva -- pensado para
        guardarse directo en la base de datos en ese mismo frame.
        """
        alerta = "Colócate de perfil"
        color_alerta = (255, 255, 255)
        evento_voz = None
        info_repeticion = None
 
        try:
            landmarks = results.pose_landmarks.landmark
            (lm_hombro, lm_cadera, lm_rodilla, lm_tobillo), pierna = self._elegir_landmarks(landmarks)
 
            VISIBILIDAD_MINIMA = 0.6
            visibilidad_min = min(
                lm_hombro.visibility, lm_cadera.visibility,
                lm_rodilla.visibility, lm_tobillo.visibility
            )
            visibilidad_promedio_total = sum(lm.visibility for lm in landmarks) / len(landmarks)
 
            if visibilidad_min < VISIBILIDAD_MINIMA or visibilidad_promedio_total < 0.5:
                raise ValueError("Landmarks poco confiables (probablemente no eres tú)")
 
            hombro = [lm_hombro.x, lm_hombro.y]
            cadera = [lm_cadera.x, lm_cadera.y]
            rodilla = [lm_rodilla.x, lm_rodilla.y]
            tobillo = [lm_tobillo.x, lm_tobillo.y]
 
            # Ángulo de rodilla con filtro anti-teletransportes + suavizado
            angulo_crudo = self.calcular_angulo_3puntos(cadera, rodilla, tobillo)
            if self.historial_rodilla:
                ultimo = self.historial_rodilla[-1]
                diferencia = angulo_crudo - ultimo
                if abs(diferencia) > 30:
                    angulo_crudo = ultimo + np.sign(diferencia) * 30
            self.historial_rodilla.append(angulo_crudo)
            angulo_rodilla = sum(self.historial_rodilla) / len(self.historial_rodilla)
 
            # Ángulo de torso respecto a la vertical
            inclinacion_torso = self.calcular_angulo_espalda(hombro, cadera)
            if inclinacion_torso > 90:
                inclinacion_torso = 180 - inclinacion_torso
 
            if angulo_rodilla < self.angulo_minimo_rep:
                self.angulo_minimo_rep = angulo_rodilla
 
            # 0. Validación de POSTURA: un desplante tiene los pies separados
            # uno adelante y otro atrás (postura en tijera). Sin este chequeo,
            # doblar la rodilla en CUALQUIER postura -incluida una sentadilla
            # con los pies juntos- se contaba igual como desplante.
            lm_tobillo_izq = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
            lm_tobillo_der = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
            separacion_tobillos = abs(lm_tobillo_izq.x - lm_tobillo_der.x)
 
            UMBRAL_SEPARACION_MINIMA = 0.15  # ajusta este número si hace falta calibrar
            if separacion_tobillos < UMBRAL_SEPARACION_MINIMA:
                # Pies juntos / en paralelo: no es postura de desplante (parece sentadilla).
                # No acumulamos frames de estado para no contar nada en esta postura.
                self.frames_abajo = 0
                self.frames_arriba = 0
                return (int(angulo_rodilla), self.contador,
                        "Da un paso: separa los pies (adelante/atrás)",
                        (255, 255, 0), rodilla, None, None, self.precision_actual)
 
            # 1. Estado y conteo
            if angulo_rodilla > self.UMBRAL_ARRIBA:
                self.frames_arriba += 1
                self.frames_abajo = 0
 
                if self.frames_arriba >= self.UMBRAL_ESTADO:
                    if self.estado == "ABAJO":
                        self.contador += 1
                        error_torso = inclinacion_torso > self.UMBRAL_TORSO
 
                        if error_torso:
                            alerta = f"Rep {self.contador}: ¡Mantén el torso recto!"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero endereza el torso"
                        else:
                            alerta = f"¡Bien hecho! ({self.contador})"
                            evento_voz = f"Bien {self.contador}"
                            color_alerta = (0, 255, 0)
 
                        info_repeticion = {
                            "numero_rep": self.contador,
                            "pierna": pierna,
                            "angulo_minimo": int(self.angulo_minimo_rep),
                            "correcta": not error_torso,
                            "errores": ["torso"] if error_torso else [],
                            "precision": self.precision_actual,
                        }
                        self.angulo_minimo_rep = 180
                    else:
                        alerta = "Correcto: Sube"
                        color_alerta = (0, 255, 0)
 
                    self.estado = "ARRIBA"
 
            elif angulo_rodilla <= self.UMBRAL_ABAJO:
                self.frames_abajo += 1
                self.frames_arriba = 0
 
                if self.frames_abajo >= self.UMBRAL_ESTADO:
                    self.estado = "ABAJO"
                    alerta = "Buena profundidad"
                    color_alerta = (0, 255, 0)
                    self.frames_totales_rep = 0
                    self.frames_error_torso_rep = 0
 
            else:
                self.frames_abajo = 0
                self.frames_arriba = 0
                if self.estado == "ARRIBA":
                    alerta = "Bajando..."
                    color_alerta = (255, 255, 0)
                elif self.estado == "ABAJO":
                    alerta = "Subiendo..."
                    color_alerta = (0, 255, 255)
 
            # 2. Validación de torso (aviso mientras bajas, no solo al final)
            detecto_error_torso_frame = (
                inclinacion_torso > self.UMBRAL_TORSO and self.estado == "ABAJO"
            )
            if detecto_error_torso_frame:
                self.frames_error_espalda += 1
                if self.frames_error_espalda >= self.UMBRAL_FRAMES_ERROR and not self.espalda_reportada:
                    if evento_voz is None:
                        alerta = "¡Mantén el torso recto!"
                        color_alerta = (0, 0, 255)
                        evento_voz = "Endereza"
                    self.espalda_reportada = True
            else:
                self.frames_error_espalda = max(0, self.frames_error_espalda - 1)
                if self.frames_error_espalda == 0:
                    self.espalda_reportada = False
 
            # ---- Precisión en vivo ----
            if self.estado == "ABAJO":
                self.frames_totales_rep += 1
                if detecto_error_torso_frame:
                    self.frames_error_torso_rep += 1
 
            if self.frames_totales_rep > 0:
                fraccion_torso = self.frames_error_torso_rep / self.frames_totales_rep
                self.precision_actual = round(100 - 60 * fraccion_torso)
                self.precision_actual = max(0, min(100, self.precision_actual))
            else:
                self.precision_actual = 100
 
            return (int(angulo_rodilla), self.contador, alerta, color_alerta,
                    rodilla, evento_voz, info_repeticion, self.precision_actual)
 
        except Exception:
            self.historial_rodilla.clear()
            self.lado_bloqueado = None
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
 