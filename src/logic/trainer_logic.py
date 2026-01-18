class TrainerLogic:
    def __init__(self):
        """
        Klasa zarządzająca stanem treningu, liczeniem powtórzeń i oceną techniki.
        """
        self.reps = 0
        self.stage = "UP"  # UP (Góra) lub DOWN (Dół)
        self.current_rep_failed = False

        # Zapamiętana wysokość biodra w pozycji stojącej (0.0 = góra ekranu, 1.0 = dół)
        self.standing_hip_y = 0.0

        # --- PROGI KALIBRACYJNE ---
        self.ANGLE_THRESHOLD_DOWN = 95
        self.ANGLE_THRESHOLD_UP = 160

        self.VALGUS_THRESHOLD = 0.03  # Koślawienie
        self.TORSO_THRESHOLD = 20  # Plecy
        self.SHIN_THRESHOLD = 40  # Kolano przód

        # Anti-Cheat: Minimalne obniżenie biodra (5% wysokości ekranu)
        self.HIP_DROP_THRESHOLD = 0.05

    def mark_error(self):
        """Oznacza obecne powtórzenie jako spalone."""
        if self.stage == "DOWN":
            self.current_rep_failed = True

    def update_reps(self, knee_angle, ankle_spread, hip_y):
        """
        Aktualizuje licznik na podstawie kąta kolana i opuszczenia biodra.
        """
        if knee_angle is None or hip_y is None:
            return self.reps, self.stage

        # FAZA 1: GÓRA (Stoisz / Wyprost)
        if knee_angle > self.ANGLE_THRESHOLD_UP:
            if self.stage == "DOWN":
                if not self.current_rep_failed:
                    self.reps += 1
                    print(f"TRENER: Rep {self.reps} OK")
                self.stage = "UP"
                self.current_rep_failed = False

            # Kalibracja wysokości biodra w staniu (bierzemy najwyższy punkt - min Y)
            if self.standing_hip_y == 0.0 or hip_y < self.standing_hip_y:
                self.standing_hip_y = hip_y

        # FAZA 2: DÓŁ (Zejście)
        elif knee_angle < self.ANGLE_THRESHOLD_DOWN:
            if self.stage == "UP":
                # SPRAWDZENIE ANTI-CHEAT:
                # Czy biodro faktycznie zjechało w dół? (Większy Y = niżej)
                current_drop = hip_y - self.standing_hip_y

                # Jeśli biodro opadło o min. 5% ekranu -> Zaliczone zejście
                if current_drop > self.HIP_DROP_THRESHOLD:
                    self.stage = "DOWN"
                    self.current_rep_failed = False
                else:
                    # Kąt mały, ale biodro wysoko -> To jest podniesienie nogi (Skip A)!
                    pass

        return self.reps, self.stage

    # --- METODY SPRAWDZAJĄCE BŁĘDY ---

    def check_valgus(self, deviation):
        if abs(deviation) > self.VALGUS_THRESHOLD:
            return True, "ZLE! (KOLANO)", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_torso(self, torso_angle):
        if torso_angle > self.TORSO_THRESHOLD:
            return True, "PLECY!", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_knee_forward(self, shin_angle, knee_angle):
        # Sprawdzamy tylko, gdy noga pracuje (jest zgięta)
        if knee_angle > 140:
            return False, "OK", (0, 255, 0)

        if shin_angle > self.SHIN_THRESHOLD:
            return True, "KOLANO (PRZOD)!", (0, 0, 255)

        return False, "OK", (0, 255, 0)

    def check_stance_width(self, ankle_spread, knee_angle):
        # Wyłączone (zwraca zawsze OK)
        return False, "OK", (0, 255, 0)