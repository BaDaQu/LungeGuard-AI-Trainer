import cv2
import time
from src.utils.camera_handler import CameraHandler
from src.logic.pose_detector import PoseDetector


def main():
    print("--- LungeGuard: Test Detekcji AI (Issue #4) ---")

    # ================= KONFIGURACJA =================
    FRONT_CAM_ID = 0
    # Wpisz tutaj SWOJE IP z telefonu:
    SIDE_CAM_URL = "http://192.168.33.15:8080/video"
    # ================================================

    print("Inicjalizacja kamer...")
    cam_front = CameraHandler(source=FRONT_CAM_ID, name="FRONT")
    cam_side = CameraHandler(source=SIDE_CAM_URL, name="SIDE")

    print("Inicjalizacja modeli AI...")
    # Tworzymy DWA osobne detektory, żeby nie mieszać kontekstu śledzenia
    detector_front = PoseDetector(complexity=1)
    detector_side = PoseDetector(complexity=1)

    cam_front.start()
    cam_side.start()

    # Czas na rozgrzanie kamer
    time.sleep(2)
    print("Start analizy! Naciśnij 'q' aby wyjść.")

    try:
        while True:
            # 1. Pobranie klatek
            frame_front = cam_front.get_frame()
            frame_side = cam_side.get_frame()

            # 2. Przetwarzanie FRONT
            if frame_front is not None:
                # Detekcja (zwraca obraz z narysowanym szkieletem)
                frame_front, _ = detector_front.find_pose(frame_front)

                # Odbicie lustrzane i wyświetlenie
                frame_front = cv2.flip(frame_front, 1)
                cv2.imshow("AI FRONT", frame_front)

            # 3. Przetwarzanie SIDE
            if frame_side is not None:
                # Detekcja
                frame_side, _ = detector_side.find_pose(frame_side)

                # Skalowanie i wyświetlenie
                frame_side = cv2.resize(frame_side, (640, 480))
                cv2.imshow("AI SIDE", frame_side)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        print("Sprzątanie...")
        cam_front.stop()
        cam_side.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()