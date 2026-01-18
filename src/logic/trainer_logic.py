class TrainerLogic:
    def __init__(self):
        self.reps = 0
        self.stage = "UP"
        self.current_rep_failed = False
        self.standing_hip_y = 0.0

        # Domyślne progi (Poziom "Normalny")
        self.ANGLE_THRESHOLD_DOWN = 95
        self.ANGLE_THRESHOLD_UP = 160
        self.VALGUS_THRESHOLD = 0.03
        self.TORSO_THRESHOLD = 20
        self.SHIN_THRESHOLD = 40
        self.HIP_DROP_THRESHOLD = 0.05

    def set_difficulty(self, level):
        """
        Zmienia progi w zależności od poziomu trudności.
        :param level: "Easy", "Medium", "Hard"
        """
        print(f"TRENER: Ustawiono poziom {level}")
        if level == "Easy":
            # Łatwiej zaliczyć (płytszy przysiad), trudniej o błąd
            self.ANGLE_THRESHOLD_DOWN = 100  # Wystarczy zejść do 100 stopni
            self.TORSO_THRESHOLD = 30  # Można się bardziej pochylić
            self.SHIN_THRESHOLD = 50  # Kolano może iść bardziej w przód
            self.VALGUS_THRESHOLD = 0.05  # Większa tolerancja na koślawienie

        elif level == "Hard":
            # Wyśrubowane normy
            self.ANGLE_THRESHOLD_DOWN = 90  # Trzeba zejść nisko
            self.TORSO_THRESHOLD = 10  # Plecy idealnie proste
            self.SHIN_THRESHOLD = 30  # Pilnuj kolana
            self.VALGUS_THRESHOLD = 0.02  # Minimalna tolerancja

        else:  # Medium (Default)
            self.ANGLE_THRESHOLD_DOWN = 95
            self.TORSO_THRESHOLD = 20
            self.SHIN_THRESHOLD = 40
            self.VALGUS_THRESHOLD = 0.03

    def mark_error(self):
        if self.stage == "DOWN":
            self.current_rep_failed = True

    def update_reps(self, knee_angle, ankle_spread, hip_y):
        if knee_angle is None or hip_y is None:
            return self.reps, self.stage

        if knee_angle > self.ANGLE_THRESHOLD_UP:
            if self.stage == "DOWN":
                if not self.current_rep_failed:
                    self.reps += 1
                    print(f"TRENER: Rep {self.reps} OK")
                self.stage = "UP"
                self.current_rep_failed = False

            if self.standing_hip_y == 0.0 or hip_y < self.standing_hip_y:
                self.standing_hip_y = hip_y

        elif knee_angle < self.ANGLE_THRESHOLD_DOWN:
            if self.stage == "UP":
                current_drop = hip_y - self.standing_hip_y
                if current_drop > self.HIP_DROP_THRESHOLD:
                    self.stage = "DOWN"
                    self.current_rep_failed = False

        return self.reps, self.stage

    def check_valgus(self, deviation):
        if abs(deviation) > self.VALGUS_THRESHOLD:
            return True, "ZLE! (KOLANO)", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_torso(self, torso_angle):
        if torso_angle > self.TORSO_THRESHOLD:
            return True, "PLECY!", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_knee_forward(self, shin_angle, knee_angle):
        if knee_angle > 140:
            return False, "OK", (0, 255, 0)
        if shin_angle > self.SHIN_THRESHOLD:
            return True, "KOLANO (PRZOD)!", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_stance_width(self, ankle_spread, knee_angle):
        return False, "OK", (0, 255, 0)