from collections import deque
import numpy as np
import mediapipe as mp
 
 
class GluteBridgeAnalyzer:
    """Analizador de Puente de Glúteos (Glute Bridge), vista DE PERFIL.
 
    Acostado boca arriba, rodillas dobladas, pies apoyados en el piso.
    El movimiento es subir/bajar la cadera. El programa elige solo el
    lado del cuerpo que mejor se vea (izquierdo o derecho), igual que
    en sentadillas y desplantes.
 
    Ángulo principal: hombro-cadera-rodilla (extensión de cadera).
    Abajo (cadera en el piso) el ángulo es más chico; arriba (cadera
    extendida, cuerpo en línea recta hombro-cadera-rodilla) se acerca
    a 180°.
 
    Errores de forma que vigila:
      - "Hiperextensión" (arquear la espalda baja subiendo la cadera
        más allá de la línea recta hombro-rodilla): se detecta
        geométricamente, comparando la cadera contra la línea que
        conecta hombro y rodilla, no con el ángulo (que se satura en
        180° y no distingue "recto" de "arqueado").
      - "Talones que se levantan": comparamos la altura del talón
        contra una línea base tomada mientras estás abajo, en reposo.
 
    NOTA: estos umbrales (UMBRAL_ARRIBA, UMBRAL_ABAJO, etc.) son un
    punto de partida razonable, no medidos con datos reales todavía.
    Igual que hiciste con los otros ejercicios, conviene correrlo,
    ver los prints de ángulo en consola, y afinar los números con tu
    propio rango de movimiento.
    """
 
    UMBRAL_ABAJO = 140    # cadera en el piso / reposo
    UMBRAL_ARRIBA = 165   # cadera extendida = arriba del puente
    UMBRAL_HIPEREXTENSION = 0.035  # cuánto puede pasarse la cadera de la línea hombro-rodilla
    UMBRAL_TALON = 0.03   # cuánto se puede levantar el talón del piso
 
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.estado = "ABAJO"
        self.contador = 0
 
        self.historial_cadera = deque(maxlen=3)
        # El talón es el landmark que más brinca (MediaPipe está entrenado
        # sobre todo con gente de pie, no acostada), así que lleva su
        # propio historial de suavizado, aparte del de la cadera.
        self.historial_talon = deque(maxlen=4)
 
        self.frames_abajo = 0
        self.frames_arriba = 0
        self.UMBRAL_ESTADO = 2
 
        # Filtro de orientación: no se analiza nada hasta confirmar que
        # ya estás acostado (mientras caminas hacia la cámara o te
        # acomodas, el cuerpo sigue "vertical" en la imagen).
        self.frames_acostado = 0
        self.frames_de_pie = 0
        self.acostado_confirmado = False
 
        # Línea base tomada en reposo (cadera en el piso): posición del
        # talón, para detectar si se despega del suelo durante el puente.
        self.talon_baseline = None
 
        self.frames_error_hiperext_rep = 0
        self.frames_error_talon_rep = 0
        self.UMBRAL_FRAMES_ERROR = 2
        self.hiperext_reportada = False
        self.talon_reportado = False
 
        # Qué lado del cuerpo se está usando para medir (se autodetecta,
        # igual que en sentadillas/desplantes)
        self.lado_bloqueado = None
 
        # ---- Precisión (0-100%) ----
        self.frames_totales_rep = 0
        self.frames_error_hiperext_precision = 0
        self.frames_error_talon_precision = 0
        self.precision_actual = 100
        self.angulo_maximo_rep = 0
 
    # ------------------------------------------------------------
    def _elegir_landmarks(self, landmarks):
        """Elige el lado del cuerpo con mejor visibilidad para la cámara
        y lo mantiene fijo durante el movimiento (mismo criterio que en
        sentadillas y desplantes)."""
        izq = (
            landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value],
            landmarks[self.mp_pose.PoseLandmark.LEFT_HEEL.value],
        )
        der = (
            landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value],
            landmarks[self.mp_pose.PoseLandmark.RIGHT_HEEL.value],
        )
        vis_izq = sum(p.visibility for p in izq)
        vis_der = sum(p.visibility for p in der)
 
        if self.lado_bloqueado == "IZQUIERDO" and vis_izq >= vis_der - 0.5:
            return izq
        if self.lado_bloqueado == "DERECHO" and vis_der >= vis_izq - 0.5:
            return der
 
        if vis_izq >= vis_der:
            self.lado_bloqueado = "IZQUIERDO"
            return izq
        else:
            self.lado_bloqueado = "DERECHO"
            return der
 
    # ------------------------------------------------------------
    def analizar(self, results):
        alerta = "Colócate de perfil"
        color_alerta = (255, 255, 255)
        evento_voz = None
        info_repeticion = None
 
        try:
            landmarks = results.pose_landmarks.landmark
 
            lm_hombro, lm_cadera, lm_rodilla, lm_tobillo, lm_talon = self._elegir_landmarks(landmarks)
 
            VISIBILIDAD_MINIMA = 0.6
            visibilidad_min = min(
                lm_hombro.visibility, lm_cadera.visibility,
                lm_rodilla.visibility, lm_tobillo.visibility, lm_talon.visibility,
            )
            visibilidad_promedio_total = sum(lm.visibility for lm in landmarks) / len(landmarks)
 
            if visibilidad_min < VISIBILIDAD_MINIMA or visibilidad_promedio_total < 0.5:
                raise ValueError("Landmarks poco confiables (probablemente no eres tú)")
 
            hombro = [lm_hombro.x, lm_hombro.y]
            cadera = [lm_cadera.x, lm_cadera.y]
            rodilla = [lm_rodilla.x, lm_rodilla.y]
            tobillo = [lm_tobillo.x, lm_tobillo.y]
 
            # ---- Filtro de orientación: acostado vs. de pie ----
            # Estando de pie/caminando, la diferencia de ALTURA entre hombro
            # y tobillo es grande y la diferencia HORIZONTAL es chica.
            # Acostado de perfil es al revés: el cuerpo es horizontal en la
            # imagen. Con esto ignoramos por completo lo que pase mientras
            # todavía te estás acomodando frente a la cámara.
            dx_cuerpo = abs(hombro[0] - tobillo[0])
            dy_cuerpo = abs(hombro[1] - tobillo[1])
            esta_acostado = dx_cuerpo > dy_cuerpo
 
            if esta_acostado:
                self.frames_acostado += 1
                self.frames_de_pie = 0
            else:
                self.frames_de_pie += 1
                self.frames_acostado = 0
 
            if self.frames_de_pie >= self.UMBRAL_ESTADO:
                self.acostado_confirmado = False
 
            if self.frames_acostado >= self.UMBRAL_ESTADO and not self.acostado_confirmado:
                self.acostado_confirmado = True
                # Te acabas de acostar: reiniciamos todo para no arrastrar
                # ruido de cuando estabas de pie caminando hacia la cámara.
                self.historial_cadera.clear()
                self.historial_talon.clear()
                self.talon_baseline = None
                self.estado = "ABAJO"
                self.frames_abajo = 0
                self.frames_arriba = 0
 
            if not self.acostado_confirmado:
                self.historial_cadera.clear()
                return (0, self.contador, "Acuéstate boca arriba, de perfil",
                        (255, 255, 0), cadera, None, None, self.precision_actual)
 
            # Suavizado + filtro anti-teletransporte del talón (landmark
            # más ruidoso, sobre todo acostado)
            talon_crudo_y = lm_talon.y
            if self.historial_talon:
                ultimo_talon = self.historial_talon[-1]
                diferencia_talon = talon_crudo_y - ultimo_talon
                if abs(diferencia_talon) > 0.05:
                    talon_crudo_y = ultimo_talon + np.sign(diferencia_talon) * 0.05
            self.historial_talon.append(talon_crudo_y)
            talon = [lm_talon.x, sum(self.historial_talon) / len(self.historial_talon)]
 
            # Cálculo del ángulo crudo y filtro anti-teletransportes de
            # MediaPipe antes de pasarlo al historial (mismo mecanismo
            # que en sentadillas/desplantes)
            angulo_crudo = self.calcular_angulo_3puntos(hombro, cadera, rodilla)
 
            if self.historial_cadera:
                ultimo = self.historial_cadera[-1]
                diferencia = angulo_crudo - ultimo
                if abs(diferencia) > 30:
                    angulo_crudo = ultimo + np.sign(diferencia) * 30
 
            self.historial_cadera.append(angulo_crudo)
            angulo_cadera = sum(self.historial_cadera) / len(self.historial_cadera)
 
            if angulo_cadera > self.angulo_maximo_rep:
                self.angulo_maximo_rep = angulo_cadera
 
            # Hiperextensión: en vez de fiarnos del ángulo (que se satura
            # en 180° y no distingue "recto" de "arqueado hacia arriba"),
            # comparamos la cadera contra la línea recta hombro-rodilla.
            # Si la cadera queda claramente por ARRIBA de esa línea
            # (y numéricamente más chica, porque en imagen "arriba" es
            # menor y), es que se pasó de la extensión neutral.
            if hombro[0] != rodilla[0]:
                t = (cadera[0] - hombro[0]) / (rodilla[0] - hombro[0])
                y_esperada = hombro[1] + t * (rodilla[1] - hombro[1])
            else:
                y_esperada = (hombro[1] + rodilla[1]) / 2
            hiperextension = y_esperada - cadera[1]  # positivo = cadera por arriba de la línea
 
            # 1. Estado y conteo
            if angulo_cadera > self.UMBRAL_ARRIBA:
                self.frames_arriba += 1
                self.frames_abajo = 0
 
                if self.frames_arriba >= self.UMBRAL_ESTADO:
                    self.estado = "ARRIBA"
                    alerta = "Buena extensión"
                    color_alerta = (0, 255, 0)
 
            elif angulo_cadera < self.UMBRAL_ABAJO:
                self.frames_abajo += 1
                self.frames_arriba = 0
 
                if self.frames_abajo >= self.UMBRAL_ESTADO:
                    if self.estado == "ARRIBA":
                        self.contador += 1
 
                        errores_rep = []
                        if self.frames_error_hiperext_rep > 0:
                            errores_rep.append("hiperextension")
                        if self.frames_error_talon_rep > 0:
                            errores_rep.append("talon")
 
                        if "hiperextension" in errores_rep:
                            alerta = f"Rep {self.contador}: ¡No arquees tanto!"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero no arquees tanto"
                        elif "talon" in errores_rep:
                            alerta = f"Rep {self.contador}: ¡Baja los talones!"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero baja los talones"
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
                        self.frames_error_hiperext_precision = 0
                        self.frames_error_talon_precision = 0
                    else:
                        alerta = "Listo, sube la cadera"
                        color_alerta = (0, 255, 0)
 
                    # Se vuelve a tomar la línea base del talón cada vez
                    # que regresas al piso, por si te recorriste un poco.
                    self.talon_baseline = talon
                    self.estado = "ABAJO"
                    self.frames_error_hiperext_rep = 0
                    self.frames_error_talon_rep = 0
 
            else:
                self.frames_abajo = 0
                self.frames_arriba = 0
                if self.estado == "ABAJO":
                    alerta = "Subiendo..."
                    color_alerta = (255, 255, 0)
                else:
                    alerta = "Bajando..."
                    color_alerta = (0, 255, 255)
 
            if self.talon_baseline is None:
                self.talon_baseline = talon
 
            # 2. Validación de hiperextensión (solo importa una vez que
            # ya extendiste la cadera, no mientras sigues en el piso)
            detecto_error_hiperext_frame = (
                self.estado == "ARRIBA" and hiperextension > self.UMBRAL_HIPEREXTENSION
            )
            if detecto_error_hiperext_frame:
                self.frames_error_hiperext_rep += 1
                if self.frames_error_hiperext_rep >= self.UMBRAL_FRAMES_ERROR and not self.hiperext_reportada:
                    if evento_voz is None:
                        alerta = "¡No arquees tanto!"
                        color_alerta = (0, 0, 255)
                        evento_voz = "No arquees tanto"
                    self.hiperext_reportada = True
            else:
                if self.frames_error_hiperext_rep == 0:
                    self.hiperext_reportada = False
 
            # 3. Validación de talones (se despegan del piso)
            drift_talon = self.talon_baseline[1] - talon[1]  # positivo = el talón subió
            detecto_error_talon_frame = self.estado == "ARRIBA" and drift_talon > self.UMBRAL_TALON
            if detecto_error_talon_frame:
                self.frames_error_talon_rep += 1
                if self.frames_error_talon_rep >= self.UMBRAL_FRAMES_ERROR and not self.talon_reportado:
                    if evento_voz is None:
                        alerta = "¡Baja los talones!"
                        color_alerta = (0, 0, 255)
                        evento_voz = "Baja los talones"
                    self.talon_reportado = True
            else:
                if self.frames_error_talon_rep == 0:
                    self.talon_reportado = False
 
            # ---- Precisión en vivo ----
            if self.estado == "ARRIBA":
                self.frames_totales_rep += 1
                if detecto_error_hiperext_frame:
                    self.frames_error_hiperext_precision += 1
                if detecto_error_talon_frame:
                    self.frames_error_talon_precision += 1
 
            if self.frames_totales_rep > 0:
                fraccion_hiperext = self.frames_error_hiperext_precision / self.frames_totales_rep
                fraccion_talon = self.frames_error_talon_precision / self.frames_totales_rep
                self.precision_actual = round(100 - 30 * fraccion_hiperext - 30 * fraccion_talon)
                self.precision_actual = max(0, min(100, self.precision_actual))
            else:
                self.precision_actual = 100
 
            return (int(angulo_cadera), self.contador, alerta, color_alerta,
                    cadera, evento_voz, info_repeticion, self.precision_actual)
 
        except Exception:
            self.historial_cadera.clear()
            self.historial_talon.clear()
            self.talon_baseline = None
            self.lado_bloqueado = None
            self.acostado_confirmado = False
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
 