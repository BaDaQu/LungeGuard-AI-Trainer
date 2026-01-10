import cv2
import time
from src.utils.camera_handler import CameraHandler
from src.logic.pose_detector import PoseDetector
from src.logic.skeleton_processor import SkeletonProcessor


def main():
    print("--- LungeGuard: System Start ---")

    # ================= KONFIGURACJA =================
    FRONT_CAM_ID = 0
    # Wpisz adres IP z aplikacji:
    SIDE_CAM_URL = "http://192.168.33.15:8080/video"
    # ================================================

    cam_front = CameraHandler(source=FRONT_CAM_ID, name="FRONT")
    cam_side = CameraHandler(source=SIDE_CAM_URL, name="SIDE")

    # Używamy modelu LITE (0) dla lepszej wydajności przy dwóch kamerach
    detector_front = PoseDetector(complexity=0)
    detector_side = PoseDetector(complexity=0)

    processor = SkeletonProcessor()

    cam_front.start()
    cam_side.start()
    print("System gotowy. Naciśnij 'q' aby wyjść.")

    try:
        while True:
            frame_front = cam_front.get_frame()
            frame_side = cam_side.get_frame()

            # === WIDOK BOCZNY (Kąty) ===
            if frame_side is not None:
                frame_side = cv2.resize(frame_side, (640, 480))

                frame_side, _ = detector_side.find_pose(frame_side)
                landmarks_side = detector_side.get_landmarks()
                side_data = processor.process_side_view(landmarks_side, side="left")

                if side_data:
                    angle = side_data["knee_angle"]
                    kx, ky = side_data["knee_point"]
                    h, w, _ = frame_side.shape
                    cx, cy = int(kx * w), int(ky * h)

                    cv2.putText(frame_side, f"{int(angle)} deg", (cx, cy - 40),
                                cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 0), 2)

                cv2.imshow("SIDE (Profile)", frame_side)

            # === WIDOK PRZEDNI (Koślawienie) ===
            if frame_front is not None:
                frame_front = cv2.flip(frame_front, 1)

                frame_front, _ = detector_front.find_pose(frame_front)
                landmarks_front = detector_front.get_landmarks()
                front_data = processor.process_front_view(landmarks_front)

                if front_data:
                    dev = front_data["valgus_deviation"]
                    kx, ky = front_data["knee_point"]
                    h, w, _ = frame_front.shape
                    cx, cy = int(kx * w), int(ky * h)

                    # Próg błędu - powyżej 0.03 uznajemy za koślawienie
                    THRESHOLD = 0.03

                    if abs(dev) > THRESHOLD:
                        color = (0, 0, 255)  # Czerwony (Błąd)
                        status = "ZLE! (KOLANO)"
                    else:
                        color = (0, 255, 0)  # Zielony (OK)
                        status = "OK"

                    cv2.circle(frame_front, (cx, cy), 15, color, cv2.FILLED)

                    # Wyświetlanie parametrów
                    cv2.putText(frame_front, f"Dev: {dev:.3f}", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    cv2.putText(frame_front, status, (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                cv2.imshow("FRONT (Valgus)", frame_front)

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