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

    def calcular_desviacion_secundaria(self, puntos):
        inclinacion_espalda = calcular_angulo_respecto_vertical(puntos["hombro"], puntos["cadera"])
        if inclinacion_espalda > 90:
            inclinacion_espalda = 180 - inclinacion_espalda
        return inclinacion_espalda

    def postura_valida_para_contar(self, angulo_principal_suavizado, desviacion_secundaria):
        # Si el torso se inclina más allá del umbral ya validado para la alerta
        # de espalda, congelamos el conteo — evita que un hip-hinge (doblar la
        # cintura sin flexionar la rodilla) se cuente como sentadilla, ya que el
        # ángulo 2D de rodilla puede leerse artificialmente bajo en ese caso.
        return desviacion_secundaria <= FormValidator.INCLINACION_ESPALDA_MAX

    def validar_forma(self, puntos, angulo_suavizado, estado, desviacion_secundaria, postura_valida):
        alerta_ov, color_ov, evento_voz_ov = self.form_validator.validar(
            angulo_suavizado, desviacion_secundaria, estado, puntos["hombro"], puntos["cadera"]
        )

        if not postura_valida and alerta_ov is None:
            # El gate de postura congeló el conteo, pero FormValidator no llegó a
            # marcarlo porque su condición exige estado=="ABAJO" (que nunca se
            # alcanza mientras el gate está activo). Reusamos el mismo aviso de
            # espalda para que el usuario reciba la corrección correcta en vez de
            # quedarse con el texto por defecto ("Colócate de perfil").
            alerta_ov = "¡Endereza la espalda!"
            color_ov = (0, 0, 255)
            evento_voz_ov = "Endereza"

        return alerta_ov, color_ov, evento_voz_ov, evento_voz_ov == "Cadera"

    def crear_form_scorer(self):
        return FormScorer(
            desviacion_min=15,
            desviacion_max=FormValidator.INCLINACION_ESPALDA_MAX,
            penalizacion_max=40,
            penalizacion_secundaria=20,
        )

    def resetear_validacion(self):
        self.form_validator.reset()
