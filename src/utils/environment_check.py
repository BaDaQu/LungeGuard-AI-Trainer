import cv2
import numpy as np


class EnvironmentCheck:
    @staticmethod
    def check_brightness(frame):
        """
        Analizuje średnią jasność klatki wideo.
        :return: (is_ok, message)
        """
        if frame is None:
            return False, "BRAK OBRAZU"

        # Konwersja na skalę szarości dla szybkości
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)

        if brightness < 60:
            return False, "ZA CIEMNO! DOSWIETL POMIESZCZENIE"
        elif brightness > 240:
            return False, "ZA JASNO! UNIKAJ SYTUACJI POD SWIATLO"

        return True, "SWIATLO OK"

    @staticmethod
    def check_distance(landmarks):
        """
        Sprawdza, czy sylwetka jest w pełni widoczna i w odpowiedniej odległości.
        """
        if not landmarks:
            return False, "NIE WIDZE CIE"

        # Kluczowe punkty: Nos (0) i Lewa Stopa (31)
        try:
            nose = landmarks[0]
            foot = landmarks[31]

            # 1. Sprawdzenie czy punkty mieszczą się w kadrze (0.0 - 1.0)
            margin = 0.02
            if not (margin < nose[1] < 1 - margin and margin < nose[2] < 1 - margin):
                return False, "GLOWA POZA KADREM"
            if not (margin < foot[1] < 1 - margin and margin < foot[2] < 1 - margin):
                return False, "STOPY POZA KADREM"

            # 2. Sprawdzenie wielkości sylwetki (czy nie stoi za daleko)
            # Wysokość postaci w % ekranu
            height_ratio = foot[2] - nose[2]

            if height_ratio < 0.35:
                return False, "PODEJDZ BLIZEJ (ZA DALEKO)"

            if height_ratio > 0.95:
                return False, "ODSUN SIE TROCHE"

            return True, "DYSTANS OK"

        except IndexError:
            return False, "BLAD DETEKCJI"