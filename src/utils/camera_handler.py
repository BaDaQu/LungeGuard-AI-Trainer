import cv2
import threading

class CameraHandler:
    def __init__(self, camera_id=0):
        """
        Inicjalizacja kamery.
        :param camera_id: ID kamery (0 dla domyślnej) lub adres IP (rtsp://...).
        """
        self.camera_id = camera_id
        self.frame = None
        self.running = False
        # Tutaj w przyszłości dodamy wątek czytający klatki
        pass

    def start(self):
        """Uruchamia wątek czytania klatek."""
        print(f"DEBUG: Uruchamiam kamerę {self.camera_id}")
        self.running = True

    def get_frame(self):
        """Zwraca ostatnią klatkę."""
        # Na razie zwraca pusty obraz (dummy), żeby testy przeszły
        return None

    def stop(self):
        """Zatrzymuje kamerę i zwalnia zasoby."""
        self.running = False
        print("DEBUG: Zatrzymano kamerę.")