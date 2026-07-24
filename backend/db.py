from prisma import Prisma

# Cliente Prisma compartido para todo el proceso backend. La conexión no se
# abre acá: el ciclo de vida (connect/disconnect) lo maneja app.py en los
# eventos de startup/shutdown de FastAPI.
db = Prisma()
