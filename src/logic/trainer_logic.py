import time


class TrainerLogic:
    def __init__(self):
        self.reps = 0
        self.stage = "UP"
        self.current_rep_failed = False
        self.standing_hip_y = 0.0

        # Progi
        self.ANGLE_THRESHOLD_DOWN = 95
        self.ANGLE_THRESHOLD_UP = 160
        self.VALGUS_THRESHOLD = 0.03
        self.TORSO_THRESHOLD = 20
        self.SHIN_THRESHOLD = 40
        self.MIN_ANKLE_SPREAD = 0.15

        # --- NOWOŚĆ: HISTORIA DANYCH ---
        self.start_time = time.time()
        # Lista krotek: (czas_od_startu, kat_kolana)
        self.angle_history = []
        # Lista krotek: (czas_od_startu, typ_bledu)
        self.error_history = []

    def _get_time(self):
        return round(time.time() - self.start_time, 2)

    def mark_error(self, error_type="General"):
        # Zapisujemy błąd do historii wykresu
        if self.stage == "DOWN":
            self.current_rep_failed = True
            # Dodajemy wpis tylko jeśli to nowy moment (unikamy spamu na wykresie)
            if not self.error_history or self.error_history[-1][0] != self._get_time():
                self.error_history.append((self._get_time(), error_type))

    def update_reps(self, knee_angle, ankle_spread, hip_y):
        if knee_angle is None: return self.reps, self.stage

        # --- REJESTRACJA DANYCH ---
        self.angle_history.append((self._get_time(), knee_angle))
        # --------------------------

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
                if current_drop > 0.05:  # HIP_DROP_THRESHOLD hardcoded for simplicity here
                    self.stage = "DOWN"
                    self.current_rep_failed = False

        return self.reps, self.stage

    # --- METODY SPRAWDZAJĄCE (Bez zmian logicznych) ---
    def check_valgus(self, deviation):
        if abs(deviation) > self.VALGUS_THRESHOLD:
            return True, "ZLE! (KOLANO)", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_torso(self, torso_angle):
        if torso_angle > self.TORSO_THRESHOLD:
            return True, "PLECY!", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_knee_forward(self, shin_angle, knee_angle):
        if knee_angle > 140: return False, "OK", (0, 255, 0)
        if shin_angle > self.SHIN_THRESHOLD:
            return True, "KOLANO (PRZOD)!", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_stance_width(self, ankle_spread, knee_angle):
        return False, "OK", (0, 255, 0)

    def set_difficulty(self, level):
        """Metoda z Issue 17 - musi tu być."""
        if level == "Easy":
            self.ANGLE_THRESHOLD_DOWN = 100
            self.TORSO_THRESHOLD = 30
            self.SHIN_THRESHOLD = 50
            self.VALGUS_THRESHOLD = 0.05
        elif level == "Hard":
            self.ANGLE_THRESHOLD_DOWN = 90
            self.TORSO_THRESHOLD = 10
            self.SHIN_THRESHOLD = 30
            self.VALGUS_THRESHOLD = 0.02
        else:
            self.ANGLE_THRESHOLD_DOWN = 95
            self.TORSO_THRESHOLD = 20
            self.SHIN_THRESHOLD = 40
            self.VALGUS_THRESHOLD = 0.03