import cv2
import threading
import time


class CameraHandler:
    def __init__(self, source=0, name="Camera"):
        """
        Inicjalizuje obsługę kamery w oddzielnym wątku.
        :param source: ID kamery (0) lub URL (http://IP:PORT/video).
        :param name: Nazwa kamery do logów (np. "FRONT", "SIDE").
        """
        self.source = source
        self.name = name
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self.capture = None

    def start(self):
        """Uruchamia połączenie i wątek pobierania klatek."""
        if self.running:
            print(f"[{self.name}] Już działa.")
            return

        print(f"[{self.name}] Łączenie ze źródłem: {self.source}...")
        try:
            # Optymalizacja dla Windows (kamera USB) - szybszy start
            if isinstance(self.source, int):
                self.capture = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
                # Opcjonalnie wymuszenie 30 FPS dla USB
                self.capture.set(cv2.CAP_PROP_FPS, 30)
            else:
                # Kamera IP
                self.capture = cv2.VideoCapture(self.source)

                # --- KLUCZOWE DLA KAMERY IP (Naprawa lagów) ---
                # Ustawiamy bufor na 1 klatkę. OpenCV nie będzie przechowywać starych klatek.
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # ----------------------------------------------

            if not self.capture.isOpened():
                print(f"[{self.name}] BŁĄD KRYTYCZNY: Nie można otworzyć źródła!")
                return

        except Exception as e:
            print(f"[{self.name}] Wyjątek przy łączeniu: {e}")
            return

        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        print(f"[{self.name}] Połączono.")

    def _update(self):
        """Pętla czytająca klatki (działa w tle)."""
        while self.running:
            if self.capture.isOpened():
                # Pobieramy klatkę
                ret, frame = self.capture.read()

                if ret:
                    with self.lock:
                        self.frame = frame
                else:
                    # Jeśli strumień zerwał, czekamy chwilę (nie katujemy CPU)
                    time.sleep(0.01)
            else:
                time.sleep(0.1)

    def get_frame(self):
        """Zwraca najnowszą klatkę (bezpiecznie dla wątków)."""
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None

    def stop(self):
        """Zatrzymuje kamerę."""
        self.running = False
        if self.thread is not None:
            # Czekamy max 1s na zakończenie wątku
            self.thread.join(timeout=1.0)

        if self.capture is not None:
            self.capture.release()

        print(f"[{self.name}] Zatrzymano.")