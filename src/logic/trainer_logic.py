class TrainerLogic:
    def __init__(self):
        """
        Klasa zarządzająca stanem treningu i oceną techniki.
        """
        self.reps = 0
        self.stage = "UP"
        self.current_rep_failed = False

        # Progi licznika
        self.ANGLE_THRESHOLD_DOWN = 95
        self.ANGLE_THRESHOLD_UP = 160

        # Progi błędów
        self.VALGUS_THRESHOLD = 0.03
        self.TORSO_THRESHOLD = 20
        self.SHIN_THRESHOLD = 40

        # NOWOŚĆ: Minimalny rozstaw stóp, aby uznać to za wykrok
        # 0.15 oznacza, że stopy muszą być oddalone o 15% szerokości ekranu
        self.MIN_ANKLE_SPREAD = 0.15

    def mark_error(self):
        """Oznacza powtórzenie jako spalone."""
        if self.stage == "DOWN":
            self.current_rep_failed = True

    def update_reps(self, knee_angle, ankle_spread):
        """
        Aktualizuje licznik. Wymaga poprawnego kąta ORAZ rozstawu nóg.
        :param knee_angle: Kąt zgięcia.
        :param ankle_spread: Rozstaw kostek w osi X.
        """
        if knee_angle is None:
            return self.reps, self.stage

        # Stan UP (Wyprost)
        if knee_angle > self.ANGLE_THRESHOLD_UP:
            if self.stage == "DOWN":
                if not self.current_rep_failed:
                    self.reps += 1
                    print(f"TRENER: Powtórzenie {self.reps} zaliczone.")
                else:
                    print("TRENER: Powtórzenie niezaliczone (BŁĄD TECHNICZNY).")

                self.stage = "UP"
                self.current_rep_failed = False

        # Stan DOWN (Zejście)
        elif knee_angle < self.ANGLE_THRESHOLD_DOWN:
            # NOWOŚĆ: Sprawdzamy czy to nie jest oszustwo (np. Skip A)
            if ankle_spread > self.MIN_ANKLE_SPREAD:
                if self.stage == "UP":
                    self.stage = "DOWN"
                    self.current_rep_failed = False
            else:
                # Jeśli kąt jest dobry, ale nogi są wąsko -> to nie jest wykrok!
                # Możemy opcjonalnie wypisać debug, że wykryto "oszustwo"
                pass

        return self.reps, self.stage

    def check_valgus(self, deviation):
        if abs(deviation) > self.VALGUS_THRESHOLD:
            return True, "ZLE! (KOLANO)", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_torso(self, torso_angle):
        if torso_angle > self.TORSO_THRESHOLD:
            return True, "PLECY!", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_knee_forward(self, shin_angle):
        if shin_angle > self.SHIN_THRESHOLD:
            return True, "KOLANO (PRZOD)!", (0, 0, 255)
        return False, "OK", (0, 255, 0)