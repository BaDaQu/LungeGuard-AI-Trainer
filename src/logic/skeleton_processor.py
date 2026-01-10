from src.logic.geometry_utils import GeometryUtils


class SkeletonProcessor:
    def __init__(self):
        """
        Klasa interpretująca surowe punkty szkieletu na dane analityczne.
        Zawiera indeksy stawów z modelu MediaPipe Pose.
        """
        self.MP_LEFT_SHOULDER = 11
        self.MP_LEFT_HIP = 23
        self.MP_LEFT_KNEE = 25
        self.MP_LEFT_ANKLE = 27

        self.MP_RIGHT_SHOULDER = 12
        self.MP_RIGHT_HIP = 24
        self.MP_RIGHT_KNEE = 26
        self.MP_RIGHT_ANKLE = 28

    def process_side_view(self, landmarks, side="left"):
        """
        Oblicza kąt zgięcia kolana oraz kąt pochylenia tułowia.
        """
        if not landmarks or len(landmarks) < 33:
            return None

        try:
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

            # Obliczenie kąta kolana (Biodro-Kolano-Kostka)
            knee_angle = GeometryUtils.calculate_angle(p_hip, p_knee, p_ankle)

            # Obliczenie kąta pochylenia tułowia
            # Tworzymy wirtualny punkt pionowo nad biodrem, aby mieć punkt odniesienia
            p_vertical = [0, p_hip[1], p_hip[2] - 0.5, 0]

            # Kąt między odcinkiem Bark-Biodro a pionem
            torso_angle = GeometryUtils.calculate_angle(p_shoulder, p_hip, p_vertical)

            return {
                "knee_angle": knee_angle,
                "torso_angle": torso_angle,
                "knee_point": (p_knee[1], p_knee[2]),
                "hip_point": (p_hip[1], p_hip[2]),
                "shoulder_point": (p_shoulder[1], p_shoulder[2])
            }

        except IndexError:
            return None

    def process_front_view(self, landmarks):
        """
        Analizuje liniowość nogi (Valgus) w widoku przednim.
        """
        if not landmarks or len(landmarks) < 33:
            return None

        p_hip = landmarks[self.MP_LEFT_HIP]
        p_knee = landmarks[self.MP_LEFT_KNEE]
        p_ankle = landmarks[self.MP_LEFT_ANKLE]

        # Sprawdzenie czy kolano znajduje się w połowie dystansu X między biodrem a kostką
        expected_knee_x = (p_hip[1] + p_ankle[1]) / 2
        deviation = p_knee[1] - expected_knee_x

        return {
            "valgus_deviation": deviation,
            "knee_point": (p_knee[1], p_knee[2])
        }