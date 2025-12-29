from src.gui.app_ui import AppUI
from src.utils.camera_handler import CameraHandler
from src.logic.pose_detector import PoseDetector
from src.logic.trainer_logic import TrainerLogic


def main():
    print("--- Inicjalizacja LungeGuard ---")

    # 1. Inicjalizacja komponentów (Architektura)
    # Tworzymy obiekty klas, żeby sprawdzić czy importy działają
    try:
        camera = CameraHandler(0)
        detector = PoseDetector()
        logic = TrainerLogic()
        ui = AppUI()

        print("\nWSZYSTKIE MODUŁY ZAŁADOWANE POPRAWNIE.\n")

        # Start aplikacji
        ui.run()

    except Exception as e:
        print(f"BŁĄD KRYTYCZNY: {e}")


if __name__ == "__main__":
    main()