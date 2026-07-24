

# from collections import deque
# import numpy as np
# import mediapipe as mp
 
# class SquatAnalyzer:
#     def __init__(self):
#         self.mp_pose = mp.solutions.pose
#         self.estado = "ARRIBA"
#         self.contador = 0
        
#         # Historial para suavizar el ángulo de la rodilla (ventana corta para no meter latencia extra)
#         self.historial_rodilla = deque(maxlen=3)
        
#         # Variables para rastrear el movimiento anterior (se mantienen por compatibilidad)
#         self.hombro_anterior = None
#         self.cadera_anterior = None
        
#         # Línea base (posición de hombro/cadera en el fondo de la sentadilla).
#         # El detector de "good morning" compara contra ESTA posición durante
#         # toda la subida, en vez de comparar frame a frame (que es muy ruidoso).
#         self.cadera_baseline = None
#         self.hombro_baseline = None
#         self.UMBRAL_DESFASE_CADERA = 0.05  # cuánto más debe subir la cadera vs el hombro para marcar error
#         self.SUBIDA_MINIMA = 0.03          # movimiento mínimo para no disparar con ruido/quietud
 
#         # Contadores de persistencia y umbrales para filtros (~300 ms)
#         self.frames_error_cadera = 0
#         self.frames_error_espalda = 0
#         self.UMBRAL_FRAMES_ERROR = 2  
        
#         # Contadores de estabilidad de estado (2 = necesita confirmación en 2 frames
#         # seguidos antes de contar un cambio de estado; evita falsos conteos cuando
#         # la malla pierde tracking por un instante y los puntos "brincan")
#         self.frames_abajo = 0
#         self.frames_arriba = 0
#         self.UMBRAL_ESTADO = 2
        
#         # Banderas para evitar bucles infinitos de voz
#         self.cadera_reportada = False
#         self.espalda_reportada = False
 
#         # Qué lado del cuerpo (izquierdo o derecho) se está usando para medir.
#         # Se elige automáticamente según cuál ve mejor la cámara y se mantiene
#         # fijo durante el movimiento para no meter saltos.
#         self.lado_bloqueado = None
 
#     def _elegir_landmarks(self, landmarks):
#         """Elige el lado del cuerpo con mejor visibilidad para la cámara.
#         Antes el código solo usaba el lado izquierdo, por eso de perfil total
#         solo funcionaba si justo ese lado quedaba hacia la cámara."""
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
#         # otro sea claramente mejor (evita que cambie de lado a media rep)
#         if self.lado_bloqueado == "IZQUIERDO" and vis_izq >= vis_der - 0.5:
#             return izq
#         if self.lado_bloqueado == "DERECHO" and vis_der >= vis_izq - 0.5:
#             return der
 
#         if vis_izq >= vis_der:
#             self.lado_bloqueado = "IZQUIERDO"
#             return izq
#         else:
#             self.lado_bloqueado = "DERECHO"
#             return der
        
#     def analizar(self, results):
#         alerta = "Colócate de perfil"
#         color_alerta = (255, 255, 255)
#         evento_voz = None
        
#         try:
#             landmarks = results.pose_landmarks.landmark
            
#             lm_hombro, lm_cadera, lm_rodilla, lm_tobillo = self._elegir_landmarks(landmarks)
 
#             # MediaPipe SIEMPRE devuelve landmarks, incluso cuando lo que ve no es
#             # realmente una persona (fondo, objetos, sombras). El campo `visibility`
#             # indica qué tan seguro está el modelo de ese punto. Si es bajo, es ruido
#             # y NO debe usarse para contar ni analizar la sentadilla.
#             VISIBILIDAD_MINIMA = 0.6
#             visibilidad_min = min(
#                 lm_hombro.visibility, lm_cadera.visibility,
#                 lm_rodilla.visibility, lm_tobillo.visibility
#             )
#             # Chequeo extra: si la malla completa (incluyendo manos/brazos) está
#             # degradada en promedio, es señal de que el tracking general se está
#             # perdiendo, aunque los 4 puntos que usamos todavía pasen el umbral.
#             visibilidad_promedio_total = sum(lm.visibility for lm in landmarks) / len(landmarks)
 
