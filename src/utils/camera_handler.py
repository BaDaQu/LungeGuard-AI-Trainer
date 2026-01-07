import cv2
import threading
import time


class CameraHandler:
    def __init__(self, camera_id=0):
        """
        Inicjalizacja kamery z obsługą wielowątkowości (threading).
        :param camera_id: ID kamery (0 dla laptopa) lub adres URL (http://.../video).
        """
        self.camera_id = camera_id
        self.frame = None
        self.running = False

        # Próba połączenia ze strumieniem wideo
        self.stream = cv2.VideoCapture(self.camera_id)

        if not self.stream.isOpened():
            print(f"DEBUG: Błąd! Nie można połączyć z kamerą: {self.camera_id}")
            self.running = False
        else:
            print(f"DEBUG: Połączono z kamerą: {self.camera_id}")
            # Pobieramy pierwszą klatkę, żeby zmienna self.frame nie była pusta
            (grabbed, self.frame) = self.stream.read()
            self.running = True

    def start(self):
        """Uruchamia wątek czytania klatek w tle."""
        if not self.running:
            print("DEBUG: Kamera nie jest połączona, nie startuję wątku.")
            return self

        print(f"DEBUG: Uruchamiam wątek dla kamery {self.camera_id}")
        t = threading.Thread(target=self.update, args=())
        t.daemon = True  # Wątek zamknie się razem z programem
        t.start()
        return self

    def update(self):
        """Pętla działająca w tle - ciągle pobiera najnowszą klatkę."""
        while self.running:
            # Czytamy klatkę ze strumienia
            (grabbed, frame) = self.stream.read()

            # Jeśli klatka jest poprawna, aktualizujemy zmienną
            if grabbed:
                self.frame = frame
            else:
                # Jeśli zerwie połączenie
                print("DEBUG: Utracono sygnał z kamery.")
                self.running = False

    def get_frame(self):
        """Zwraca ostatnią klatkę (natychmiastowo)."""
        return self.frame

    def stop(self):
        """Zatrzymuje kamerę i zwalnia zasoby."""
        self.running = False
        if self.stream:
            self.stream.release()
        print("DEBUG: Zatrzymano kamerę.")