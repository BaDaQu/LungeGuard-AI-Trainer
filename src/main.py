import cv2
from src.utils.camera_handler import CameraHandler


def main():
    print("--- LungeGuard: Test Dwóch Kamer (Issue #3) ---")

    # ================= KONFIGURACJA =================
    # 1. Kamera Frontowa (Laptop)
    FRONT_CAM_ID = 0

    # 2. Kamera Boczna (Telefon - IP Webcam)

    SIDE_CAM_URL = "http://192.168.33.15:8080/video"
    # ================================================

    print("Inicjalizacja kamer...")

    # Tworzymy instancje handlerów
    cam_front = CameraHandler(source=FRONT_CAM_ID, name="FRONT")
    cam_side = CameraHandler(source=SIDE_CAM_URL, name="SIDE")

    # Uruchamiamy wątki
    cam_front.start()
    cam_side.start()

    print("\nOczekiwanie na sygnał wideo... (Naciśnij 'q' aby wyjść)\n")

    try:
        while True:
            # Pobieramy klatki
            frame_front = cam_front.get_frame()
            frame_side = cam_side.get_frame()

            # Wyświetlanie FRONT (Laptop)
            if frame_front is not None:
                # Odbicie lustrzane dla naturalnego odczucia
                frame_front = cv2.flip(frame_front, 1)
                cv2.imshow("Kamera FRONT (Laptop)", frame_front)

            # Wyświetlanie SIDE (Telefon)
            if frame_side is not None:
                # Skalowanie obrazu z telefonu (często są ogromne, np. 4K)
                frame_side = cv2.resize(frame_side, (640, 480))
                cv2.imshow("Kamera SIDE (Telefon)", frame_side)

            # Wyjście klawiszem 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Przerwano przez użytkownika.")
    finally:
        print("Zamykanie zasobów...")
        cam_front.stop()
        cam_side.stop()
        cv2.destroyAllWindows()
        print("Koniec testu.")


if __name__ == "__main__":
    main()