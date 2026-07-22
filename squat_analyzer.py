
# import numpy as np
# import mediapipe as mp

# class SquatAnalyzer:
#     def __init__(self):
#         self.mp_pose = mp.solutions.pose
#         self.estado = "ARRIBA"
#         self.contador = 0
        
#     def analizar(self, results):
#         alerta = "Colócate de perfil"
#         color_alerta = (255, 255, 255)
#         evento_voz = None
        
#         try:
#             landmarks = results.pose_landmarks.landmark
            
#             hombro = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
#             cadera = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
#             rodilla = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
#             tobillo = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            
#             angulo_rodilla = self.calcular_angulo_3puntos(cadera, rodilla, tobillo)
#             inclinacion_espalda = self.calcular_angulo_espalda(hombro, cadera)
            
#             # 1. Lógica principal de estados y conteo (La rodilla manda para que siempre cuente)
#             if angulo_rodilla > 130:
#                 if self.estado == "ABAJO":
#                     self.contador += 1
#                     alerta = f"¡Bien hecho! ({self.contador})"
#                     evento_voz = f"Bien {self.contador}"
#                     color_alerta = (0, 255, 0)
#                 else:
#                     alerta = "Correcto: Baja"
#                     color_alerta = (0, 255, 0)
                
#                 self.estado = "ARRIBA"
                
#             elif angulo_rodilla <= 95:
#                 self.estado = "ABAJO"
#                 alerta = "Buen fondo"
#                 color_alerta = (0, 255, 0)
                
#             else:
#                 if self.estado == "ARRIBA":
#                     alerta = "Bajando..."
#                     color_alerta = (255, 255, 0)
#                 elif self.estado == "ABAJO":
#                     alerta = "Subiendo..."
#                     color_alerta = (0, 255, 255)

#             # 2. Validación secundaria de espalda (Si te encorvas, pisa la alerta visual pero no bloquea el conteo)
#             # if inclinacion_espalda > 45 and angulo_rodilla < 120:
#             #     alerta = "¡Endereza la espalda!"
#             #     color_alerta = (0, 0, 255)
#             #     evento_voz = "Endereza la espalda"

#             # # Dentro de tu método analizar(), puedes agregar esta regla de validación de cadera:

#             # # 3. Validación de cadera (Efecto Good Morning: la cadera sube antes que el torso)
#             # # Evaluamos si la cadera se eleva desproporcionadamente mientras estamos en fase de subida
#             # if self.estado == "ABAJO" and angulo_rodilla > 100 and angulo_rodilla < 140:
#             #     # Comparamos la elevación de la cadera con respecto al hombro
#             #     # (Recuerda que en el plano de MediaPipe, Y disminuye conforme sube en la pantalla)
#             #     diferencia_vertical = hombro[1] - cadera[1]
                
#             #     # Si la cadera sube demasiado abruptamente rompiendo la sincronía con el torso
#             #     if diferencia_vertical < 0.15: # Este umbral lo puedes ajustar según tus pruebas en vivo
#             #         alerta = "¡Cuidado con la cadera! No la subas antes"
#             #         color_alerta = (0, 0, 255)
#             #         evento_voz = "Sube el pecho" # O "Cadera abajo"

#             if 100 < angulo_rodilla < 130:
#                 diferencia_vertical = hombro[1] - cadera[1]

#                 if diferencia_vertical < 0.10:
#                     alerta = "¡Cuidado con la cadera! No la subas antes"
#                     color_alerta = (0, 0, 255)
#                     evento_voz = "Cuidado con la cadera"

#             # ----------------------------
#             # VALIDACIÓN DE ESPALDA
#             # ----------------------------
#             elif inclinacion_espalda > 45 and angulo_rodilla < 120:
#                 alerta = "¡Endereza la espalda!"
#                 color_alerta = (0, 0, 255)
#                 evento_voz = "Endereza la espalda"

#             return int(angulo_rodilla), self.contador, alerta, color_alerta, rodilla, evento_voz

