from collections import deque
import numpy as np
import mediapipe as mp
 
 
class CurlAnalyzer:
    """Analizador de Curl de Bíceps (ambos brazos a la vez, de frente a la cámara).
 
    Ángulo medido: hombro-codo-muñeca (en vez de cadera-rodilla-tobillo).
    Extendido ≈ 160-180°, contraído (arriba del curl) ≈ 30-50°.
 
    Errores de forma que vigila:
      - "Balanceo": el hombro se mueve para darle impulso al peso con el
        cuerpo en vez de con el bíceps (la típica "trampa" del curl).
      - "Codo despegado": el codo se adelanta o se abre en vez de quedarse
        fijo como bisagra pegado al torso.
 
    Ambos se miden comparando la posición ACTUAL de hombro/codo contra la
    posición que tenían justo antes de empezar a curvear (mientras el brazo
    está en reposo/extendido) -- el mismo principio de "línea base" que ya
    usamos para la cadera en sentadillas.
    """
 
    UMBRAL_EXTENDIDO = 155   # brazo casi recto = posición de reposo (para contar reps)
    UMBRAL_REPOSO_BASELINE = 172  # más estricto: solo aquí se actualiza la línea base,
                                   # para no "perseguir" al hombro/codo si ya empezaron
                                   # a moverse justo cuando arranca el curl
    UMBRAL_CONTRAIDO = 55    # brazo muy doblado = arriba del curl
    UMBRAL_DRIFT_CODO = 0.06     # cuánto se puede mover el codo antes de marcar error
    UMBRAL_DRIFT_HOMBRO = 0.035  # el hombro debería moverse aún menos que el codo
 
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.estado = "EXTENDIDO"
        self.contador = 0
 
        self.historial_izq = deque(maxlen=3)
        self.historial_der = deque(maxlen=3)
 
        self.frames_extendido = 0
        self.frames_contraido = 0
        self.UMBRAL_ESTADO = 2
 
        # Posición de "reposo" de hombro/codo, se actualiza en vivo mientras
        # el brazo está extendido y se congela en cuanto arranca el curl.
        self.hombro_reposo_izq = None
        self.hombro_reposo_der = None
        self.codo_reposo_izq = None
        self.codo_reposo_der = None
 
        self.frames_error_codo_rep = 0
        self.frames_error_hombro_rep = 0
        self.UMBRAL_FRAMES_ERROR = 2
        self.codo_reportado = False
        self.hombro_reportado = False
 
        # ---- Precisión (0-100%) ----
        self.frames_totales_rep = 0
        self.frames_error_codo_precision = 0
        self.frames_error_hombro_precision = 0
        self.precision_actual = 100
        self.angulo_minimo_rep = 180
 
    # ------------------------------------------------------------
    def analizar(self, results):
        alerta = "Colócate de frente"
        color_alerta = (255, 255, 255)
        evento_voz = None
        info_repeticion = None
 
        try:
            landmarks = results.pose_landmarks.landmark
            lm = self.mp_pose.PoseLandmark
 
            lm_hombro_izq = landmarks[lm.LEFT_SHOULDER.value]
            lm_codo_izq = landmarks[lm.LEFT_ELBOW.value]
            lm_muneca_izq = landmarks[lm.LEFT_WRIST.value]
            lm_hombro_der = landmarks[lm.RIGHT_SHOULDER.value]
            lm_codo_der = landmarks[lm.RIGHT_ELBOW.value]
            lm_muneca_der = landmarks[lm.RIGHT_WRIST.value]
 
            VISIBILIDAD_MINIMA = 0.6
            visibilidad_min = min(
                lm_hombro_izq.visibility, lm_codo_izq.visibility, lm_muneca_izq.visibility,
                lm_hombro_der.visibility, lm_codo_der.visibility, lm_muneca_der.visibility,
            )
            visibilidad_promedio_total = sum(l.visibility for l in landmarks) / len(landmarks)
 
            if visibilidad_min < VISIBILIDAD_MINIMA or visibilidad_promedio_total < 0.5:
                raise ValueError("Landmarks poco confiables (probablemente no eres tú)")
 
            # De perfil los dos hombros casi se encimarían en X; de frente
            # quedan bien separados. Este chequeo evita analizar de perfil.
            separacion_hombros = abs(lm_hombro_izq.x - lm_hombro_der.x)
            if separacion_hombros < 0.12:
                return (0, self.contador, "Ponte de frente a la cámara",
                        (255, 255, 0), [0, 0], None, None, self.precision_actual)
 
            hombro_izq = [lm_hombro_izq.x, lm_hombro_izq.y]
            codo_izq = [lm_codo_izq.x, lm_codo_izq.y]
            muneca_izq = [lm_muneca_izq.x, lm_muneca_izq.y]
            hombro_der = [lm_hombro_der.x, lm_hombro_der.y]
            codo_der = [lm_codo_der.x, lm_codo_der.y]
            muneca_der = [lm_muneca_der.x, lm_muneca_der.y]
 
            # Ángulo de cada brazo, suavizado
            self.historial_izq.append(self.calcular_angulo_3puntos(hombro_izq, codo_izq, muneca_izq))
            self.historial_der.append(self.calcular_angulo_3puntos(hombro_der, codo_der, muneca_der))
            angulo_izq = sum(self.historial_izq) / len(self.historial_izq)
            angulo_der = sum(self.historial_der) / len(self.historial_der)
            angulo_prom = (angulo_izq + angulo_der) / 2
 
            if angulo_prom < self.angulo_minimo_rep:
                self.angulo_minimo_rep = angulo_prom
 
            # Mientras el brazo está en reposo (extendido), vamos actualizando
            # la posición "normal" de hombro y codo. En cuanto arranca el
            # curl, esta posición se queda congelada como referencia.
            # OJO: usamos el ángulo directo (no self.estado) porque el estado
            # tiene un pequeño debounce de frames y se quedaría "pegado" en
            # EXTENDIDO durante parte de la subida, dejando que la base siga
            # persiguiendo al hombro justo cuando más importa congelarla.
            if angulo_prom > self.UMBRAL_REPOSO_BASELINE:
                self.hombro_reposo_izq = hombro_izq
                self.hombro_reposo_der = hombro_der
                self.codo_reposo_izq = codo_izq
                self.codo_reposo_der = codo_der
 
            # 1. Estado y conteo
            if angulo_prom > self.UMBRAL_EXTENDIDO:
                self.frames_extendido += 1
                self.frames_contraido = 0
 
                if self.frames_extendido >= self.UMBRAL_ESTADO:
                    if self.estado == "CONTRAIDO":
                        self.contador += 1
 
                        errores_rep = []
                        if self.frames_error_codo_rep > 0:
                            errores_rep.append("codo")
                        if self.frames_error_hombro_rep > 0:
                            errores_rep.append("hombro")
 
                        if "codo" in errores_rep:
                            alerta = f"Rep {self.contador}: ¡Fija el codo!"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero fija el codo"
                        elif "hombro" in errores_rep:
                            alerta = f"Rep {self.contador}: ¡No balancees!"
                            color_alerta = (0, 0, 255)
                            evento_voz = "Bien pero no balancees"
                        else:
                            alerta = f"¡Bien hecho! ({self.contador})"
                            evento_voz = f"Bien {self.contador}"
                            color_alerta = (0, 255, 0)
 
                        info_repeticion = {
                            "numero_rep": self.contador,
                            "angulo_minimo": int(self.angulo_minimo_rep),
                            "correcta": len(errores_rep) == 0,
                            "errores": errores_rep,
                            "precision": self.precision_actual,
                        }
                        self.angulo_minimo_rep = 180
                        self.frames_totales_rep = 0
                        self.frames_error_codo_precision = 0
                        self.frames_error_hombro_precision = 0
                    else:
                        alerta = "Listo, sube"
                        color_alerta = (0, 255, 0)
 
                    self.estado = "EXTENDIDO"
                    self.frames_error_codo_rep = 0
                    self.frames_error_hombro_rep = 0
 
            elif angulo_prom < self.UMBRAL_CONTRAIDO:
                self.frames_contraido += 1
                self.frames_extendido = 0
 
                if self.frames_contraido >= self.UMBRAL_ESTADO:
                    self.estado = "CONTRAIDO"
                    alerta = "Buena contracción"
                    color_alerta = (0, 255, 0)
 
            else:
                self.frames_extendido = 0
                self.frames_contraido = 0
                if self.estado == "EXTENDIDO":
                    alerta = "Subiendo..."
                    color_alerta = (255, 255, 0)
                else:
                    alerta = "Bajando..."
                    color_alerta = (0, 255, 255)
 
            # 2. Validación de codo despegado (comparado contra su posición de reposo)
            detecto_error_codo_frame = False
            if angulo_prom <= self.UMBRAL_EXTENDIDO and self.codo_reposo_izq is not None:
                drift_izq = np.linalg.norm(np.array(codo_izq) - np.array(self.codo_reposo_izq))
                drift_der = np.linalg.norm(np.array(codo_der) - np.array(self.codo_reposo_der))
                if drift_izq > self.UMBRAL_DRIFT_CODO or drift_der > self.UMBRAL_DRIFT_CODO:
                    detecto_error_codo_frame = True
 
            if detecto_error_codo_frame:
                self.frames_error_codo_rep += 1
                if self.frames_error_codo_rep >= self.UMBRAL_FRAMES_ERROR and not self.codo_reportado:
                    alerta = "¡Fija el codo!"
                    color_alerta = (0, 0, 255)
                    evento_voz = "Codo"
                    self.codo_reportado = True
            else:
                if self.frames_error_codo_rep == 0:
                    self.codo_reportado = False
 
            # 3. Validación de balanceo de hombro
            detecto_error_hombro_frame = False
            if angulo_prom <= self.UMBRAL_EXTENDIDO and self.hombro_reposo_izq is not None:
                drift_h_izq = np.linalg.norm(np.array(hombro_izq) - np.array(self.hombro_reposo_izq))
                drift_h_der = np.linalg.norm(np.array(hombro_der) - np.array(self.hombro_reposo_der))
                if drift_h_izq > self.UMBRAL_DRIFT_HOMBRO or drift_h_der > self.UMBRAL_DRIFT_HOMBRO:
                    detecto_error_hombro_frame = True
 
            if detecto_error_hombro_frame:
                self.frames_error_hombro_rep += 1
                if self.frames_error_hombro_rep >= self.UMBRAL_FRAMES_ERROR and not self.hombro_reportado:
                    if evento_voz is None:
                        alerta = "¡No balancees el cuerpo!"
                        color_alerta = (0, 0, 255)
                        evento_voz = "Hombro"
                    self.hombro_reportado = True
            else:
                if self.frames_error_hombro_rep == 0:
                    self.hombro_reportado = False
 
            # ---- Precisión en vivo ----
            if angulo_prom <= self.UMBRAL_EXTENDIDO:
                self.frames_totales_rep += 1
                if detecto_error_codo_frame:
                    self.frames_error_codo_precision += 1
                if detecto_error_hombro_frame:
                    self.frames_error_hombro_precision += 1
 
            if self.frames_totales_rep > 0:
                fraccion_codo = self.frames_error_codo_precision / self.frames_totales_rep
                fraccion_hombro = self.frames_error_hombro_precision / self.frames_totales_rep
                self.precision_actual = round(100 - 30 * fraccion_codo - 30 * fraccion_hombro)
                self.precision_actual = max(0, min(100, self.precision_actual))
            else:
                self.precision_actual = 100
 
            # Usamos el codo izquierdo para ubicar el número de ángulo en pantalla
            return (int(angulo_prom), self.contador, alerta, color_alerta,
                    codo_izq, evento_voz, info_repeticion, self.precision_actual)
 
        except Exception:
            self.historial_izq.clear()
            self.historial_der.clear()
            self.hombro_reposo_izq = None
            self.hombro_reposo_der = None
            self.codo_reposo_izq = None
            self.codo_reposo_der = None
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
 