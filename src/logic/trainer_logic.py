class TrainerLogic:
    def __init__(self):
        """
        Klasa zarządzająca stanem treningu.
        Liczy powtórzenia na podstawie cyklu ruchu (Góra -> Dół -> Góra).
        """
        self.reps = 0
        self.stage = "UP"  # Dostępne stany: "UP" (góra), "DOWN" (dół)

        # Progi kątowe (kalibracja)
        self.ANGLE_THRESHOLD_DOWN = 95  # Poniżej tego kąta uznajemy zejście w dół
        self.ANGLE_THRESHOLD_UP = 160  # Powyżej tego kąta uznajemy wyprost

    def update_reps(self, knee_angle):
        """
        Aktualizuje licznik powtórzeń na podstawie kąta kolana.
        :param knee_angle: Aktualny kąt zgięcia kolana.
        :return: (liczba_powtórzeń, aktualny_stan)
        """
        if knee_angle is None:
            return self.reps, self.stage

        # Logika maszyny stanów
        if knee_angle > self.ANGLE_THRESHOLD_UP:
            # Jeśli wróciliśmy do góry, a wcześniej byliśmy na dole -> zaliczamy powtórzenie
            if self.stage == "DOWN":
                self.reps += 1
                self.stage = "UP"
                print(f"TRENER: Powtórzenie zaliczone! Razem: {self.reps}")

        elif knee_angle < self.ANGLE_THRESHOLD_DOWN:
            # Jeśli zeszliśmy nisko -> zmieniamy stan na DOWN
            if self.stage == "UP":
                self.stage = "DOWN"

        return self.reps, self.stage

    def reset(self):
        """Zeruje licznik."""
        self.reps = 0
        self.stage = "UP"