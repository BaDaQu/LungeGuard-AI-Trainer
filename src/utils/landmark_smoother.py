class LandmarkSmoother:
    def __init__(self, alpha=0.65):
        """
        Klasa wygładzająca drgania punktów szkieletu (jitter reduction).
        Używa algorytmu Exponential Moving Average (EMA).

        :param alpha: Współczynnik wygładzania (0.0 - 1.0).
                      Większy = mniejsze wygładzanie (szybsza reakcja).
                      Mniejszy = mocniejsze wygładzanie (płynniejszy ruch).
        """
        self.alpha = alpha
        self.prev_landmarks = None

    def smooth(self, current_landmarks):
        """
        Wygładza listę punktów.
        :param current_landmarks: Lista [id, x, y, z] z PoseDetector.
        :return: Wygładzona lista w tym samym formacie.
        """
        if not current_landmarks:
            self.prev_landmarks = None
            return None

        # Jeśli nie ma historii, zwracamy obecne (pierwsza klatka)
        if self.prev_landmarks is None:
            self.prev_landmarks = current_landmarks
            return current_landmarks

        smoothed_landmarks = []
        for i, curr_lm in enumerate(current_landmarks):
            # Pobieramy poprzedni stan tego samego punktu
            # Zakładamy, że kolejność punktów jest stała (gwarantowane przez MediaPipe)
            try:
                prev_lm = self.prev_landmarks[i]

                # Wygładzamy współrzędne x, y, z
                smooth_x = self.alpha * curr_lm[1] + (1 - self.alpha) * prev_lm[1]
                smooth_y = self.alpha * curr_lm[2] + (1 - self.alpha) * prev_lm[2]
                smooth_z = self.alpha * curr_lm[3] + (1 - self.alpha) * prev_lm[3]

                smoothed_landmarks.append([curr_lm[0], smooth_x, smooth_y, smooth_z])
            except IndexError:
                # Zabezpieczenie na wypadek niespójności danych
                smoothed_landmarks.append(curr_lm)

        self.prev_landmarks = smoothed_landmarks
        return smoothed_landmarks