#         except Exception as e:
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
        
        # Historial para suavizar el ángulo de la rodilla
        self.historial_rodilla = deque(maxlen=5)
        
        # Variables para rastrear el movimiento anterior (Detector de levantamiento anticipado de cadera)
        self.hombro_anterior = None
        self.cadera_anterior = None
        
        # Contadores de persistencia y umbrales para filtros (~300 ms)
        self.frames_error_cadera = 0
        self.frames_error_espalda = 0
        self.UMBRAL_FRAMES_ERROR = 2  
        
        # Contadores de estabilidad de estado
        self.frames_abajo = 0
        self.frames_arriba = 0
        self.UMBRAL_ESTADO = 3
        
        # Banderas para evitar bucles infinitos de voz
        self.cadera_reportada = False
        self.espalda_reportada = False
        
    def analizar(self, results):
        alerta = "Colócate de perfil"
        color_alerta = (255, 255, 255)
        evento_voz = None
        
        try:
            landmarks = results.pose_landmarks.landmark
            
            hombro = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            cadera = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
            rodilla = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            tobillo = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            
            # Cálculo del ángulo crudo y filtro anti-teletransportes de MediaPipe antes de pasarlo al historial
            angulo_crudo = self.calcular_angulo_3puntos(cadera, rodilla, tobillo)

            if self.historial_rodilla:
                ultimo = self.historial_rodilla[-1]
                diferencia = angulo_crudo - ultimo

                if abs(diferencia) > 30:
                        angulo_crudo = ultimo + np.sign(diferencia) * 30
                    
            self.historial_rodilla.append(angulo_crudo)
            angulo_rodilla = sum(self.historial_rodilla) / len(self.historial_rodilla)
            
            # Normalización del ángulo de la espalda (mapea de 0° a 90° reales respecto a la vertical)
            inclinacion_espalda = self.calcular_angulo_espalda(hombro, cadera)
            if inclinacion_espalda > 90:
                inclinacion_espalda = 180 - inclinacion_espalda
                
            print("ESPALDA:", round(inclinacion_espalda, 2))
            print(f"Estado={self.estado} | Rodilla={angulo_rodilla:.1f}")
            
            # 1. Lógica principal de estados y conteo
            if angulo_rodilla > 130:
                self.frames_arriba += 1
                self.frames_abajo = 0
                
                if self.frames_arriba >= self.UMBRAL_ESTADO:
                    if self.estado == "ABAJO":
                        print("✅ REPETICION:", angulo_rodilla)
                        self.contador += 1
                        alerta = f"¡Bien hecho! ({self.contador})"
                        evento_voz = f"Bien {self.contador}"
                        color_alerta = (0, 255, 0)
                    else:
                        alerta = "Correcto: Baja"
                        color_alerta = (0, 255, 0)
                    
                    self.estado = "ARRIBA"
                
            elif angulo_rodilla <= 105:
                self.frames_abajo += 1
                self.frames_arriba = 0
                
                if self.frames_abajo >= self.UMBRAL_ESTADO:
                    print("FONDO:", angulo_rodilla)
                    self.estado = "ABAJO"
                    alerta = "Buen fondo"
                    color_alerta = (0, 255, 0)
                
            else:
                self.frames_abajo = 0
                self.frames_arriba = 0
                if self.estado == "ARRIBA":
                    alerta = "Bajando..."
                    color_alerta = (255, 255, 0)
                elif self.estado == "ABAJO":
                    alerta = "Subiendo..."
                    color_alerta = (0, 255, 255)

            # 2. Validación de Cadera (Detector de levantamiento anticipado de cadera)
            detecto_error_cadera_frame = False
            if self.hombro_anterior is not None and self.cadera_anterior is not None:
                delta_y_hombro = hombro[1] - self.hombro_anterior[1]
                delta_y_cadera = cadera[1] - self.cadera_anterior[1]
                
                if 100 < angulo_rodilla < 130:
                    if delta_y_cadera < delta_y_hombro - 0.008:
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
            
            return int(angulo_rodilla), self.contador, alerta, color_alerta, rodilla, evento_voz
            
        except Exception as e:
            self.hombro_anterior = None
            self.cadera_anterior = None
            self.historial_rodilla.clear()  # Limpieza del historial si se pierde el esqueleto de vista
            return 0, self.contador, "Alineate con la camara", (0, 0, 255), [0, 0], None

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
