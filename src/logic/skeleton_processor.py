from src.logic.geometry_utils import GeometryUtils


class SkeletonProcessor:
    def __init__(self):
        """
        Klasa interpretująca surowe punkty szkieletu na dane analityczne.
        Mapuje indeksy MediaPipe na konkretne stawy.
        """
        self.MP_LEFT_HIP = 23
        self.MP_LEFT_KNEE = 25
        self.MP_LEFT_ANKLE = 27

        self.MP_RIGHT_HIP = 24
        self.MP_RIGHT_KNEE = 26
        self.MP_RIGHT_ANKLE = 28

    def process_side_view(self, landmarks, side="left"):
        """
        Oblicza kąt zgięcia kolana na podstawie widoku bocznego.
        """
        if not landmarks or len(landmarks) < 33:
            return None

        try:
            if side == "left":
                p_hip = landmarks[self.MP_LEFT_HIP]
                p_knee = landmarks[self.MP_LEFT_KNEE]
                p_ankle = landmarks[self.MP_LEFT_ANKLE]
            else:
                p_hip = landmarks[self.MP_RIGHT_HIP]
                p_knee = landmarks[self.MP_RIGHT_KNEE]
                p_ankle = landmarks[self.MP_RIGHT_ANKLE]

            knee_angle = GeometryUtils.calculate_angle(p_hip, p_knee, p_ankle)

            return {
                "knee_angle": knee_angle,
                "knee_point": (p_knee[1], p_knee[2]),
                "hip_point": (p_hip[1], p_hip[2])
            }

        except IndexError:
            return None

    def process_front_view(self, landmarks):
        """
        Analizuje liniowość nogi (Valgus) w widoku przednim.
        Zwraca odchylenie kolana od linii biodro-kostka.
        """
        if not landmarks or len(landmarks) < 33:
            return None

        # Domyślnie analizujemy lewą nogę
        p_hip = landmarks[self.MP_LEFT_HIP]
        p_knee = landmarks[self.MP_LEFT_KNEE]
        p_ankle = landmarks[self.MP_LEFT_ANKLE]

        # Oczekiwana pozycja X kolana (średnia z biodra i kostki)
        expected_knee_x = (p_hip[1] + p_ankle[1]) / 2
        deviation = p_knee[1] - expected_knee_x

        return {
            "valgus_deviation": deviation,
            "knee_point": (p_knee[1], p_knee[2])
        }