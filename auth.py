"""
Persistencia de usuarios (registro/login) en SQLite, en la misma base de
datos que ya usa RegistroEntrenamiento (smart_gym.db).

Tabla `usuarios`:
    id              INTEGER PRIMARY KEY
    nombre          TEXT      NOT NULL
    email           TEXT      NOT NULL UNIQUE
    password_hash   TEXT      NOT NULL  ("<salt_hex>$<hash_hex>")
    fecha_registro  TEXT      NOT NULL
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime

PBKDF2_ITERACIONES = 260_000

# En un entorno real esto tiene que salir de una variable de entorno. Acá
# tiene un default de desarrollo para no bloquear a nadie que clone el repo,
# pero cualquier despliegue real DEBE setear SMART_GYM_SECRET_KEY.
SECRET_KEY = os.environ.get("SMART_GYM_SECRET_KEY", "smart-gym-dev-secret-no-usar-en-produccion")
SESION_DURACION_SEGUNDOS = 7 * 24 * 60 * 60  # 7 días


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    relleno = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + relleno)


def crear_token(usuario):
    """Genera un token firmado (estilo JWT, HS256) con el id/nombre/email del
    usuario y una expiración. No usa ninguna librería externa: header y
    payload van en base64url, firmados con HMAC-SHA256 sobre SECRET_KEY."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": usuario["id"],
        "nombre": usuario["nombre"],
        "email": usuario["email"],
        "exp": int(time.time()) + SESION_DURACION_SEGUNDOS,
    }
    partes = f"{_b64url_encode(json.dumps(header).encode())}.{_b64url_encode(json.dumps(payload).encode())}"
    firma = hmac.new(SECRET_KEY.encode("utf-8"), partes.encode("ascii"), hashlib.sha256).digest()
    return f"{partes}.{_b64url_encode(firma)}"


def verificar_token(token):
    """Devuelve el payload del token si la firma es válida y no expiró, o None."""
    try:
        header_b64, payload_b64, firma_b64 = token.split(".")
    except (ValueError, AttributeError):
        return None

    partes = f"{header_b64}.{payload_b64}"
    firma_esperada = hmac.new(SECRET_KEY.encode("utf-8"), partes.encode("ascii"), hashlib.sha256).digest()
    firma_recibida = _b64url_decode(firma_b64)

    if not hmac.compare_digest(firma_esperada, firma_recibida):
        return None

    payload = json.loads(_b64url_decode(payload_b64))
    if payload.get("exp", 0) < time.time():
        return None

    return payload


def hashear_password(password):
    sal = secrets.token_hex(16)
    hash_ = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal.encode("utf-8"), PBKDF2_ITERACIONES)
    return f"{sal}${hash_.hex()}"


def verificar_password(password, password_hash):
    sal, _, hash_esperado = password_hash.partition("$")
    hash_calculado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal.encode("utf-8"), PBKDF2_ITERACIONES)
    return secrets.compare_digest(hash_calculado.hex(), hash_esperado)


class EmailYaRegistradoError(Exception):
    pass


class GestorUsuarios:
    def __init__(self, ruta_db=None):
        if ruta_db is None:
            ruta_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart_gym.db")
        self.ruta_db = ruta_db
        self._crear_tablas()

    def _conectar(self):
        return sqlite3.connect(self.ruta_db, check_same_thread=False)

    def _crear_tablas(self):
        con = self._conectar()
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                fecha_registro TEXT NOT NULL
            )
        """)
        con.commit()
        con.close()

    def crear_usuario(self, nombre, email, password):
        con = self._conectar()
        cur = con.cursor()
        cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        if cur.fetchone() is not None:
            con.close()
            raise EmailYaRegistradoError(email)

        cur.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, fecha_registro) VALUES (?, ?, ?, ?)",
            (nombre, email, hashear_password(password), datetime.now().isoformat()),
        )
        usuario_id = cur.lastrowid
        con.commit()
        con.close()
        return {"id": usuario_id, "nombre": nombre, "email": email}

    def verificar_credenciales(self, email, password):
        """Devuelve {id, nombre, email} si las credenciales son correctas, o None."""
        con = self._conectar()
        cur = con.cursor()
        cur.execute("SELECT id, nombre, email, password_hash FROM usuarios WHERE email = ?", (email,))
        fila = cur.fetchone()
        con.close()

        if fila is None:
            return None

        usuario_id, nombre, email, password_hash = fila
        if not verificar_password(password, password_hash):
            return None

        return {"id": usuario_id, "nombre": nombre, "email": email}
