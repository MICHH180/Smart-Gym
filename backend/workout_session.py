import sys
from pathlib import Path

# Los módulos core (pose_detector.py, squat_analyzer.py, etc.) viven en el directorio
# padre como scripts sueltos, sin estructura de paquete (__init__.py). Insertamos el
# padre en sys.path para poder importarlos sin tocar main.py ni reestructurar el core.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import cv2

from pose_detector import PoseDetector
from squat_analyzer import SquatAnalyzer


class WorkoutSession:
    """Encapsula el estado de UNA sesión de usuario (una conexión WebSocket).

    Cada instancia crea su propio PoseDetector y SquatAnalyzer para que el
    contador de repeticiones, el lado elegido y el form scorer no se compartan
    entre usuarios distintos.
    """

    def __init__(self):
        self.detector = PoseDetector(escala_inferencia=0.75)
        self.analyzer = SquatAnalyzer()

    def procesar_frame_bytes(self, frame_bytes: bytes) -> dict:
        """Decodifica un frame JPEG recibido por WebSocket y devuelve las
        métricas de la sentadilla como un dict serializable a JSON."""
        buffer = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

        _, results = self.detector.procesar_frame(frame)
        angulo, contador, alerta, color_alerta, _rodilla, evento_voz, form_score = self.analyzer.analizar(results)

        landmarks = None
        if results.pose_landmarks:
            landmarks = [{"x": lm.x, "y": lm.y} for lm in results.pose_landmarks.landmark]

        return {
            "angulo": angulo,
            "contador": contador,
            "alerta": alerta,
            # OpenCV (cv2.putText) usa el orden BGR internamente, pero el frontend
            # web interpreta arrays de color como RGB: invertimos la tupla aquí,
            # en el límite de la API, para que el contrato JSON sea honestamente RGB.
            "color_alerta": list(color_alerta)[::-1],
            "evento_voz": evento_voz,
            "form_score": form_score,
            "landmarks": landmarks,
        }
