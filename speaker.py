
import threading
import queue
import time
import subprocess
import os
import platform

# "Darwin" = macOS. Es la única plataforma con `say`/`afplay` disponibles
# (son comandos de la terminal de Mac, no existen en Windows ni Linux).
SISTEMA = platform.system()


class Speaker:
    # Carpeta donde se guardan los audios pre-generados (junto a este archivo)
    AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_cache")
 
    FRASES_FIJAS = [
        "Endereza", "Cadera", "Pecho", "Buen fondo", "Correcto: Baja",
        "Bien pero endereza la espalda", "Bien pero endereza el torso",
        "Codo", "Hombro", "Bien pero fija el codo", "Bien pero no balancees",
        "Baja los hombros", "No te inclines", "Bien pero baja los hombros", "Bien pero no te inclines",
        "Bien pero sube completo",
        "No subas tanto", "Bien pero no subas tanto",
        "Nivela los hombros", "Bien pero nivela los hombros",
    ]
    MAX_REPS_PRECARGA = 50  # pre-generamos "Bien 1".."Bien 50" para que salgan al instante
 
    def __init__(self):
        self.queue = queue.Queue()
        self.running = True
        self.last_time = {}
        self.current_process = None
 
        # Qué tipo de audio está sonando en este momento: "critico", "conteo", "info" o None
        self.current_type = None
 
        # Palabras clave de errores críticos (tienen la prioridad más alta)
        self.error_words = [
            "Pecho",
            "Endereza",
            "Cadera",
            "Codo",
            "Hombro",
            "Baja los hombros",
            "No te inclines",
            "No subas tanto",
            "Nivela los hombros",
        ]
 
        if SISTEMA == "Darwin":
            # La precarga solo tiene sentido con `say`: generar el .aiff es
            # lento, así que lo hacemos una vez al arrancar en vez de en
            # cada repetición. pyttsx3 (Windows/Linux) sintetiza y reproduce
            # en el momento, no hay archivo que precargar.
            os.makedirs(self.AUDIO_DIR, exist_ok=True)
            print("Preparando frases de voz (una sola vez, unos segundos)...")
            self._precargar_audios()
            print("Voz lista.")
        else:
            print("Voz lista (motor de Windows/Linux, sin precarga).")

        self.thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self.thread.start()
 
    # ------------------------------------------------------------
    # Generación / caché de audio: aquí es donde ocurre la síntesis
    # lenta de "say". La hacemos ANTES de la sesión, no durante.
    # ------------------------------------------------------------
    def _ruta_audio(self, text):
        nombre = text.replace(" ", "_").replace(":", "")
        return os.path.join(self.AUDIO_DIR, f"{nombre}.aiff")
 
    def _generar_audio(self, text):
        ruta = self._ruta_audio(text)
        if not os.path.exists(ruta):
            subprocess.run(
                ["say", "-r", "180", "-o", ruta, text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return ruta
 
    def _precargar_audios(self):
        frases = list(self.FRASES_FIJAS)
        frases += [f"Bien {i}" for i in range(1, self.MAX_REPS_PRECARGA + 1)]
        for frase in frases:
            self._generar_audio(frase)
 
    def _vaciar_cola(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
 
    def speak_unique(self, text):
        if not text:
            return
 
        ahora = time.time()
        es_critico = text in self.error_words
        es_conteo = text.startswith("Bien ")
 
        # ----------------------------------------------------
        # 1. PRIORIDAD MÁXIMA: ERRORES TÉCNICOS CRÍTICOS
        # ----------------------------------------------------
        if es_critico:
            # Control de cooldown específico para errores (3 segundos para no saturar al usuario)
            if text in self.last_time:
                if ahora - self.last_time[text] < 3.0:
                    return
            self.last_time[text] = ahora
 
            # Los errores SIEMPRE interrumpen cualquier otra cosa que esté sonando
            if self.current_process is not None:
                try:
                    self.current_process.terminate()
                except:
                    pass
 
            self._vaciar_cola()
            self.queue.put(text)
            return
 
        # ----------------------------------------------------
        # 2. PRIORIDAD MEDIA: CONTADOR DE REPETICIONES
        # ----------------------------------------------------
        if es_conteo:
            # Si en este momento está sonando una corrección crítica (ej. "Endereza"),
            # NO la interrumpimos: dejamos que termine y el "Bien X" se dice justo después
            if self.current_type == "critico":
                self._vaciar_cola()
                self.queue.put(text)
                return
 
            # Si no hay nada crítico sonando, sí puede interrumpir (ej. un "Bien" anterior)
            if self.current_process is not None:
                try:
                    self.current_process.terminate()
                except:
                    pass
 
            self._vaciar_cola()
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
 
    def _reproducir_windows(self, text):
        """pyttsx3 en Windows tiene un problema conocido de threading (COM
        apartment): si se reutiliza el mismo motor/hilo para hablar varias
        veces seguidas, se queda mudo después de la primera frase. La forma
        confiable de evitarlo es crear un motor nuevo en un hilo nuevo,
        throwaway, por cada frase, y esperarlo de forma síncrona antes de
        seguir con la próxima de la cola.

        Diferencia con macOS: acá no hay un proceso de SO que se pueda matar
        a mitad de reproducción, así que un error crítico nuevo no corta en
        seco la frase que está sonando (sí se saltea todo lo que quedó en
        cola detrás). Las frases son cortas, así que en la práctica no se
        nota casi nada.
        """
        import pyttsx3

        def _hablar():
            motor = pyttsx3.init()
            for voz in motor.getProperty("voices"):
                if "ES-MX" in voz.id.upper() or "ES_MX" in voz.id.upper():
                    motor.setProperty("voice", voz.id)
                    break
                if "ES-" in voz.id.upper() or "ES_" in voz.id.upper():
                    motor.setProperty("voice", voz.id)
            motor.say(text)
            motor.runAndWait()
            motor.stop()

        hilo = threading.Thread(target=_hablar, daemon=True)
        hilo.start()
        hilo.join()

    def _process_queue(self):
        while self.running:
            try:
                text = self.queue.get(timeout=1)

                if text in self.error_words:
                    self.current_type = "critico"
                elif text.startswith("Bien "):
                    self.current_type = "conteo"
                else:
                    self.current_type = "info"

                print(time.time(), "SPEAKER ->", text)

                if SISTEMA == "Darwin":
                    # Usamos el audio pre-generado (instantáneo). Si por algo no
                    # está cacheado (ej. reps > 50), se genera acá como respaldo.
                    ruta = self._generar_audio(text)

                    self.current_process = subprocess.Popen(
                        ["afplay", ruta],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                    self.current_process.wait()
                    self.current_process = None
                else:
                    self._reproducir_windows(text)

                self.current_type = None

            except queue.Empty:
                continue

            except Exception as e:
                print(e)
 