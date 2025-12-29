class TrainerLogic:
    def __init__(self):
        """Zarządza stanem ćwiczenia (liczenie powtórzeń, wykrywanie błędów)."""
        self.reps = 0
        self.current_state = "START"  # START, DOWN, UP
        self.errors = []
        print("DEBUG: Logika trenera gotowa.")

    def analyze_pose(self, landmarks):
        """Analizuje pozycję ciała i zwraca feedback."""
        # Tu wyląduje matematyka (kąty)
        pass