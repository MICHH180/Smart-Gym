# """
# Capa de persistencia local con SQLite para Smart Gym.
 
# Diseñada para ser genérica: sirve tanto para sentadillas como para
# desplantes (o cualquier ejercicio futuro), guardando sesiones y
# repeticiones individuales con fecha, para poder construir una UI
# encima (historial, gráficas de progreso, racha de días, etc.).
 
# Esquema:
 
#   sesiones
#     id             INTEGER PK
#     ejercicio      TEXT      ("sentadilla", "desplante", ...)
#     fecha_inicio   TEXT      (ISO 8601)
#     fecha_fin      TEXT      (ISO 8601, NULL mientras la sesión sigue activa)
 
#   repeticiones
#     id             INTEGER PK
#     sesion_id      INTEGER   (FK -> sesiones.id)
#     numero_rep     INTEGER   (1, 2, 3... dentro de esa sesión)
#     timestamp      TEXT      (ISO 8601, momento exacto de la repetición)
#     pierna         TEXT      ("izquierda" / "derecha" / NULL si no aplica)
#     angulo_minimo  INTEGER   (qué tan profundo llegó, útil para calidad)
#     correcta       INTEGER   (1 = sin errores de forma, 0 = con errores)
#     errores        TEXT      (lista separada por comas: "cadera,espalda", o NULL)
# """
 
# import sqlite3
# import os
# from datetime import datetime
 
 
# class RegistroEntrenamiento:
#     def __init__(self, ruta_db=None):
#         if ruta_db is None:
#             ruta_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart_gym.db")
#         self.ruta_db = ruta_db
#         self._crear_tablas()
 
#     def _conectar(self):
#         # check_same_thread=False porque en main.py se puede llamar desde
#         # el hilo principal sin problema, pero lo dejamos flexible.
#         return sqlite3.connect(self.ruta_db, check_same_thread=False)
 
