

# import pyttsx3
# import threading
# import queue

# class Speaker:
#     def __init__(self):
#         self.queue = queue.Queue()
#         self.running = True
#         self.last_spoken = ""
        
#         self.thread = threading.Thread(target=self._process_queue, daemon=True)
#         self.thread.start()

#     def speak_unique(self, text):
#         if not text:
#             return
        
#         # Permitir siempre repetir los números de repeticiones ("Bien X")
#         if not text.startswith("Bien ") and text == self.last_spoken:
#             return
        
#         self.last_spoken = text
#         # Vaciar cola anterior para decir siempre la instrucción más fresca
#         while not self.queue.empty():
#             try:
#                 self.queue.get_nowait()
#             except queue.Empty:
#                 break
                
#         self.queue.put(text)

#     def _process_queue(self):
#         while self.running:
#             try:
#                 text = self.queue.get(timeout=1)
#                 engine = pyttsx3.init()
#                 engine.setProperty('rate', 180)
#                 engine.say(text)
#                 engine.runAndWait()
#                 engine.stop()
#             except queue.Empty:
#                 continue
#             except Exception as e:
#                 print(f"Error en audio: {e}")




# import threading
# import queue
# import time
# import subprocess


# class Speaker:
#     def __init__(self):
#         self.queue = queue.Queue()
#         self.running = True
#         self.last_time = {}

#         self.thread = threading.Thread(
#             target=self._process_queue,
#             daemon=True
#         )
#         self.thread.start()

#     def speak_unique(self, text):
#         if not text:
#             return

#         ahora = time.time()

#         # "Bien X" siempre se permite
#         if not text.startswith("Bien "):
#             if text in self.last_time:
#                 if ahora - self.last_time[text] < 4:
#                     return

#             self.last_time[text] = ahora

#         # Solo agregar si no hay otra voz esperando
#         if self.queue.empty():
#             self.queue.put(text)

#     def _process_queue(self):
#         while self.running:
#             try:
#                 text = self.queue.get(timeout=1)

#                 print(f"🔊 {text}")

#                 subprocess.run(
#                     ["say", "-r", "180", text],
#                     stdout=subprocess.DEVNULL,
#                     stderr=subprocess.DEVNULL
#                 )

#             except queue.Empty:
#                 continue
#             except Exception as e:
#                 print("Error en audio:", e)


import threading
import queue
import time
import subprocess

class Speaker:
    def __init__(self):
        self.queue = queue.Queue()
        self.running = True
        self.last_time = {}
        self.current_process = None

        # Palabras clave de errores críticos que matan cualquier audio en curso
        self.error_words = [
            "Pecho",
            "Endereza"
        ]

        self.thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self.thread.start()

    def speak_unique(self, text):
        if not text:
            return

        ahora = time.time()

        # ----------------------------------------------------
        # 1. PRIORIDAD MÁXIMA: ERRORES TÉCNICOS CRÍTICOS
        # ----------------------------------------------------
        if text in self.error_words:
            # Control de cooldown específico para errores (3 segundos para no saturar al usuario)
            if text in self.last_time:
                if ahora - self.last_time[text] < 3.0:
                    return
            self.last_time[text] = ahora

            # Interrumpir de inmediato cualquier audio que esté sonando (ej. si iba diciendo un "Bien")
            if self.current_process is not None:
                try:
                    self.current_process.terminate()
                except:
                    pass

            # Vaciar la cola para descartar audios viejos acumulados
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break

            self.queue.put(text)
            return

        # ----------------------------------------------------
        # 2. PRIORIDAD MEDIA: CONTADOR DE REPETICIONES
        # ----------------------------------------------------
        if text.startswith("Bien "):
            # Sin filtro de tiempo (cooldown) para que los números fluyan seguidos sin bloquearse ("Bien 1", "Bien 2"...)
            
            # Si hay un error sonando, lo matamos también; si es otro conteo anterior, se limpia
            if self.current_process is not None:
                try:
                    self.current_process.terminate()
                except:
                    pass

            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break

            self.queue.put(text)
            return

        # ----------------------------------------------------
        # 3. INFORMACIÓN / OTROS MENSAJES GENERALES
        # ----------------------------------------------------
        if text in self.last_time:
            if ahora - self.last_time[text] < 2.0:
                return

        self.last_time[text] = ahora

        if self.queue.empty():
            self.queue.put(text)

    def _process_queue(self):
        while self.running:
            try:
                text = self.queue.get(timeout=1)

                print(time.time(), "SPEAKER ->", text)

                self.current_process = subprocess.Popen(
                    ["say", "-r", "180", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                self.current_process.wait()

                self.current_process = None

            except queue.Empty:
                continue

            except Exception as e:
                print(e)
