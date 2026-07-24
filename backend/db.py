from prisma import Prisma

# Cliente Prisma compartido para todo el proceso backend. La conexión no se
# abre acá: el ciclo de vida (connect/disconnect) lo maneja app.py en los
# eventos de startup/shutdown de FastAPI.
db = Prisma()

# Usuario placeholder de desarrollo: todavía no hay autenticación real, así
# que toda sesión persistida se asocia a este email fijo. Reemplazar cuando
# se implemente auth (incremento futuro, fuera de este alcance).
# Vive acá (no en app.py) para que tanto app.py como historial.py puedan
# importarlo sin crear un import circular (backend.db no depende de nada
# más del paquete backend).
DEV_USER_EMAIL = "dev@smartgym.local"
