import pyttsx3
import threading
import queue
import time


class AudioManager:
    def __init__(self):
        """
        Manager dźwięku odporny na błędy wątków Windows (SAPI5).
        Tworzy nową instancję silnika dla każdego komunikatu.
        """
        self.queue = queue.Queue()
        self.is_running = False
        self.thread = None
        self.last_spoken = {}
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
                # 1. Czekamy na tekst w kolejce
                text = self.queue.get(timeout=0.5)

                print(f"AUDIO DEBUG: Mówię -> '{text}'")

                # 2. Inicjalizacja silnika WEWNĄTRZ pętli (Fix dla Windows)
                # Dzięki temu unikamy zawieszenia pętli zdarzeń
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)

                # Ustawienie głosu (opcjonalne)
                voices = engine.getProperty('voices')
                for v in voices:
                    if "pl" in v.id.lower():
                        engine.setProperty('voice', v.id)
                        break

                # 3. Wypowiedzenie i zamknięcie
                engine.say(text)
                engine.runAndWait()
                engine.stop()

                # 4. Sprzątanie
                del engine
                self.queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"AUDIO ERROR: {e}")

    def speak(self, text, force=False):
        """Dodaje komunikat do kolejki z uwzględnieniem cooldownu."""
        now = time.time()

        if not force:
            last_time = self.last_spoken.get(text, 0)
            if now - last_time < self.COOLDOWN_SECONDS:
                return

        self.last_spoken[text] = now
        self.queue.put(text)

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()