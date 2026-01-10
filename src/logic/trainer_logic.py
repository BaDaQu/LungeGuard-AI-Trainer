class TrainerLogic:
    def __init__(self):
        """
        Klasa zarządzająca stanem treningu i oceną techniki.
        """
        self.reps = 0
        self.stage = "UP"

        # Flaga, która pamięta, czy w trakcie obecnego powtórzenia wystąpił błąd
        self.current_rep_failed = False

        self.ANGLE_THRESHOLD_DOWN = 95
        self.ANGLE_THRESHOLD_UP = 160
        self.VALGUS_THRESHOLD = 0.03
        self.TORSO_THRESHOLD = 20

    def mark_error(self):
        """
        Metoda wywoływana, gdy wykryto błąd techniczny (plecy lub kolano).
        Oznacza obecne powtórzenie jako 'spalone'.
        """
        if self.stage == "DOWN":
            self.current_rep_failed = True

    def update_reps(self, knee_angle):
        """
        Aktualizuje licznik powtórzeń, biorąc pod uwagę błędy techniczne.
        """
        if knee_angle is None:
            return self.reps, self.stage

        if knee_angle > self.ANGLE_THRESHOLD_UP:
            if self.stage == "DOWN":
                # Sprawdzamy, czy powtórzenie było czyste
                if not self.current_rep_failed:
                    self.reps += 1
                    print(f"TRENER: Powtórzenie {self.reps} zaliczone.")
                else:
                    print("TRENER: Powtórzenie niezaliczone (BŁĄD TECHNICZNY).")

                # Resetujemy stan i flagę błędu na nowe powtórzenie
                self.stage = "UP"
                self.current_rep_failed = False

        elif knee_angle < self.ANGLE_THRESHOLD_DOWN:
            if self.stage == "UP":
                self.stage = "DOWN"
                # Na wszelki wypadek resetujemy flagę przy zejściu w dół
                self.current_rep_failed = False

        return self.reps, self.stage

    def check_valgus(self, deviation):
        """Analiza Valgus."""
        if abs(deviation) > self.VALGUS_THRESHOLD:
            return True, "ZLE! (KOLANO)", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_torso(self, torso_angle):
        """Analiza Pleców."""
        if torso_angle > self.TORSO_THRESHOLD:
            return True, "PLECY!", (0, 0, 255)
        return False, "OK", (0, 255, 0)