#             if visibilidad_min < VISIBILIDAD_MINIMA or visibilidad_promedio_total < 0.5:
#                 raise ValueError("Landmarks poco confiables (probablemente no eres tú)")
 
#             hombro = [lm_hombro.x, lm_hombro.y]
#             cadera = [lm_cadera.x, lm_cadera.y]
#             rodilla = [lm_rodilla.x, lm_rodilla.y]
#             tobillo = [lm_tobillo.x, lm_tobillo.y]
            
#             # Cálculo del ángulo crudo y filtro anti-teletransportes de MediaPipe antes de pasarlo al historial
#             angulo_crudo = self.calcular_angulo_3puntos(cadera, rodilla, tobillo)
 
#             if self.historial_rodilla:
#                 ultimo = self.historial_rodilla[-1]
#                 diferencia = angulo_crudo - ultimo
 
#                 if abs(diferencia) > 30:
#                         angulo_crudo = ultimo + np.sign(diferencia) * 30
                    
#             self.historial_rodilla.append(angulo_crudo)
#             angulo_rodilla = sum(self.historial_rodilla) / len(self.historial_rodilla)
            
#             # Normalización del ángulo de la espalda (mapea de 0° a 90° reales respecto a la vertical)
#             inclinacion_espalda = self.calcular_angulo_espalda(hombro, cadera)
#             if inclinacion_espalda > 90:
#                 inclinacion_espalda = 180 - inclinacion_espalda
                
#             print("ESPALDA:", round(inclinacion_espalda, 2))
#             print(f"Estado={self.estado} | Rodilla={angulo_rodilla:.1f}")
            
#             # 1. Lógica principal de estados y conteo
#             if angulo_rodilla > 120:
#                 self.frames_arriba += 1
#                 self.frames_abajo = 0
                
#                 if self.frames_arriba >= self.UMBRAL_ESTADO:
#                     if self.estado == "ABAJO":
#                         print("✅ REPETICION:", angulo_rodilla)
#                         self.contador += 1
 
#                         # Piernas ya estiradas, pero si la espalda TODAVÍA está muy
#                         # inclinada es que subiste la cadera antes que el pecho
#                         # (el clásico "good morning" hasta el final del movimiento).
#                         # OJO: usamos una frase DISTINTA a "Endereza" (el aviso que
#                         # ya suena mientras subes) para que no choque con su cooldown
#                         # de 3 segundos y termine sin decir nada.
#                         if inclinacion_espalda > 35:
#                             alerta = f"Rep {self.contador}: ¡Endereza la espalda!"
#                             color_alerta = (0, 0, 255)
#                             evento_voz = "Bien pero endereza la espalda"
#                         else:
#                             alerta = f"¡Bien hecho! ({self.contador})"
#                             evento_voz = f"Bien {self.contador}"
#                             color_alerta = (0, 255, 0)
#                     else:
#                         alerta = "Correcto: Baja"
#                         color_alerta = (0, 255, 0)
                    
#                     self.estado = "ARRIBA"
#                     # Terminó la repetición: limpiamos la línea base para la siguiente
#                     self.cadera_baseline = None
#                     self.hombro_baseline = None
                
#             elif angulo_rodilla <= 105:
#                 self.frames_abajo += 1
#                 self.frames_arriba = 0
                
#                 if self.frames_abajo >= self.UMBRAL_ESTADO:
#                     print("FONDO:", angulo_rodilla)
#                     self.estado = "ABAJO"
#                     alerta = "Buen fondo"
#                     color_alerta = (0, 255, 0)
#                     # Guardamos la posición de referencia del fondo (solo la primera vez
#                     # que se llega, para poder medir cuánto sube cada punto durante la subida)
#                     if self.cadera_baseline is None:
#                         self.cadera_baseline = cadera[1]
#                         self.hombro_baseline = hombro[1]
                
