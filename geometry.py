import numpy as np


def calcular_angulo_3puntos(a, b, c):
    """Calcula el ángulo entre tres puntos (ej. Cadera, Rodilla, Tobillo)."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radianes = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angulo = np.abs(radianes * 180.0 / np.pi)

    if angulo > 180.0:
        angulo = 360 - angulo

    return angulo


def calcular_angulo_respecto_vertical(punto_superior, punto_inferior):
    """Ángulo de un segmento (ej. hombro-cadera) respecto a la vertical que pasa por el punto inferior."""
    punto_superior = np.array(punto_superior)
    punto_inferior = np.array(punto_inferior)
    vertical = np.array([punto_inferior[0], punto_inferior[1] + 1.0])
    return calcular_angulo_3puntos(punto_superior, punto_inferior, vertical)
