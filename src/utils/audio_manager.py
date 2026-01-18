import pyttsx3
import threading
import queue
import time


class AudioManager:
    def __init__(self):
        """
        Manager dźwięku z priorytetami.
        """
        self.queue = queue.Queue()
        self.is_running = False
        self.thread = None
        self.last_spoken = {}
        # Cooldown 2.0s dla błędów
        self.COOLDOWN_SECONDS = 2.0

    def start(self):
        if self.is_running: return

        self.is_running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        print("AUDIO DEBUG: Wątek wystartował.")

    def _worker(self):
        """Pętla robocza."""
        while self.is_running:
            try:
                # 1. Pobieramy tekst
                text = self.queue.get(timeout=0.5)

                # 2. Tworzymy jednorazowy silnik (dla stabilności)
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)

                # Szukamy polskiego głosu
                voices = engine.getProperty('voices')
                for v in voices:
                    if "pl" in v.id.lower():
                        engine.setProperty('voice', v.id)
                        break

                # 3. Mówimy
                # print(f"AUDIO MÓWI: {text}") # Uncomment for debug
                engine.say(text)
                engine.runAndWait()
                engine.stop()

                del engine
                self.queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"AUDIO ERROR: {e}")

    def speak(self, text, force=False):
        """
        Dodaje komunikat do kolejki.
        :param force: Jeśli True (Start/Stop/Licznik) -> CZYŚCI KOLEJKĘ z poprzednich błędów.
        """
        now = time.time()

        if force:
            # --- KLUCZOWA ZMIANA: PRIORYTET ---
            # Jeśli to ważny komunikat, usuwamy wszystkie oczekujące "błędy techniczne"
            # żeby system zareagował natychmiast i nie gadał starych rzeczy.
            with self.queue.mutex:
                self.queue.queue.clear()
        else:
            # Dla zwykłych błędów sprawdzamy cooldown
            last_time = self.last_spoken.get(text, 0)
            if now - last_time < self.COOLDOWN_SECONDS:
                return

        self.last_spoken[text] = now
        self.queue.put(text)

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()