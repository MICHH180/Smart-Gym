# """
# Script simple para ver tu historial de entrenamientos guardado en SQLite.
 
# Uso: colócalo en la misma carpeta que database.py (tu carpeta Smart-gym)
# y corre en la terminal:
 
#     python3 ver_historial.py
# """
 
# from database import RegistroEntrenamiento
 
# r = RegistroEntrenamiento()
 
# print("=" * 50)
# print("SESIONES")
# print("=" * 50)
# for sesion in r.obtener_sesiones():
#     print(sesion)
 
# print()
# print("=" * 50)
# print("RESUMEN POR DÍA (todas las repeticiones)")
# print("=" * 50)
# for fila in r.obtener_resumen_por_dia():
#     print(fila)
 
# print()
# print("=" * 50)
# print("RESUMEN POR DÍA - solo sentadillas")
# print("=" * 50)
# for fila in r.obtener_resumen_por_dia(ejercicio="sentadilla"):
#     print(fila)
 
# print()
# print("=" * 50)
# print("RESUMEN POR DÍA - solo desplantes")
# print("=" * 50)
# for fila in r.obtener_resumen_por_dia(ejercicio="desplante"):
#     print(fila)
 
"""
Script simple para ver tu historial de entrenamientos guardado en SQLite.
 
Uso: colócalo en la misma carpeta que database.py (tu carpeta Smart-gym)
y corre en la terminal:
 
    python3 ver_historial.py
"""
 
from database import RegistroEntrenamiento
 
r = RegistroEntrenamiento()
 
print("=" * 50)
print("SESIONES")
print("=" * 50)
for sesion in r.obtener_sesiones():
    print(sesion)
 
print()
print("=" * 50)
print("RESUMEN POR DÍA (todas las repeticiones)")
print("Formato: (día, total, correctas, precisión promedio %)")
print("=" * 50)
for fila in r.obtener_resumen_por_dia():
    print(fila)
 
print()
print("=" * 50)
print("RESUMEN POR DÍA - solo sentadillas")
print("=" * 50)
for fila in r.obtener_resumen_por_dia(ejercicio="sentadilla"):
    print(fila)
 
print()
print("=" * 50)
print("RESUMEN POR DÍA - solo desplantes")
print("=" * 50)
for fila in r.obtener_resumen_por_dia(ejercicio="desplante"):
    print(fila)
 