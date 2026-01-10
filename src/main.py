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

            # === WIDOK BOCZNY (Kąty i Plecy) ===
            if frame_side is not None:
                frame_side = cv2.resize(frame_side, (640, 480))

                frame_side, _ = detector_side.find_pose(frame_side)
                landmarks_side = detector_side.get_landmarks()

                side_data = processor.process_side_view(landmarks_side, side="left")

                if side_data:
                    knee_angle = side_data["knee_angle"]
                    torso_angle = side_data["torso_angle"]

                    kx, ky = side_data["knee_point"]
                    sx, sy = side_data["shoulder_point"]
                    hx, hy = side_data["hip_point"]

                    h, w, _ = frame_side.shape

                    # Wizualizacja kolana
                    ckx, cky = int(kx * w), int(ky * h)
                    cv2.putText(frame_side, f"Knee: {int(knee_angle)}", (ckx, cky - 40),
                                cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 2)

                    # Wizualizacja pleców
                    chx, chy = int(hx * w), int(hy * h)
                    csx, csy = int(sx * w), int(sy * h)

                    # Rysowanie linii pleców
                    cv2.line(frame_side, (chx, chy), (csx, csy), (255, 255, 0), 2)

                    # Zmiana koloru w zależności od pochylenia (> 20 stopni = błąd)
                    back_color = (0, 255, 0) if torso_angle < 20 else (0, 0, 255)
                    cv2.putText(frame_side, f"Back: {int(torso_angle)}", (10, 50),
                                cv2.FONT_HERSHEY_DUPLEX, 1, back_color, 2)

                cv2.imshow("SIDE (Profile Analysis)", frame_side)

            # === WIDOK PRZEDNI (Valgus) ===
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

                    # Wizualizacja błędu koślawienia
                    color = (0, 0, 255) if abs(dev) > 0.03 else (0, 255, 0)
                    cv2.circle(frame_front, (cx, cy), 15, color, cv2.FILLED)

                    cv2.putText(frame_front, f"Dev: {dev:.3f}", (10, 50),
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