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
                # --- ZMIANA: PRÓBA WYMUSZENIA 60 FPS ---
                self.capture.set(cv2.CAP_PROP_FPS, 60)
            else:
                # IP Camera
                self.capture = cv2.VideoCapture(self.source)
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
            try:
                if self.capture is not None and self.capture.isOpened():
                    try:
                        self.capture.grab()
                    except Exception:
                        break

                    ret, raw_frame = self.capture.retrieve()

                    if ret:
                        try:
                            # Skalowanie (szybkie)
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
                        time.sleep(0.005)  # Krótszy sleep dla 60 FPS
                else:
                    time.sleep(0.1)

            except Exception as e:
                print(f"[{self.name}] Thread Error: {e}")
                break

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