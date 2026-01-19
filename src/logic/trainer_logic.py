import time


class TrainerLogic:
    def __init__(self):
        """
        Mózg trenera: Licznik, Anti-Cheat, Poziomy trudności i Historia.
        """
        self.reps = 0
        self.stage = "UP"  # UP (Góra) lub DOWN (Dół)

        self.standing_hip_y = 0.0

        # Historia do wykresów
        self.start_time = time.time()
        self.angle_history = []
        self.error_history = []

        # --- ZMIANA: Obsługa czasu błędu ---
        self.last_technique_error_time = 0.0  # Kiedy wystąpił ostatni błąd techniczny?
        self.ERROR_PENALTY_TIME = 0.4  # Ile sekund blokady po błędzie

        # Domyślne progi (Medium)
        self.ANGLE_THRESHOLD_DOWN = 95
        self.ANGLE_THRESHOLD_UP = 160
        self.VALGUS_THRESHOLD = 0.03
        self.TORSO_THRESHOLD = 20
        self.SHIN_THRESHOLD = 40
        self.HIP_DROP_THRESHOLD = 0.05
        self.MIN_ANKLE_SPREAD = 0.15

        # Synchronizacja zapisu do bazy i wykresu
        self.last_error_log_time = {}
        self.ERROR_COOLDOWN = 1.5

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
        else:  # Medium
            self.ANGLE_THRESHOLD_DOWN = 95
            self.TORSO_THRESHOLD = 20
            self.SHIN_THRESHOLD = 40
            self.VALGUS_THRESHOLD = 0.03

    def mark_error(self, error_type="General"):
        """
        Rejestruje błąd techniczny.
        1. Nakłada karę czasową (0.4s).
        2. Zapisuje do historii (wykres/baza) z uwzględnieniem cooldownu logowania.
        Zwraca True, jeśli błąd należy zapisać w bazie danych.
        """
        current_time = self._get_time()
        real_time = time.time()

        # --- 1. NAKŁADAMY BLOKADĘ CZASOWĄ NA LICZNIK ---
        self.last_technique_error_time = real_time
        # -----------------------------------------------

        # 2. Logika zapisu do wykresu/bazy (żeby nie spamować logami)
        last_log = self.last_error_log_time.get(error_type, -10.0)

        if current_time - last_log < self.ERROR_COOLDOWN:
            return False  # Za często, nie loguj do bazy

        # Zapis do historii wykresu
        self.error_history.append((current_time, error_type))
        self.last_error_log_time[error_type] = current_time

        return True  # Sygnał: Zapisz błąd w bazie SQL

    def update_reps(self, knee_angle, ankle_spread, hip_y):
        if knee_angle is None: return self.reps, self.stage

        self.angle_history.append((self._get_time(), knee_angle))

        # FAZA 1: Wyprost (Góra) - Tu zaliczamy powtórzenie
        if knee_angle > self.ANGLE_THRESHOLD_UP:
            if self.stage == "DOWN":

                # --- ZMIANA: SPRAWDZAMY CZAS OD OSTATNIEGO BŁĘDU ---
                time_since_error = time.time() - self.last_technique_error_time

                if time_since_error > self.ERROR_PENALTY_TIME:
                    self.reps += 1
                    print(f"TRENER: Rep {self.reps} OK")
                else:
                    print(f"TRENER: Rep odrzucony (Błąd {time_since_error:.2f}s temu)")
                # ---------------------------------------------------

                self.stage = "UP"

            # Kalibracja biodra
            if hip_y is not None:
                if self.standing_hip_y == 0.0 or hip_y < self.standing_hip_y:
                    self.standing_hip_y = hip_y

        # FAZA 2: Zejście (Dół)
        elif knee_angle < self.ANGLE_THRESHOLD_DOWN:
            if self.stage == "UP":
                # Anti-Cheat: Hip Drop
                if hip_y is not None:
                    current_drop = hip_y - self.standing_hip_y
                    if current_drop > self.HIP_DROP_THRESHOLD:
                        self.stage = "DOWN"

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
        if knee_angle > 140: return False, "OK", (0, 255, 0)
        if shin_angle > self.SHIN_THRESHOLD:
            return True, "KOLANO (PRZOD)!", (0, 0, 255)
        return False, "OK", (0, 255, 0)

    def check_stance_width(self, ankle_spread, knee_angle):
        return False, "OK", (0, 255, 0)