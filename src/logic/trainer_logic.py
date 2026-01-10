class TrainerLogic:
    def __init__(self):
        """
        Klasa zarządzająca stanem treningu i oceną techniki.
        """
        self.reps = 0
        self.stage = "UP"
        self.current_rep_failed = False

        # Progi kątowe dla licznika (Góra/Dół)
        self.ANGLE_THRESHOLD_DOWN = 95
        self.ANGLE_THRESHOLD_UP = 160

        # Progi błędów
        self.VALGUS_THRESHOLD = 0.03
        self.TORSO_THRESHOLD = 20
        self.SHIN_THRESHOLD = 40

    def mark_error(self):
        """Oznacza powtórzenie jako spalone."""
        if self.stage == "DOWN":
            self.current_rep_failed = True

    def update_reps(self, knee_angle):
        """Aktualizuje licznik powtórzeń."""
        if knee_angle is None:
            return self.reps, self.stage

        if knee_angle > self.ANGLE_THRESHOLD_UP:
            if self.stage == "DOWN":
                if not self.current_rep_failed:
                    self.reps += 1
                    print(f"TRENER: Powtórzenie {self.reps} zaliczone.")
                else:
                    print("TRENER: Powtórzenie niezaliczone (BŁĄD TECHNICZNY).")

                self.stage = "UP"
                self.current_rep_failed = False

        elif knee_angle < self.ANGLE_THRESHOLD_DOWN:
            if self.stage == "UP":
                self.stage = "DOWN"
                self.current_rep_failed = False

        return self.reps, self.stage

    def check_valgus(self, deviation):
        """Analiza koślawienia kolana."""
        if abs(deviation) > self.VALGUS_THRESHOLD:
            return True, "ZLE! (KOLANO)", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_torso(self, torso_angle):
        """Analiza pochylenia pleców."""
        if torso_angle > self.TORSO_THRESHOLD:
            return True, "PLECY!", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_knee_forward(self, shin_angle):
        """Analiza wysunięcia kolana (kąt piszczeli)."""
        if shin_angle > self.SHIN_THRESHOLD:
            return True, "KOLANO (PRZOD)!", (0, 0, 255)
        return False, "OK", (0, 255, 0)