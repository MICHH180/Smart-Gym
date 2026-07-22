import cv2
import numpy as np
import mediapipe as mp

class PoseDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_confidence, 
            min_tracking_confidence=min_tracking_confidence
        )

    def procesar_frame(self, frame):
        """Convierte la imagen y procesa los landmarks corporales."""
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = self.pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image, results

    def calcular_angulo(self, a, b, c):
        """Calcula el ángulo entre tres puntos (ej. Cadera, Rodilla, Tobillo)."""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radianes = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angulo = np.abs(radianes * 180.0 / np.pi)
        
        if angulo > 180.0:
            angulo = 360 - angulo
            
        return angulo

    def dibujar_esqueleto(self, image, results):
        """Dibuja la malla corporal sobre el frame."""
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
            )