from src.gui.app_ui import AppUI
from src.utils.camera_handler import CameraHandler
from src.logic.pose_detector import PoseDetector
from src.logic.trainer_logic import TrainerLogic

# --- KONFIGURACJA ---
# Tutaj wpisz adres, który wyświetli Ci aplikacja IP Webcam na telefonie
# Pamiętaj o końcówce /video
ANDROID_IP = "http://10.1.4.128:8080/video"


def main():
    print("--- Inicjalizacja LungeGuard ---")

    try:
        # 1. Inicjalizacja komponentów

        print(f"Łączenie z kamerą: {ANDROID_IP} ...")

        camera = CameraHandler(ANDROID_IP)
        camera.start()

        # Sprawdzamy czy się udało połączyć
        if not camera.running:
            print("OSTRZEŻENIE: Nie udało się połączyć z telefonem. Sprawdź IP/Wi-Fi.")
            # Możesz tu dodać fallback na kamerę laptopa: camera = CameraHandler(0).start()

        detector = PoseDetector()
        logic = TrainerLogic()

        # Uwaga: Tutaj tworzymy UI. W przyszłości pewnie będziesz musiał przekazać
        # obiekt 'camera' do środka, np.: ui = AppUI(camera)
        # Na razie zostawiamy tak jak jest u kolegi.
        ui = AppUI()

        print("\nWSZYSTKIE MODUŁY ZAŁADOWANE POPRAWNIE.\n")

        # Start aplikacji
        ui.run()

        # --- SPRZĄTANIE ---
        # Gdy zamkniesz okno aplikacji, trzeba zatrzymać wątek kamery
        camera.stop()

    except Exception as e:
        print(f"BŁĄD KRYTYCZNY: {e}")


if __name__ == "__main__":
    main()