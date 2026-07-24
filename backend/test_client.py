"""Cliente manual de prueba: simula lo que hará el navegador (captura de
webcam + envío de frames por WebSocket) para validar el pipeline completo
antes de que exista un frontend real.

Uso: con el servidor corriendo (`uvicorn backend.app:app --reload` desde la
raíz del proyecto), ejecutar este script y presionar 'ESC' para salir.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
from websockets.sync.client import connect

URL = "ws://localhost:8000/ws/session"


def main():
    cap = cv2.VideoCapture(0)
    print("Smart Gym - Cliente de prueba WebSocket. Presiona 'ESC' para salir.")

    with connect(URL) as websocket:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)

            ok, buffer = cv2.imencode(".jpg", frame)
            if not ok:
                continue

            websocket.send(buffer.tobytes())
            resultado = websocket.recv()
            print(resultado)

            cv2.imshow("Smart Gym - Cliente de prueba", frame)

            if cv2.waitKey(10) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