#             else:
#                 self.frames_abajo = 0
#                 self.frames_arriba = 0
#                 if self.estado == "ARRIBA":
#                     alerta = "Bajando..."
#                     color_alerta = (255, 255, 0)
#                 elif self.estado == "ABAJO":
#                     alerta = "Subiendo..."
#                     color_alerta = (0, 255, 255)
 
#             # 2. Validación de Cadera (Detector de levantamiento anticipado de cadera / "good morning")
#             # Comparamos cuánto ha subido la cadera vs cuánto ha subido el hombro desde
#             # el fondo de la sentadilla (en vez de frame-a-frame, que era muy ruidoso
#             # y solo miraba una ventana angular muy estrecha).
#             detecto_error_cadera_frame = False
#             if self.estado == "ABAJO" and self.cadera_baseline is not None and angulo_rodilla < 150:
#                 # Recuerda: en coordenadas de imagen, Y disminuye hacia arriba.
#                 subida_cadera = self.cadera_baseline - cadera[1]
#                 subida_hombro = self.hombro_baseline - hombro[1]
 
#                 if subida_cadera > self.SUBIDA_MINIMA and subida_cadera > subida_hombro + self.UMBRAL_DESFASE_CADERA:
#                     detecto_error_cadera_frame = True
 
#             # Filtro de persistencia para cadera
#             if detecto_error_cadera_frame:
#                 self.frames_error_cadera += 1
#                 if self.frames_error_cadera >= self.UMBRAL_FRAMES_ERROR and not self.cadera_reportada:
#                     alerta = "¡Cuidado con la cadera!"
#                     color_alerta = (0, 0, 255)
#                     evento_voz = "Cadera"  
#                     self.cadera_reportada = True
#             else:
#                 self.frames_error_cadera = max(0, self.frames_error_cadera - 1)
#                 if self.frames_error_cadera == 0:
#                     self.cadera_reportada = False
 
#             # 3. Validación de Espalda (Con umbral ajustado a 35° para mayor precisión técnica)
#             detecto_error_espalda_frame = (
#                 inclinacion_espalda > 35 
#                 and angulo_rodilla < 120 
#                 and self.estado == "ABAJO"
#             )
            
#             if detecto_error_espalda_frame:
#                 self.frames_error_espalda += 1
#                 if self.frames_error_espalda >= self.UMBRAL_FRAMES_ERROR and not self.espalda_reportada:
#                     if evento_voz is None:
#                         alerta = "¡Endereza la espalda!"
#                         color_alerta = (0, 0, 255)
#                         evento_voz = "Endereza"
#                     self.espalda_reportada = True
#             else:
#                 self.frames_error_espalda = max(0, self.frames_error_espalda - 1)
#                 if self.frames_error_espalda == 0:
#                     self.espalda_reportada = False
 
#             # Guardar posiciones actuales para el siguiente frame
#             self.hombro_anterior = hombro
#             self.cadera_anterior = cadera
            
#             return int(angulo_rodilla), self.contador, alerta, color_alerta, rodilla, evento_voz
            
#         except Exception as e:
#             self.hombro_anterior = None
#             self.cadera_anterior = None
#             self.historial_rodilla.clear()  # Limpieza del historial si se pierde el esqueleto de vista
#             self.lado_bloqueado = None  # Al recuperar la vista, se vuelve a elegir el mejor lado
#             return 0, self.contador, "Alineate con la camara", (0, 0, 255), [0, 0], None
 
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
 
