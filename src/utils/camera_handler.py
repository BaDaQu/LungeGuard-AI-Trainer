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
            if isinstance(self.source, int):
                # USB Camera
                self.capture = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
                self.capture.set(cv2.CAP_PROP_FPS, 30)
            else:
                # IP Camera
                self.capture = cv2.VideoCapture(self.source)
                # Wymuszenie minimalnego bufora
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
        while self.running:
            if self.capture.isOpened():
                # GRAB: Pobieramy dane z bufora, ale jeszcze nie dekodujemy
                # To pozwala "przewinąć" bufor, jeśli zrobił się korek
                self.capture.grab()

                # RETRIEVE: Dekodujemy tylko najnowszą klatkę
                ret, raw_frame = self.capture.retrieve()

                if ret:
                    try:
                        # Używamy INTER_NEAREST - najszybsze możliwe skalowanie (zero antyaliasingu)
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
                    # Jeśli strumień zerwał, czekamy chwilę
                    time.sleep(0.05)
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