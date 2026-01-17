from src.logic.geometry_utils import GeometryUtils


class SkeletonProcessor:
    def __init__(self):
        """
        Klasa interpretująca surowe punkty szkieletu na dane analityczne.
        """
        self.MP_LEFT_SHOULDER = 11
        self.MP_RIGHT_SHOULDER = 12
        self.MP_LEFT_HIP = 23
        self.MP_RIGHT_HIP = 24
        self.MP_LEFT_KNEE = 25
        self.MP_RIGHT_KNEE = 26
        self.MP_LEFT_ANKLE = 27
        self.MP_RIGHT_ANKLE = 28

    def process_side_view(self, landmarks, side="left"):
        """
        Analizuje widok boczny. Dodano obliczanie rozstawu stóp (spread) i wysokości biodra.
        """
        if not landmarks or len(landmarks) < 33:
            return None

        try:
            # Pobieramy punkty dla wybranej strony (głównej)
            if side == "left":
                p_shoulder = landmarks[self.MP_LEFT_SHOULDER]
                p_hip = landmarks[self.MP_LEFT_HIP]
                p_knee = landmarks[self.MP_LEFT_KNEE]
                p_ankle = landmarks[self.MP_LEFT_ANKLE]
            else:
                p_shoulder = landmarks[self.MP_RIGHT_SHOULDER]
                p_hip = landmarks[self.MP_RIGHT_HIP]
                p_knee = landmarks[self.MP_RIGHT_KNEE]
                p_ankle = landmarks[self.MP_RIGHT_ANKLE]

            # Pobieramy kostkę DRUGIEJ nogi, żeby policzyć rozstaw
            p_ankle_left = landmarks[self.MP_LEFT_ANKLE]
            p_ankle_right = landmarks[self.MP_RIGHT_ANKLE]

            # Obliczenia podstawowe
            knee_angle = GeometryUtils.calculate_angle(p_hip, p_knee, p_ankle)

            p_vertical_hip = [0, p_hip[1], p_hip[2] - 0.5, 0]
            torso_angle = GeometryUtils.calculate_angle(p_shoulder, p_hip, p_vertical_hip)

            p_vertical_ankle = [0, p_ankle[1], p_ankle[2] - 0.5, 0]
            shin_angle = GeometryUtils.calculate_angle(p_knee, p_ankle, p_vertical_ankle)

            # NOWOŚĆ: Obliczenie rozstawu stóp w osi X (normalized coordinates)
            ankle_spread = abs(p_ankle_left[1] - p_ankle_right[1])

            return {
                "knee_angle": knee_angle,
                "torso_angle": torso_angle,
                "shin_angle": shin_angle,
                "ankle_spread": ankle_spread,  # Czy nogi są szeroko?
                "hip_y": p_hip[2],  # Wysokość biodra (im więcej tym niżej)
                "knee_point": (p_knee[1], p_knee[2]),
                "hip_point": (p_hip[1], p_hip[2]),
                "shoulder_point": (p_shoulder[1], p_shoulder[2]),
                "ankle_point": (p_ankle[1], p_ankle[2])
            }

        except IndexError:
            return None

    def process_front_view(self, landmarks):
        """Analiza Valgus w widoku przednim."""
        if not landmarks or len(landmarks) < 33:
            return None

        p_hip = landmarks[self.MP_LEFT_HIP]
        p_knee = landmarks[self.MP_LEFT_KNEE]
        p_ankle = landmarks[self.MP_LEFT_ANKLE]

        expected_knee_x = (p_hip[1] + p_ankle[1]) / 2
        deviation = p_knee[1] - expected_knee_x

        return {
            "valgus_deviation": deviation,
            "knee_point": (p_knee[1], p_knee[2])
        }