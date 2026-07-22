import cv2
import numpy as np
from pose_detector import PoseDetector
from speaker import Speaker
from squat_analyzer import SquatAnalyzer
import time

# Inicializar componentes
detector = PoseDetector()
speaker = Speaker()
analyzer = SquatAnalyzer()

cap = cv2.VideoCapture(0)
print("Smart Gym - Módulo Modular de Sentadillas iniciado. Presiona 'ESC' para salir.")

# Mensaje de bienvenida inicial
speaker.speak_unique("Prepárate. Baja para iniciar")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    image, results = detector.procesar_frame(frame)

    # Analizar postura y obtener métricas a través del módulo escalable
    angulo, contador, alerta, color_alerta, rodilla, evento_voz = analyzer.analizar(results)

    if evento_voz:
        print(time.time(), "MAIN ->", evento_voz)
        speaker.speak_unique(evento_voz)

    if results.pose_landmarks:
        # Mostrar el ángulo numérico en la pantalla cerca de la rodilla
        cv2.putText(image, str(angulo), 
                       tuple(np.multiply(rodilla, [640, 480]).astype(int)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    # Dibujar panel visual de estadísticas en pantalla
    cv2.rectangle(image, (0, 0), (640, 73), (245, 117, 16), -1)
    
    # Texto de Repeticiones
    cv2.putText(image, 'REPS', (15, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(image, str(contador), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Texto de Alerta / Estado
    cv2.putText(image, 'ESTADO', (130, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(image, alerta, (130, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_alerta, 2, cv2.LINE_AA)

    # Dibujar malla de esqueleto encima
    detector.dibujar_esqueleto(image, results)

    cv2.imshow('Smart Gym - Sentadillas en Vivo', image)

    if cv2.waitKey(10) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
