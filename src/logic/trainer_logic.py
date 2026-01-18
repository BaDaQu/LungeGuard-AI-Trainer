import time


class TrainerLogic:
    def __init__(self):
        self.reps = 0
        self.stage = "UP"
        self.current_rep_failed = False
        self.standing_hip_y = 0.0

        self.start_time = time.time()
        self.angle_history = []
        self.error_history = []

        # --- NOWOŚĆ: Synchronizacja czasu błędów ---
        self.last_error_time = {}  # Kiedy ostatnio zapisaliśmy dany typ błędu?
        self.ERROR_COOLDOWN = 1.5  # Sekundy (zapisuj błąd max raz na 1.5s)

        # Progi
        self.ANGLE_THRESHOLD_DOWN = 95
        self.ANGLE_THRESHOLD_UP = 160
        self.VALGUS_THRESHOLD = 0.03
        self.TORSO_THRESHOLD = 20
        self.SHIN_THRESHOLD = 40
        self.HIP_DROP_THRESHOLD = 0.05
        self.MIN_ANKLE_SPREAD = 0.15

    def _get_time(self):
        return round(time.time() - self.start_time, 2)

    def set_difficulty(self, level):
        print(f"TRENER: Ustawiono poziom {level}")
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

    def mark_error(self, error_type="General"):
        """
        Rejestruje błąd. Zwraca True, jeśli błąd został dopisany do historii (minął cooldown).
        """
        current_time = self._get_time()
        last_time = self.last_error_time.get(error_type, -10.0)

        # 1. Sprawdzamy Cooldown (żeby nie było 2 kropek obok siebie)
        if current_time - last_time < self.ERROR_COOLDOWN:
            return False  # Ignorujemy (za często)

        # 2. Zapisujemy do historii wykresu
        self.error_history.append((current_time, error_type))
        self.last_error_time[error_type] = current_time

        # 3. Spalamy powtórzenie
        if self.stage == "DOWN":
            self.current_rep_failed = True

        return True  # Sygnał dla bazy danych: "Zapisz mnie!"

    def update_reps(self, knee_angle, ankle_spread, hip_y):
        if knee_angle is None: return self.reps, self.stage

        self.angle_history.append((self._get_time(), knee_angle))

        if knee_angle > self.ANGLE_THRESHOLD_UP:
            if self.stage == "DOWN":
                if not self.current_rep_failed:
                    self.reps += 1
                    print(f"TRENER: Rep {self.reps} OK")
                self.stage = "UP"
                self.current_rep_failed = False

            if hip_y is not None:
                if self.standing_hip_y == 0.0 or hip_y < self.standing_hip_y:
                    self.standing_hip_y = hip_y

        elif knee_angle < self.ANGLE_THRESHOLD_DOWN:
            if self.stage == "UP":
                if hip_y is not None:
                    current_drop = hip_y - self.standing_hip_y
                    if current_drop > self.HIP_DROP_THRESHOLD:
                        self.stage = "DOWN"
                        self.current_rep_failed = False

        return self.reps, self.stage

    # Checks
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