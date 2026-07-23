import threading
import queue
import time
import pyttsx3


class Speaker:
    def __init__(self, rate=180, voice_hint="ES-"):
        self.queue = queue.Queue()
        self.running = True
        self.last_time = {}

        # Palabras clave de errores críticos: descartan cualquier mensaje
        # pendiente (aún no hablado) en la cola para priorizarse.
        self.error_words = [
            "Pecho",
            "Endereza",
            "Cadera",
        ]

        self.rate = rate
        self.voice_hint = voice_hint

        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()

    def _build_engine(self):
        # pyttsx3 + SAPI5 se cuelga si se reutiliza la misma instancia entre
        # llamadas a runAndWait(); crear un motor nuevo por frase es el
        # workaround estable en Windows.
        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate)
        for voice in engine.getProperty("voices"):
            if self.voice_hint in voice.id:
                engine.setProperty("voice", voice.id)
                break
        return engine

    def speak_unique(self, text):
        if not text:
            return

        ahora = time.time()

        # 1. Prioridad máxima: errores técnicos críticos.
        if text in self.error_words:
            if text in self.last_time and ahora - self.last_time[text] < 3.0:
                return
            self.last_time[text] = ahora
            self._replace_pending(text)
            return

        # 2. Prioridad media: contador de repeticiones (sin cooldown,
        # para que los números fluyan seguidos: "Bien 1", "Bien 2"...).
        if text.startswith("Bien "):
            self._replace_pending(text)
            return

        # 3. Información / mensajes generales.
        if text in self.last_time and ahora - self.last_time[text] < 2.0:
            return
        self.last_time[text] = ahora

        if self.queue.empty():
            self.queue.put(text)

    def _replace_pending(self, text):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
        self.queue.put(text)

    def _process_queue(self):
        while self.running:
            try:
                text = self.queue.get(timeout=1)
            except queue.Empty:
                continue

            print(time.time(), "SPEAKER ->", text)
            # SAPI5/pywin32 deja el apartment COM del hilo en un estado que
            # solo funciona para la PRIMERA vez que se habla en ese hilo; las
            # llamadas siguientes "funcionan" (sin excepción) pero quedan
            # mudas. Ejecutar cada frase en un hilo descartable nuevo evita
            # el problema porque siempre es "la primera vez" en ese hilo.
            worker = threading.Thread(target=self._speak_once, args=(text,))
            worker.start()
            worker.join()

    def _speak_once(self, text):
        engine = self._build_engine()
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    def stop(self):
        self.running = False
