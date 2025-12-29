import mediapipe as mp
import cv2

class PoseDetector:
    def __init__(self):
        """Inicjalizacja modelu MediaPipe."""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.mp_draw = mp.solutions.drawing_utils
        print("DEBUG: PoseDetector zainicjalizowany.")

    def process_image(self, img):
        """
        Przetwarza klatkę i zwraca punkty (landmarks).
        :param img: Klatka z OpenCV.
        :return: Obraz z narysowanym szkieletem.
        """
        # Tu będzie właściwa detekcja
        return img