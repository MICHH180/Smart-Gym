# import cv2
# import numpy as np
# import threading
# from pose_detector import PoseDetector
# from speaker import Speaker
# from lunge_analyzer import LungeAnalyzer
# from database import RegistroEntrenamiento
# import time
 
 
# class CamaraEnVivo:
#     """Lee la cámara en un hilo aparte y se queda solo con el frame más
#     reciente, para que el video no se vaya atrasando (mismo mecanismo
#     que en main.py de sentadillas)."""
 
#     def __init__(self, src=0):
#         self.cap = cv2.VideoCapture(src)
#         self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
 
#         self.lock = threading.Lock()
#         self.frame = None
#         self.ret = False
#         self.running = True
#         self.thread = threading.Thread(target=self._actualizar, daemon=True)
#         self.thread.start()
 
#     def _actualizar(self):
#         while self.running:
#             ret, frame = self.cap.read()
#             with self.lock:
#                 self.ret = ret
#                 self.frame = frame
 
#     def read(self):
#         with self.lock:
#             if self.frame is None:
#                 return False, None
#             return self.ret, self.frame.copy()
 
#     def isOpened(self):
#         return self.cap.isOpened()
 
#     def release(self):
#         self.running = False
#         self.thread.join(timeout=1)
#         self.cap.release()
 
 
# # Inicializar componentes
# # model_complexity=1 (en vez de 0): el desplante cruza/encima las piernas en
# # la imagen más que la sentadilla, y el modelo más ligero se confunde ahí.
# # Cuesta algo de velocidad, pero vale la pena para la precisión de piernas.
# detector = PoseDetector(model_complexity=1)
# speaker = Speaker()
# analyzer = LungeAnalyzer()
 
# # Base de datos: una sesión por corrida del programa
# registro = RegistroEntrenamiento()
# sesion_id = registro.iniciar_sesion("desplante")
 
# cap = CamaraEnVivo(0)
# print("Smart Gym - Módulo de Desplantes iniciado. Presiona 'ESC' para salir.")
 
# speaker.speak_unique("Prepárate. Da un paso para iniciar")
 
# while cap.isOpened():
#     success, frame = cap.read()
#     if not success:
#         time.sleep(0.01)
#         continue
 
#     frame = cv2.flip(frame, 1)
#     image, results = detector.procesar_frame(frame)
 
#     angulo, contador, alerta, color_alerta, rodilla, evento_voz, info_repeticion = analyzer.analizar(results)
 
#     # Cada vez que se cuenta una repetición nueva, se guarda en la base de datos
#     if info_repeticion:
#         registro.registrar_repeticion(
#             sesion_id,
#             numero_rep=info_repeticion["numero_rep"],
#             pierna=info_repeticion["pierna"],
#             angulo_minimo=info_repeticion["angulo_minimo"],
#             correcta=info_repeticion["correcta"],
#             errores=info_repeticion["errores"],
#         )
 
#     if evento_voz:
#         speaker.speak_unique(evento_voz)
 
#     if results.pose_landmarks:
#         cv2.putText(image, str(angulo),
#                     tuple(np.multiply(rodilla, [640, 480]).astype(int)),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
 
#     # Panel visual de estadísticas
#     cv2.rectangle(image, (0, 0), (640, 73), (245, 117, 16), -1)
 
#     cv2.putText(image, 'REPS', (15, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
#     cv2.putText(image, str(contador), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
 
#     cv2.putText(image, 'ESTADO', (130, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
#     cv2.putText(image, alerta, (130, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_alerta, 2, cv2.LINE_AA)
 
#     detector.dibujar_esqueleto(image, results)
 
#     cv2.imshow('Smart Gym - Desplantes en Vivo', image)
 
#     if cv2.waitKey(10) & 0xFF == 27:
#         break
 
# registro.cerrar_sesion(sesion_id)
# cap.release()
# cv2.destroyAllWindows()
 

import cv2
import numpy as np
import threading
from pose_detector import PoseDetector
from speaker import Speaker
from lunge_analyzer import LungeAnalyzer
from database import RegistroEntrenamiento
import time
 
 
class CamaraEnVivo:
    """Lee la cámara en un hilo aparte y se queda solo con el frame más
    reciente, para que el video no se vaya atrasando (mismo mecanismo
    que en main.py de sentadillas)."""
 
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
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
 
 
# Inicializar componentes
# model_complexity=1 (en vez de 0): el desplante cruza/encima las piernas en
# la imagen más que la sentadilla, y el modelo más ligero se confunde ahí.
# Cuesta algo de velocidad, pero vale la pena para la precisión de piernas.
detector = PoseDetector(model_complexity=1)
speaker = Speaker()
analyzer = LungeAnalyzer()
 
# Base de datos: una sesión por corrida del programa
registro = RegistroEntrenamiento()
sesion_id = registro.iniciar_sesion("desplante")
 
cap = CamaraEnVivo(0)
print("Smart Gym - Módulo de Desplantes iniciado. Presiona 'ESC' para salir.")
 
speaker.speak_unique("Prepárate. Da un paso para iniciar")
 
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        time.sleep(0.01)
        continue
 
    frame = cv2.flip(frame, 1)
    image, results = detector.procesar_frame(frame)
 
    angulo, contador, alerta, color_alerta, rodilla, evento_voz, info_repeticion, precision_actual = analyzer.analizar(results)
 
    # Cada vez que se cuenta una repetición nueva, se guarda en la base de datos
    if info_repeticion:
        registro.registrar_repeticion(
            sesion_id,
            numero_rep=info_repeticion["numero_rep"],
            pierna=info_repeticion["pierna"],
            angulo_minimo=info_repeticion["angulo_minimo"],
            correcta=info_repeticion["correcta"],
            errores=info_repeticion["errores"],
            precision=info_repeticion["precision"],
        )
 
    if evento_voz:
        speaker.speak_unique(evento_voz)
 
    if results.pose_landmarks:
        cv2.putText(image, str(angulo),
                    tuple(np.multiply(rodilla, [640, 480]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
 
    # Panel visual de estadísticas
    cv2.rectangle(image, (0, 0), (640, 73), (245, 117, 16), -1)
 
    cv2.putText(image, 'REPS', (15, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(image, str(contador), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
 
    cv2.putText(image, 'ESTADO', (130, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(image, alerta, (130, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_alerta, 2, cv2.LINE_AA)
 
    # Precisión en vivo (% del movimiento en buena forma en la bajada actual)
    color_precision = (0, 255, 0) if precision_actual >= 90 else (0, 255, 255) if precision_actual >= 70 else (0, 0, 255)
    cv2.putText(image, 'PRECISION', (420, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(image, f"{precision_actual}%", (420, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color_precision, 2, cv2.LINE_AA)
 
    detector.dibujar_esqueleto(image, results)
 
    cv2.imshow('Smart Gym - Desplantes en Vivo', image)
 
    if cv2.waitKey(10) & 0xFF == 27:
        break
 
registro.cerrar_sesion(sesion_id)
cap.release()
cv2.destroyAllWindows()
