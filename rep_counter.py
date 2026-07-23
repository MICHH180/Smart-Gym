import logging


class RepCounter:
    """Máquina de estados ARRIBA/ABAJO con debounce por persistencia de frames."""

    UMBRAL_RODILLA_ARRIBA = 130
    UMBRAL_RODILLA_ABAJO = 105
    UMBRAL_ESTADO = 3

    def __init__(self):
        self.estado = "ARRIBA"
        self.contador = 0
        self.frames_arriba = 0
        self.frames_abajo = 0

    def actualizar(self, angulo_rodilla_suavizado):
        alerta = None
        color_alerta = None
        se_completo_repeticion = False
        nueva_bajada = False

        if angulo_rodilla_suavizado > self.UMBRAL_RODILLA_ARRIBA:
            self.frames_arriba += 1
            self.frames_abajo = 0

            if self.frames_arriba >= self.UMBRAL_ESTADO:
                if self.estado == "ABAJO":
                    logging.debug("REPETICION: %s", angulo_rodilla_suavizado)
                    self.contador += 1
                    alerta = f"¡Bien hecho! ({self.contador})"
                    color_alerta = (0, 255, 0)
                    se_completo_repeticion = True
                else:
                    alerta = "Correcto: Baja"
                    color_alerta = (0, 255, 0)

                self.estado = "ARRIBA"

        elif angulo_rodilla_suavizado <= self.UMBRAL_RODILLA_ABAJO:
            self.frames_abajo += 1
            self.frames_arriba = 0

            if self.frames_abajo >= self.UMBRAL_ESTADO:
                logging.debug("FONDO: %s", angulo_rodilla_suavizado)
                if self.estado != "ABAJO":
                    nueva_bajada = True
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

        return self.estado, self.contador, alerta, color_alerta, se_completo_repeticion, nueva_bajada
