import cv2
import mediapipe as mp
from geometry import calcular_angulo_3puntos

class PoseDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1, escala_inferencia=1.0):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.escala_inferencia = escala_inferencia
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=model_complexity
        )

    def procesar_frame(self, frame):
        """Convierte la imagen y procesa los landmarks corporales."""
        if self.escala_inferencia != 1.0:
            frame_inferencia = cv2.resize(frame, None, fx=self.escala_inferencia, fy=self.escala_inferencia, interpolation=cv2.INTER_LINEAR)
        else:
            frame_inferencia = frame

        # Los landmarks de MediaPipe son normalizados (0-1), por lo que siguen siendo
        # válidos sobre el frame original sin importar la resolución usada para inferir.
        image_rgb = cv2.cvtColor(frame_inferencia, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        return frame, results

    def calcular_angulo(self, a, b, c):
        """Calcula el ángulo entre tres puntos (ej. Cadera, Rodilla, Tobillo)."""
        return calcular_angulo_3puntos(a, b, c)

    def dibujar_esqueleto(self, image, results):
        """Dibuja la malla corporal sobre el frame."""
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
            )