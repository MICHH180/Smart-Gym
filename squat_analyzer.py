from geometry import calcular_angulo_3puntos, calcular_angulo_respecto_vertical
from exercise_analyzer import ExerciseAnalyzer
from form_validator import FormValidator
from form_scorer import FormScorer


class SquatAnalyzer(ExerciseAnalyzer):
    def __init__(self):
        super().__init__()
        self.form_validator = FormValidator()

    def puntos_visibilidad(self):
        return ["SHOULDER", "HIP", "KNEE", "ANKLE"]

    def extraer_puntos(self, landmarks, lado):
        hombro = [
            landmarks[self.mp_pose.PoseLandmark[f"{lado}_SHOULDER"].value].x,
            landmarks[self.mp_pose.PoseLandmark[f"{lado}_SHOULDER"].value].y,
        ]
        cadera = [
            landmarks[self.mp_pose.PoseLandmark[f"{lado}_HIP"].value].x,
            landmarks[self.mp_pose.PoseLandmark[f"{lado}_HIP"].value].y,
        ]
        rodilla = [
            landmarks[self.mp_pose.PoseLandmark[f"{lado}_KNEE"].value].x,
            landmarks[self.mp_pose.PoseLandmark[f"{lado}_KNEE"].value].y,
        ]
        tobillo = [
            landmarks[self.mp_pose.PoseLandmark[f"{lado}_ANKLE"].value].x,
            landmarks[self.mp_pose.PoseLandmark[f"{lado}_ANKLE"].value].y,
        ]
        return {"hombro": hombro, "cadera": cadera, "rodilla": rodilla, "tobillo": tobillo}

    def angulo_principal(self, puntos):
        return calcular_angulo_3puntos(puntos["cadera"], puntos["rodilla"], puntos["tobillo"])

    def punto_referencia(self, puntos):
        return puntos["rodilla"]

    def validar_forma(self, puntos, angulo_suavizado, estado):
        # Normalización del ángulo de la espalda (mapea de 0° a 90° reales respecto a la vertical)
        inclinacion_espalda = calcular_angulo_respecto_vertical(puntos["hombro"], puntos["cadera"])
        if inclinacion_espalda > 90:
            inclinacion_espalda = 180 - inclinacion_espalda

        alerta_ov, color_ov, evento_voz_ov = self.form_validator.validar(
            angulo_suavizado, inclinacion_espalda, estado, puntos["hombro"], puntos["cadera"]
        )
        return alerta_ov, color_ov, evento_voz_ov, inclinacion_espalda, evento_voz_ov == "Cadera"

    def crear_form_scorer(self):
        return FormScorer(
            desviacion_min=15,
            desviacion_max=FormValidator.INCLINACION_ESPALDA_MAX,
            penalizacion_max=40,
            penalizacion_secundaria=20,
        )

    def resetear_validacion(self):
        self.form_validator.reset()