#     def _crear_tablas(self):
#         con = self._conectar()
#         cur = con.cursor()
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS sesiones (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 ejercicio TEXT NOT NULL,
#                 fecha_inicio TEXT NOT NULL,
#                 fecha_fin TEXT
#             )
#         """)
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS repeticiones (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sesion_id INTEGER NOT NULL,
#                 numero_rep INTEGER NOT NULL,
#                 timestamp TEXT NOT NULL,
#                 pierna TEXT,
#                 angulo_minimo INTEGER,
#                 correcta INTEGER NOT NULL,
#                 errores TEXT,
#                 FOREIGN KEY (sesion_id) REFERENCES sesiones (id)
#             )
#         """)
#         con.commit()
#         con.close()
 
#     # ------------------------------------------------------------
#     # Escritura
#     # ------------------------------------------------------------
#     def iniciar_sesion(self, ejercicio):
#         """Crea una nueva sesión (se llama una vez al arrancar el programa).
#         Devuelve el id de la sesión para usarlo en registrar_repeticion()."""
#         con = self._conectar()
#         cur = con.cursor()
#         cur.execute(
#             "INSERT INTO sesiones (ejercicio, fecha_inicio) VALUES (?, ?)",
#             (ejercicio, datetime.now().isoformat())
#         )
#         sesion_id = cur.lastrowid
#         con.commit()
#         con.close()
#         return sesion_id
 
#     def registrar_repeticion(self, sesion_id, numero_rep, pierna=None,
#                               angulo_minimo=None, correcta=True, errores=None):
#         """Guarda una repetición individual. `errores` puede ser una lista
#         de strings (ej. ["cadera", "espalda"]) o None."""
#         errores_str = ",".join(errores) if errores else None
#         con = self._conectar()
#         cur = con.cursor()
#         cur.execute(
#             """INSERT INTO repeticiones
#                (sesion_id, numero_rep, timestamp, pierna, angulo_minimo, correcta, errores)
#                VALUES (?, ?, ?, ?, ?, ?, ?)""",
#             (sesion_id, numero_rep, datetime.now().isoformat(),
#              pierna, angulo_minimo, 1 if correcta else 0, errores_str)
#         )
#         con.commit()
#         con.close()
 
#     def cerrar_sesion(self, sesion_id):
#         """Marca la sesión como terminada (llamar al salir del programa)."""
#         con = self._conectar()
#         cur = con.cursor()
#         cur.execute(
#             "UPDATE sesiones SET fecha_fin = ? WHERE id = ?",
#             (datetime.now().isoformat(), sesion_id)
#         )
#         con.commit()
#         con.close()
 
#     # ------------------------------------------------------------
#     # Lectura (para cuando se construya la UI)
#     # ------------------------------------------------------------
#     def obtener_sesiones(self, ejercicio=None, limite=50):
#         con = self._conectar()
#         cur = con.cursor()
#         if ejercicio:
#             cur.execute(
#                 "SELECT * FROM sesiones WHERE ejercicio = ? ORDER BY fecha_inicio DESC LIMIT ?",
#                 (ejercicio, limite)
#             )
#         else:
#             cur.execute("SELECT * FROM sesiones ORDER BY fecha_inicio DESC LIMIT ?", (limite,))
#         filas = cur.fetchall()
#         con.close()
#         return filas
 
#     def obtener_repeticiones_de_sesion(self, sesion_id):
#         con = self._conectar()
#         cur = con.cursor()
#         cur.execute(
#             "SELECT * FROM repeticiones WHERE sesion_id = ? ORDER BY numero_rep ASC",
#             (sesion_id,)
#         )
#         filas = cur.fetchall()
#         con.close()
#         return filas
 
#     def obtener_resumen_por_dia(self, ejercicio=None):
#         """Total de repeticiones por día (para una gráfica de progreso en la UI)."""
#         con = self._conectar()
#         cur = con.cursor()
#         if ejercicio:
#             cur.execute("""
#                 SELECT date(r.timestamp) as dia, COUNT(*) as total,
#                        SUM(r.correcta) as correctas
#                 FROM repeticiones r
#                 JOIN sesiones s ON r.sesion_id = s.id
#                 WHERE s.ejercicio = ?
#                 GROUP BY dia
#                 ORDER BY dia DESC
#             """, (ejercicio,))
#         else:
#             cur.execute("""
#                 SELECT date(timestamp) as dia, COUNT(*) as total,
#                        SUM(correcta) as correctas
#                 FROM repeticiones
#                 GROUP BY dia
#                 ORDER BY dia DESC
#             """)
#         filas = cur.fetchall()
#         con.close()
#         return filas


"""
Capa de persistencia local con SQLite para Smart Gym.
 
Diseñada para ser genérica: sirve tanto para sentadillas como para
desplantes (o cualquier ejercicio futuro), guardando sesiones y
repeticiones individuales con fecha, para poder construir una UI
encima (historial, gráficas de progreso, racha de días, etc.).
 
Esquema:
 
  sesiones
    id             INTEGER PK
    ejercicio      TEXT      ("sentadilla", "desplante", ...)
    fecha_inicio   TEXT      (ISO 8601)
    fecha_fin      TEXT      (ISO 8601, NULL mientras la sesión sigue activa)
 
  repeticiones
    id             INTEGER PK
    sesion_id      INTEGER   (FK -> sesiones.id)
    numero_rep     INTEGER   (1, 2, 3... dentro de esa sesión)
    timestamp      TEXT      (ISO 8601, momento exacto de la repetición)
    pierna         TEXT      ("izquierda" / "derecha" / NULL si no aplica)
    angulo_minimo  INTEGER   (qué tan profundo llegó, útil para calidad)
    correcta       INTEGER   (1 = sin errores de forma, 0 = con errores)
    errores        TEXT      (lista separada por comas: "cadera,espalda", o NULL)
"""
 
import sqlite3
import os
from datetime import datetime

# Mismas claves que EJERCICIOS en main.py / los ids de app/lib/exercises.ts
# en el frontend. Se usa solo para mostrar un nombre lindo en el historial
# del dashboard; si aparece una clave que no está acá (ejercicio viejo o
# nuevo todavía sin agregar), se cae a un capitalize() simple.
NOMBRES_EJERCICIO = {
    "sentadillas": "Sentadillas",
    "desplantes": "Desplantes",
    "curl-biceps": "Curl de bíceps",
    "elevaciones-laterales": "Elevaciones laterales",
}


class RegistroEntrenamiento:
    def __init__(self, ruta_db=None):
        if ruta_db is None:
            ruta_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart_gym.db")
        self.ruta_db = ruta_db
        self._crear_tablas()
 
    def _conectar(self):
        # check_same_thread=False porque en main.py se puede llamar desde
        # el hilo principal sin problema, pero lo dejamos flexible.
        return sqlite3.connect(self.ruta_db, check_same_thread=False)
 
    def _crear_tablas(self):
        con = self._conectar()
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ejercicio TEXT NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS repeticiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sesion_id INTEGER NOT NULL,
                numero_rep INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                pierna TEXT,
                angulo_minimo INTEGER,
                correcta INTEGER NOT NULL,
                errores TEXT,
                FOREIGN KEY (sesion_id) REFERENCES sesiones (id)
            )
        """)
        con.commit()

        # Migración: si la base de datos ya existía de antes (sin la columna
        # "precision"), la agregamos sin perder nada de lo que ya tenías.
        cur.execute("PRAGMA table_info(repeticiones)")
        columnas = [fila[1] for fila in cur.fetchall()]
        if "precision" not in columnas:
            cur.execute("ALTER TABLE repeticiones ADD COLUMN precision INTEGER")
            con.commit()

        # Migración: asociar cada sesión a un usuario (columna nueva desde
        # que existe login). Las sesiones viejas quedan con usuario_id NULL.
        cur.execute("PRAGMA table_info(sesiones)")
        columnas = [fila[1] for fila in cur.fetchall()]
        if "usuario_id" not in columnas:
            cur.execute("ALTER TABLE sesiones ADD COLUMN usuario_id INTEGER")
            con.commit()

        con.close()

    # ------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------
    def iniciar_sesion(self, ejercicio, usuario_id=None):
        """Crea una nueva sesión asociada a un usuario.
        Devuelve el id de la sesión para usarlo en registrar_repeticion()."""
        con = self._conectar()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO sesiones (ejercicio, fecha_inicio, usuario_id) VALUES (?, ?, ?)",
            (ejercicio, datetime.now().isoformat(), usuario_id)
        )
        sesion_id = cur.lastrowid
        con.commit()
        con.close()
        return sesion_id
 
    def registrar_repeticion(self, sesion_id, numero_rep, pierna=None,
                              angulo_minimo=None, correcta=True, errores=None,
                              precision=None):
        """Guarda una repetición individual. `errores` puede ser una lista
        de strings (ej. ["cadera", "espalda"]) o None. `precision` es un
        entero 0-100 (qué porcentaje del movimiento estuvo en buena forma)."""
        errores_str = ",".join(errores) if errores else None
        con = self._conectar()
        cur = con.cursor()
        cur.execute(
            """INSERT INTO repeticiones
               (sesion_id, numero_rep, timestamp, pierna, angulo_minimo, correcta, errores, precision)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (sesion_id, numero_rep, datetime.now().isoformat(),
             pierna, angulo_minimo, 1 if correcta else 0, errores_str, precision)
        )
        con.commit()
        con.close()
 
    def cerrar_sesion(self, sesion_id):
        """Marca la sesión como terminada (llamar al salir del programa)."""
        con = self._conectar()
        cur = con.cursor()
        cur.execute(
            "UPDATE sesiones SET fecha_fin = ? WHERE id = ?",
            (datetime.now().isoformat(), sesion_id)
        )
        con.commit()
        con.close()

    def obtener_sesion(self, sesion_id):
        """Devuelve {id, ejercicio, fecha_inicio, fecha_fin, usuario_id} o None."""
        con = self._conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT id, ejercicio, fecha_inicio, fecha_fin, usuario_id FROM sesiones WHERE id = ?",
            (sesion_id,)
        )
        fila = cur.fetchone()
        con.close()
        if fila is None:
            return None
        sid, ejercicio, fecha_inicio, fecha_fin, usuario_id = fila
        return {
            "id": sid,
            "ejercicio": ejercicio,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "usuario_id": usuario_id,
        }
 
    # ------------------------------------------------------------
    # Lectura (para cuando se construya la UI)
    # ------------------------------------------------------------
    def obtener_sesiones(self, ejercicio=None, limite=50):
        con = self._conectar()
        cur = con.cursor()
        if ejercicio:
            cur.execute(
                "SELECT * FROM sesiones WHERE ejercicio = ? ORDER BY fecha_inicio DESC LIMIT ?",
                (ejercicio, limite)
            )
        else:
            cur.execute("SELECT * FROM sesiones ORDER BY fecha_inicio DESC LIMIT ?", (limite,))
        filas = cur.fetchall()
        con.close()
        return filas
 
    def obtener_repeticiones_de_sesion(self, sesion_id):
        con = self._conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM repeticiones WHERE sesion_id = ? ORDER BY numero_rep ASC",
            (sesion_id,)
        )
        filas = cur.fetchall()
        con.close()
        return filas
 
    def obtener_resumen_por_dia(self, ejercicio=None):
        """Total de repeticiones por día, con precisión promedio (para
        gráficas de progreso en la UI)."""
        con = self._conectar()
        cur = con.cursor()
        if ejercicio:
            cur.execute("""
                SELECT date(r.timestamp) as dia, COUNT(*) as total,
                       SUM(r.correcta) as correctas,
                       ROUND(AVG(r.precision), 1) as precision_promedio
                FROM repeticiones r
                JOIN sesiones s ON r.sesion_id = s.id
                WHERE s.ejercicio = ?
                GROUP BY dia
                ORDER BY dia DESC
            """, (ejercicio,))
        else:
            cur.execute("""
                SELECT date(timestamp) as dia, COUNT(*) as total,
                       SUM(correcta) as correctas,
                       ROUND(AVG(precision), 1) as precision_promedio
                FROM repeticiones
                GROUP BY dia
                ORDER BY dia DESC
            """)
        filas = cur.fetchall()
        con.close()
        return filas

    def obtener_resumen_usuario(self, usuario_id):
        """Stats agregadas de un usuario puntual, para las stat cards del dashboard."""
        con = self._conectar()
        cur = con.cursor()
        cur.execute("""
            SELECT
                COUNT(DISTINCT s.id) as total_sesiones,
                COUNT(r.id) as total_reps,
                COALESCE(SUM(CASE WHEN r.correcta = 0 THEN 1 ELSE 0 END), 0) as total_errores,
                COALESCE(SUM(
                    CASE WHEN s.fecha_fin IS NOT NULL
                    THEN (julianday(s.fecha_fin) - julianday(s.fecha_inicio)) * 24 * 60
                    ELSE 0 END
                ), 0) as total_minutos
            FROM sesiones s
            LEFT JOIN repeticiones r ON r.sesion_id = s.id
            WHERE s.usuario_id = ?
        """, (usuario_id,))
        total_sesiones, total_reps, total_errores, total_minutos = cur.fetchone()
        con.close()
        return {
            "totalSessions": total_sesiones or 0,
            "totalReps": total_reps or 0,
            "totalFormErrors": total_errores or 0,
            "totalMinutes": round(total_minutos or 0),
        }

    def obtener_sesiones_usuario(self, usuario_id, limite=20):
        """Historial de sesiones de un usuario puntual, más recientes primero,
        con repeticiones/errores/duración ya agregados por sesión."""
        con = self._conectar()
        cur = con.cursor()
        cur.execute("""
            SELECT
                s.id, s.ejercicio, s.fecha_inicio,
                COUNT(r.id) as reps,
                COALESCE(SUM(CASE WHEN r.correcta = 0 THEN 1 ELSE 0 END), 0) as errores,
                CASE WHEN s.fecha_fin IS NOT NULL
                THEN ROUND((julianday(s.fecha_fin) - julianday(s.fecha_inicio)) * 24 * 60)
                ELSE 0 END as duracion_min
            FROM sesiones s
            LEFT JOIN repeticiones r ON r.sesion_id = s.id
            WHERE s.usuario_id = ?
            GROUP BY s.id
            ORDER BY s.fecha_inicio DESC
            LIMIT ?
        """, (usuario_id, limite))
        filas = cur.fetchall()
        con.close()
        return [
            {
                "id": str(sesion_id),
                "exerciseName": NOMBRES_EJERCICIO.get(ejercicio, ejercicio.capitalize()),
                "date": fecha_inicio,
                "reps": reps,
                "formErrors": errores,
                "durationMinutes": int(duracion_min),
            }
            for sesion_id, ejercicio, fecha_inicio, reps, errores, duracion_min in filas
        ]

    def obtener_racha_dias(self, usuario_id):
        """Días consecutivos (hasta hoy o ayer) con al menos una sesión.
        Si el último día con sesión fue antes de ayer, la racha está cortada."""
        con = self._conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT DISTINCT date(fecha_inicio) FROM sesiones WHERE usuario_id = ? ORDER BY date(fecha_inicio) DESC",
            (usuario_id,)
        )
        dias = [fila[0] for fila in cur.fetchall()]
        con.close()

        if not dias:
            return 0

        hoy = datetime.now().date()
        ultimo_dia = datetime.strptime(dias[0], "%Y-%m-%d").date()
        if (hoy - ultimo_dia).days > 1:
            return 0

        racha = 1
        dia_anterior = ultimo_dia
        for dia_str in dias[1:]:
            dia = datetime.strptime(dia_str, "%Y-%m-%d").date()
            if (dia_anterior - dia).days == 1:
                racha += 1
                dia_anterior = dia
            else:
                break
        return racha

    def obtener_logros(self, usuario_id):
        """Logros simples con metas fijas: racha activa, repeticiones sin
        error acumuladas, y cantidad de sesiones. Devuelve cada uno con su
        estado (desbloqueado o no) y un texto ya armado para mostrar."""
        con = self._conectar()
        cur = con.cursor()
        cur.execute("""
            SELECT
                COUNT(DISTINCT s.id) as total_sesiones,
                COALESCE(SUM(CASE WHEN r.correcta = 1 THEN 1 ELSE 0 END), 0) as reps_sin_error
            FROM sesiones s
            LEFT JOIN repeticiones r ON r.sesion_id = s.id
            WHERE s.usuario_id = ?
        """, (usuario_id,))
        total_sesiones, reps_sin_error = cur.fetchone()
        con.close()

        racha = self.obtener_racha_dias(usuario_id)
        META_REPS_SIN_ERROR = 50
        META_SESIONES = 10

        return [
            {
                "id": "racha",
                "emoji": "🔥",
                "label": f"Racha de {racha} día{'s' if racha != 1 else ''}",
                "unlocked": racha >= 1,
            },
            {
                "id": "reps_sin_error",
                "emoji": "💪",
                "label": (
                    f"{META_REPS_SIN_ERROR} repeticiones sin error"
                    if reps_sin_error >= META_REPS_SIN_ERROR
                    else f"{reps_sin_error}/{META_REPS_SIN_ERROR} repeticiones sin error"
                ),
                "unlocked": reps_sin_error >= META_REPS_SIN_ERROR,
            },
            {
                "id": "sesiones",
                "emoji": "🏅",
                "label": (
                    f"{META_SESIONES} sesiones completadas"
                    if total_sesiones >= META_SESIONES
                    else f"{total_sesiones} sesiones (faltan {META_SESIONES - total_sesiones})"
                ),
                "unlocked": total_sesiones >= META_SESIONES,
            },
        ]
 