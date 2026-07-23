class FormValidator:
    """Validaciones secundarias de técnica: levantamiento anticipado de cadera y encorvamiento de espalda."""

    UMBRAL_FRAMES_ERROR = 2

    # Validación de cadera (Efecto Good Morning: la cadera sube antes que el torso)
    RODILLA_MIN_CADERA = 100
    RODILLA_MAX_CADERA = 130
    DELTA_CADERA_HOMBRO = 0.008

    # Validación de espalda
    INCLINACION_ESPALDA_MAX = 35
    RODILLA_MAX_ESPALDA = 120

    def __init__(self):
        self.hombro_anterior = None
        self.cadera_anterior = None

        self.frames_error_cadera = 0
        self.frames_error_espalda = 0

        self.cadera_reportada = False
        self.espalda_reportada = False

    def validar(self, angulo_rodilla, inclinacion_espalda, estado, hombro, cadera):
        alerta_override = None
        color_override = None
        evento_voz = None

        # 1. Validación de Cadera (Detector de levantamiento anticipado de cadera)
        detecto_error_cadera_frame = False
        if self.hombro_anterior is not None and self.cadera_anterior is not None:
            delta_y_hombro = hombro[1] - self.hombro_anterior[1]
            delta_y_cadera = cadera[1] - self.cadera_anterior[1]

            if self.RODILLA_MIN_CADERA < angulo_rodilla < self.RODILLA_MAX_CADERA:
                if delta_y_cadera < delta_y_hombro - self.DELTA_CADERA_HOMBRO:
                    detecto_error_cadera_frame = True

        if detecto_error_cadera_frame:
            self.frames_error_cadera += 1
            if self.frames_error_cadera >= self.UMBRAL_FRAMES_ERROR and not self.cadera_reportada:
                alerta_override = "¡Cuidado con la cadera!"
                color_override = (0, 0, 255)
                evento_voz = "Cadera"
                self.cadera_reportada = True
        else:
            self.frames_error_cadera = max(0, self.frames_error_cadera - 1)
            if self.frames_error_cadera == 0:
                self.cadera_reportada = False

        # 2. Validación de Espalda (Con umbral ajustado a 35° para mayor precisión técnica)
        detecto_error_espalda_frame = (
            inclinacion_espalda > self.INCLINACION_ESPALDA_MAX
            and angulo_rodilla < self.RODILLA_MAX_ESPALDA
            and estado == "ABAJO"
        )

        if detecto_error_espalda_frame:
            self.frames_error_espalda += 1
            if self.frames_error_espalda >= self.UMBRAL_FRAMES_ERROR and not self.espalda_reportada:
                if evento_voz is None:
                    alerta_override = "¡Endereza la espalda!"
                    color_override = (0, 0, 255)
                    evento_voz = "Endereza"
                self.espalda_reportada = True
        else:
            self.frames_error_espalda = max(0, self.frames_error_espalda - 1)
            if self.frames_error_espalda == 0:
                self.espalda_reportada = False

        # Guardar posiciones actuales para el siguiente frame
        self.hombro_anterior = hombro
        self.cadera_anterior = cadera

        return alerta_override, color_override, evento_voz

    def reset(self):
        self.hombro_anterior = None
        self.cadera_anterior = None
