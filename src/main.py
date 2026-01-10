import cv2
import time
from src.utils.camera_handler import CameraHandler
from src.logic.pose_detector import PoseDetector
from src.logic.geometry_utils import GeometryUtils


def main():
    print("--- LungeGuard: Test Matematyki (Issue #5) ---")

    # ================= KONFIGURACJA =================
    FRONT_CAM_ID = 0
    # Twoje IP z telefonu:
    SIDE_CAM_URL = "http://192.168.33.15:8080/video"
    # ================================================

    print("Inicjalizacja...")
    cam_front = CameraHandler(source=FRONT_CAM_ID, name="FRONT")
    cam_side = CameraHandler(source=SIDE_CAM_URL, name="SIDE")

    # complexity=0 dla szybkości, 1 dla dokładności
    detector_front = PoseDetector(complexity=1)
    detector_side = PoseDetector(complexity=1)

    cam_front.start()
    cam_side.start()
    time.sleep(2)  # Rozgrzewka

    print("Analiza kątów! Naciśnij 'q' aby wyjść.")

    try:
        while True:
            frame_front = cam_front.get_frame()
            frame_side = cam_side.get_frame()

            # --- ANALIZA FRONT (Tutaj zazwyczaj patrzymy na koślawienie) ---
            if frame_front is not None:
                frame_front, _ = detector_front.find_pose(frame_front)
                frame_front = cv2.flip(frame_front, 1)
                cv2.imshow("FRONT (Analiza)", frame_front)

            # --- ANALIZA SIDE (Tutaj liczymy kąt zgięcia kolana) ---
            if frame_side is not None:
                # 1. Detekcja
                frame_side, _ = detector_side.find_pose(frame_side)

                # 2. Pobranie punktów
                lm_list = detector_side.get_landmarks()

                if lm_list and len(lm_list) > 28:
                    # Indeksy MediaPipe: 23=Biodro, 25=Kolano, 27=Kostka (Lewa strona)
                    # Jeśli stoisz prawym bokiem, użyj: 24, 26, 28
                    # Na razie zakładamy lewą stronę:
                    p1 = lm_list[23]  # Biodro
                    p2 = lm_list[25]  # Kolano
                    p3 = lm_list[27]  # Kostka

                    # 3. Obliczenie kąta
                    angle = GeometryUtils.calculate_angle(p1, p2, p3)

                    # 4. Wyświetlenie liczby na ekranie (przy kolanie)
                    # Musimy zamienić współrzędne znormalizowane (0.0-1.0) na piksele
                    h, w, _ = frame_side.shape
                    cx, cy = int(p2[1] * w), int(p2[2] * h)

                    # Rysowanie kółka i tekstu
                    cv2.circle(frame_side, (cx, cy), 10, (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame_side, str(int(angle)), (cx - 20, cy - 20),
                                cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)

                frame_side = cv2.resize(frame_side, (640, 480))
                cv2.imshow("SIDE (Kat kolana)", frame_side)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cam_front.stop()
        cam_side.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()