class SquatAnalyzer:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.estado = "ARRIBA"
        self.contador = 0
        
        # Historial para suavizar el ángulo de la rodilla (ventana corta para no meter latencia extra)
        self.historial_rodilla = deque(maxlen=3)
        
        # Variables para rastrear el movimiento anterior (se mantienen por compatibilidad)
        self.hombro_anterior = None
        self.cadera_anterior = None
        
        # Línea base (posición de hombro/cadera en el fondo de la sentadilla).
        # El detector de "good morning" compara contra ESTA posición durante
        # toda la subida, en vez de comparar frame a frame (que es muy ruidoso).
        self.cadera_baseline = None
        self.hombro_baseline = None
        self.UMBRAL_DESFASE_CADERA = 0.05  # cuánto más debe subir la cadera vs el hombro para marcar error
        self.SUBIDA_MINIMA = 0.03          # movimiento mínimo para no disparar con ruido/quietud
 
        # Contadores de persistencia y umbrales para filtros (~300 ms)
        self.frames_error_cadera = 0
        self.frames_error_espalda = 0
        self.UMBRAL_FRAMES_ERROR = 2  
        
        # Contadores de estabilidad de estado (2 = necesita confirmación en 2 frames
        # seguidos antes de contar un cambio de estado; evita falsos conteos cuando
        # la malla pierde tracking por un instante y los puntos "brincan")
        self.frames_abajo = 0
        self.frames_arriba = 0
        self.UMBRAL_ESTADO = 2
        
        # Banderas para evitar bucles infinitos de voz
        self.cadera_reportada = False
        self.espalda_reportada = False
 
        # Qué lado del cuerpo (izquierdo o derecho) se está usando para medir.
        # Se elige automáticamente según cuál ve mejor la cámara y se mantiene
        # fijo durante el movimiento para no meter saltos.
        self.lado_bloqueado = None
 
        # ---- Sistema de precisión (0-100%) ----
        # Por cada repetición, contamos en cuántos frames del movimiento hubo
        # un error activo (cadera o espalda) contra el total de frames de esa
        # bajada. Con eso armamos un porcentaje en vivo, no solo bien/mal.
        self.frames_totales_rep = 0
        self.frames_error_cadera_rep = 0
        self.frames_error_espalda_rep = 0
        self.precision_actual = 100
        self.angulo_minimo_rep = 180
 
    def _elegir_landmarks(self, landmarks):
        """Elige el lado del cuerpo con mejor visibilidad para la cámara.
        Antes el código solo usaba el lado izquierdo, por eso de perfil total
        solo funcionaba si justo ese lado quedaba hacia la cámara."""
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
        # otro sea claramente mejor (evita que cambie de lado a media rep)
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
        
    def analizar(self, results):
        alerta = "Colócate de perfil"
        color_alerta = (255, 255, 255)
        evento_voz = None
        info_repeticion = None
        
        try:
            landmarks = results.pose_landmarks.landmark
            
            lm_hombro, lm_cadera, lm_rodilla, lm_tobillo = self._elegir_landmarks(landmarks)
 
            # MediaPipe SIEMPRE devuelve landmarks, incluso cuando lo que ve no es
            # realmente una persona (fondo, objetos, sombras). El campo `visibility`
            # indica qué tan seguro está el modelo de ese punto. Si es bajo, es ruido
            # y NO debe usarse para contar ni analizar la sentadilla.
            VISIBILIDAD_MINIMA = 0.6
            visibilidad_min = min(
                lm_hombro.visibility, lm_cadera.visibility,
                lm_rodilla.visibility, lm_tobillo.visibility
            )
            # Chequeo extra: si la malla completa (incluyendo manos/brazos) está
            # degradada en promedio, es señal de que el tracking general se está
            # perdiendo, aunque los 4 puntos que usamos todavía pasen el umbral.
            visibilidad_promedio_total = sum(lm.visibility for lm in landmarks) / len(landmarks)
 
            if visibilidad_min < VISIBILIDAD_MINIMA or visibilidad_promedio_total < 0.5:
                raise ValueError("Landmarks poco confiables (probablemente no eres tú)")
 
            hombro = [lm_hombro.x, lm_hombro.y]
            cadera = [lm_cadera.x, lm_cadera.y]
            rodilla = [lm_rodilla.x, lm_rodilla.y]
            tobillo = [lm_tobillo.x, lm_tobillo.y]
            
            # Cálculo del ángulo crudo y filtro anti-teletransportes de MediaPipe antes de pasarlo al historial
            angulo_crudo = self.calcular_angulo_3puntos(cadera, rodilla, tobillo)
 
            if self.historial_rodilla:
                ultimo = self.historial_rodilla[-1]
                diferencia = angulo_crudo - ultimo
 
                if abs(diferencia) > 30:
                        angulo_crudo = ultimo + np.sign(diferencia) * 30
                    
            self.historial_rodilla.append(angulo_crudo)
            angulo_rodilla = sum(self.historial_rodilla) / len(self.historial_rodilla)
 
            if angulo_rodilla < self.angulo_minimo_rep:
                self.angulo_minimo_rep = angulo_rodilla
            
            # Normalización del ángulo de la espalda (mapea de 0° a 90° reales respecto a la vertical)
            inclinacion_espalda = self.calcular_angulo_espalda(hombro, cadera)
            if inclinacion_espalda > 90:
                inclinacion_espalda = 180 - inclinacion_espalda
                
            print("ESPALDA:", round(inclinacion_espalda, 2))
            print(f"Estado={self.estado} | Rodilla={angulo_rodilla:.1f}")
            
            # 1. Lógica principal de estados y conteo
            if angulo_rodilla > 120:
                self.frames_arriba += 1
                self.frames_abajo = 0
                
                if self.frames_arriba >= self.UMBRAL_ESTADO:
                    if self.estado == "ABAJO":
                        print("✅ REPETICION:", angulo_rodilla)
                        self.contador += 1
 
                        # Piernas ya estiradas, pero si la espalda TODAVÍA está muy
                        # inclinada es que subiste la cadera antes que el pecho
                        # (el clásico "good morning" hasta el final del movimiento).
                        # OJO: usamos una frase DISTINTA a "Endereza" (el aviso que
                        # ya suena mientras subes) para que no choque con su cooldown
                        # de 3 segundos y termine sin decir nada.
                        if inclinacion_espalda > 35:
                            alerta = f"Rep {self.contador}: ¡Endereza la espalda!"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero endereza la espalda"
                        else:
                            alerta = f"¡Bien hecho! ({self.contador})"
                            evento_voz = f"Bien {self.contador}"
                            color_alerta = (0, 255, 0)
 
                        errores_rep = []
                        if self.frames_error_cadera_rep > 0:
                            errores_rep.append("cadera")
                        if self.frames_error_espalda_rep > 0:
                            errores_rep.append("espalda")
 
                        info_repeticion = {
                            "numero_rep": self.contador,
                            "angulo_minimo": int(self.angulo_minimo_rep),
                            "correcta": len(errores_rep) == 0,
                            "errores": errores_rep,
                            "precision": self.precision_actual,
                        }
                        self.angulo_minimo_rep = 180
                    else:
                        alerta = "Correcto: Baja"
                        color_alerta = (0, 255, 0)
                    
                    self.estado = "ARRIBA"
                    # Terminó la repetición: limpiamos la línea base para la siguiente
                    self.cadera_baseline = None
                    self.hombro_baseline = None
                
            elif angulo_rodilla <= 105:
                self.frames_abajo += 1
                self.frames_arriba = 0
                
                if self.frames_abajo >= self.UMBRAL_ESTADO:
                    print("FONDO:", angulo_rodilla)
                    self.estado = "ABAJO"
                    alerta = "Buen fondo"
                    color_alerta = (0, 255, 0)
                    # Guardamos la posición de referencia del fondo (solo la primera vez
                    # que se llega, para poder medir cuánto sube cada punto durante la subida)
                    if self.cadera_baseline is None:
                        self.cadera_baseline = cadera[1]
                        self.hombro_baseline = hombro[1]
                        self.frames_totales_rep = 0
                        self.frames_error_cadera_rep = 0
                        self.frames_error_espalda_rep = 0
                
            else:
                self.frames_abajo = 0
                self.frames_arriba = 0
                if self.estado == "ARRIBA":
                    alerta = "Bajando..."
                    color_alerta = (255, 255, 0)
                elif self.estado == "ABAJO":
                    alerta = "Subiendo..."
                    color_alerta = (0, 255, 255)
 
            # 2. Validación de Cadera (Detector de levantamiento anticipado de cadera / "good morning")
            # Comparamos cuánto ha subido la cadera vs cuánto ha subido el hombro desde
            # el fondo de la sentadilla (en vez de frame-a-frame, que era muy ruidoso
            # y solo miraba una ventana angular muy estrecha).
            detecto_error_cadera_frame = False
            if self.estado == "ABAJO" and self.cadera_baseline is not None and angulo_rodilla < 150:
                # Recuerda: en coordenadas de imagen, Y disminuye hacia arriba.
                subida_cadera = self.cadera_baseline - cadera[1]
                subida_hombro = self.hombro_baseline - hombro[1]
 
                if subida_cadera > self.SUBIDA_MINIMA and subida_cadera > subida_hombro + self.UMBRAL_DESFASE_CADERA:
                    detecto_error_cadera_frame = True
 
            # Filtro de persistencia para cadera
            if detecto_error_cadera_frame:
                self.frames_error_cadera += 1
                if self.frames_error_cadera >= self.UMBRAL_FRAMES_ERROR and not self.cadera_reportada:
                    alerta = "¡Cuidado con la cadera!"
                    color_alerta = (0, 0, 255)
                    evento_voz = "Cadera"  
                    self.cadera_reportada = True
            else:
                self.frames_error_cadera = max(0, self.frames_error_cadera - 1)
                if self.frames_error_cadera == 0:
                    self.cadera_reportada = False
 
            # 3. Validación de Espalda (Con umbral ajustado a 35° para mayor precisión técnica)
            detecto_error_espalda_frame = (
                inclinacion_espalda > 35 
                and angulo_rodilla < 120 
                and self.estado == "ABAJO"
            )
            
            if detecto_error_espalda_frame:
                self.frames_error_espalda += 1
                if self.frames_error_espalda >= self.UMBRAL_FRAMES_ERROR and not self.espalda_reportada:
                    if evento_voz is None:
                        alerta = "¡Endereza la espalda!"
                        color_alerta = (0, 0, 255)
                        evento_voz = "Endereza"
                    self.espalda_reportada = True
            else:
                self.frames_error_espalda = max(0, self.frames_error_espalda - 1)
                if self.frames_error_espalda == 0:
                    self.espalda_reportada = False
 
            # Guardar posiciones actuales para el siguiente frame
            self.hombro_anterior = hombro
            self.cadera_anterior = cadera
 
            # ---- Precisión en vivo ----
            # Contamos, mientras estás en la fase de bajada, en cuántos frames
            # hubo un error activo. Con eso armamos un % que se puede mostrar
            # en pantalla y guardar en la base de datos.
            if self.estado == "ABAJO":
                self.frames_totales_rep += 1
                if detecto_error_cadera_frame:
                    self.frames_error_cadera_rep += 1
                if detecto_error_espalda_frame:
                    self.frames_error_espalda_rep += 1
 
            if self.frames_totales_rep > 0:
                fraccion_cadera = self.frames_error_cadera_rep / self.frames_totales_rep
                fraccion_espalda = self.frames_error_espalda_rep / self.frames_totales_rep
                self.precision_actual = round(100 - 30 * fraccion_cadera - 30 * fraccion_espalda)
                self.precision_actual = max(0, min(100, self.precision_actual))
            else:
                self.precision_actual = 100
 
            return (int(angulo_rodilla), self.contador, alerta, color_alerta,
                    rodilla, evento_voz, info_repeticion, self.precision_actual)
            
        except Exception as e:
            self.hombro_anterior = None
            self.cadera_anterior = None
            self.historial_rodilla.clear()  # Limpieza del historial si se pierde el esqueleto de vista
            self.lado_bloqueado = None  # Al recuperar la vista, se vuelve a elegir el mejor lado
            return 0, self.contador, "Alineate con la camara", (0, 0, 255), [0, 0], None, None, self.precision_actual
 
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
 