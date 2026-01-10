import cv2
import mediapipe as mp


class PoseDetector:
    def __init__(self, mode=False, complexity=1, smooth_landmarks=True,
                 detection_con=0.5, track_con=0.5):
        """
        Inicjalizacja modelu MediaPipe Pose.
        :param complexity: Złożoność modelu (0=Lite, 1=Full, 2=Heavy). 1 jest optymalne.
        """
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=mode,
            model_complexity=complexity,
            smooth_landmarks=smooth_landmarks,
            min_detection_confidence=detection_con,
            min_tracking_confidence=track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def find_pose(self, img, draw=True):
        """
        Wykrywa pozę na klatce wideo i rysuje szkielet.
        :param img: Klatka z OpenCV (BGR).
        :param draw: Czy rysować linie na obrazie.
        :return: (img, results) - obraz z rysunkiem i obiekt wyników.
        """
        # 1. Konwersja BGR -> RGB (wymagane przez MediaPipe)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # 2. Przetwarzanie (Detekcja)
        # To tutaj dzieje się "magia" AI
        self.results = self.pose.process(img_rgb)

        # 3. Rysowanie
        if self.results.pose_landmarks and draw:
            self.mp_draw.draw_landmarks(
                img,
                self.results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
            )

        return img, self.results

    def get_landmarks(self):
        """Zwraca listę punktów (id, x, y, z) lub None jeśli nie wykryto."""
        if not self.results.pose_landmarks:
            return None

        landmarks = []
        for id, lm in enumerate(self.results.pose_landmarks.landmark):
            h, w, c = 0, 0, 0  # Będziemy to uzupełniać w kolejnym sprincie (math)
            landmarks.append([id, lm.x, lm.y, lm.z])

        return landmarks