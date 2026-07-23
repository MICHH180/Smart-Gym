class FormScorer:
    """Calcula un puntaje de técnica (0-100) por cada repetición completada,
    en base a la desviación máxima de una métrica de forma secundaria y a si
    hubo (o no) una falla puntual durante la repetición. Los umbrales y
    penalizaciones son específicos de cada ejercicio y los provee quien
    instancia la clase."""

    def __init__(self, desviacion_min, desviacion_max, penalizacion_max, penalizacion_secundaria):
        self.desviacion_min = desviacion_min
        self.desviacion_max = desviacion_max
        self.penalizacion_max = penalizacion_max
        self.penalizacion_secundaria = penalizacion_secundaria

        self.max_desviacion_rep = 0
        self.hubo_falla_secundaria_rep = False

    def iniciar_repeticion(self):
        self.max_desviacion_rep = 0
        self.hubo_falla_secundaria_rep = False

    def actualizar(self, desviacion_forma, estado, hubo_falla_secundaria):
        if estado == "ABAJO":
            if desviacion_forma > self.max_desviacion_rep:
                self.max_desviacion_rep = desviacion_forma

        if hubo_falla_secundaria:
            self.hubo_falla_secundaria_rep = True

    def finalizar_repeticion(self):
        rango = self.desviacion_max - self.desviacion_min
        exceso = self.max_desviacion_rep - self.desviacion_min
        penalizacion_desviacion = (exceso / rango) * self.penalizacion_max
        penalizacion_desviacion = min(max(penalizacion_desviacion, 0), self.penalizacion_max)

        penalizacion_secundaria = self.penalizacion_secundaria if self.hubo_falla_secundaria_rep else 0

        puntaje = 100 - penalizacion_desviacion - penalizacion_secundaria
        puntaje = min(max(puntaje, 0), 100)

        return round(puntaje)
