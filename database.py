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
 
        con.close()
 
    # ------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------
    def iniciar_sesion(self, ejercicio):
        """Crea una nueva sesión (se llama una vez al arrancar el programa).
        Devuelve el id de la sesión para usarlo en registrar_repeticion()."""
        con = self._conectar()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO sesiones (ejercicio, fecha_inicio) VALUES (?, ?)",
            (ejercicio, datetime.now().isoformat())
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
 