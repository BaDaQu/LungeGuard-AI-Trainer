import cv2
import threading
import time


class CameraHandler:
    def __init__(self, source=0, name="Camera", width=640, height=480):
        self.source = source
        self.name = name
        self.target_width = width
        self.target_height = height

        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self.capture = None

    def start(self):
        if self.running: return

        print(f"[{self.name}] Start: {self.source}")
        try:
            # DSHOW dla Windows USB (szybki start)
            if isinstance(self.source, int):
                self.capture = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
                self.capture.set(cv2.CAP_PROP_FPS, 30)
            else:
                # IP Camera
                self.capture = cv2.VideoCapture(self.source)
                # Ustawiamy minimalny bufor
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self.capture.isOpened():
                print(f"[{self.name}] Błąd otwarcia!")
                return

        except Exception as e:
            print(f"[{self.name}] Wyjątek: {e}")
            return

        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        """
        Wątek pobierający.
        AGRESYWNA OPTYMALIZACJA: Zawsze czytamy najnowszą klatkę, pomijając stare.
        """
        while self.running:
            if self.capture.isOpened():
                # --- KLUCZOWA ZMIANA ---
                # Grab() pobiera klatkę z bufora sprzętowego.
                # Robimy to, żeby 'przewinąć' bufor do końca.
                self.capture.grab()

                # Retrieve() dekoduje obraz. Robimy to raz na pętlę.
                ret, raw_frame = self.capture.retrieve()

                if ret:
                    try:
                        # Skalowanie w wątku (najszybsza metoda INTER_NEAREST)
                        resized_frame = cv2.resize(
                            raw_frame,
                            (self.target_width, self.target_height),
                            interpolation=cv2.INTER_NEAREST
                        )

                        with self.lock:
                            self.frame = resized_frame
                    except Exception:
                        pass
                else:
                    # Jeśli zgubiliśmy sygnał, krótki sleep żeby nie spalić CPU
                    time.sleep(0.01)
            else:
                time.sleep(0.1)

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        if self.capture is not None:
            self.capture.release()