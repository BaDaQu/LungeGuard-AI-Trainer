import cv2
from src.utils.camera_handler import CameraHandler
from src.utils.landmark_smoother import LandmarkSmoother
from src.utils.environment_check import EnvironmentCheck
from src.logic.pose_detector import PoseDetector
from src.logic.skeleton_processor import SkeletonProcessor
from src.logic.trainer_logic import TrainerLogic


def main():
    print("--- LungeGuard: Low Latency Mode ---")

    # ================= KONFIGURACJA =================
    FRONT_CAM_ID = 0
    SIDE_CAM_URL = "http://192.168.33.8:8080/video"
    # ================================================

    # Konfigurujemy handler, żeby od razu zmniejszał obraz do 640x480
    cam_front = CameraHandler(source=FRONT_CAM_ID, name="FRONT", width=640, height=480)
    cam_side = CameraHandler(source=SIDE_CAM_URL, name="SIDE", width=640, height=480)

    detector_front = PoseDetector(complexity=1)
    detector_side = PoseDetector(complexity=1)

    smoother_front = LandmarkSmoother(alpha=0.65)
    smoother_side = LandmarkSmoother(alpha=0.65)

    processor = SkeletonProcessor()
    trainer = TrainerLogic()

    cam_front.start()
    cam_side.start()

    frame_count = 0
    cached_light_msg = ""
    cached_dist_front = ""
    cached_dist_side = ""

    print("System gotowy. Naciśnij 'q' aby wyjść.")

    try:
        while True:
            frame_front = cam_front.get_frame()
            frame_side = cam_side.get_frame()

            frame_count += 1
            do_heavy_check = (frame_count % 30 == 0)

            # ================= WIDOK PRZEDNI =================
            if frame_front is not None:
                # Odbicie lustrzane
                frame_front = cv2.flip(frame_front, 1)
                h, w, _ = frame_front.shape  # Powinno być 480, 640

                if do_heavy_check or cached_light_msg == "":
                    _, cached_light_msg = EnvironmentCheck.check_brightness(frame_front)

                if "OK" not in cached_light_msg:
                    cv2.putText(frame_front, cached_light_msg, (10, h - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                detector_front.find_pose(frame_front, draw=False)
                raw_landmarks = detector_front.get_landmarks()
                landmarks_front = smoother_front.smooth(raw_landmarks)

                if (do_heavy_check or cached_dist_front == "") and landmarks_front:
                    _, cached_dist_front = EnvironmentCheck.check_distance(landmarks_front)

                cv2.putText(frame_front, f"DYSTANS: {cached_dist_front}", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                front_data = processor.process_front_view(landmarks_front)

                if front_data:
                    dev = front_data["valgus_deviation"]
                    kx, ky = front_data["knee_point"]
                    # Skalowanie punktów
                    cx, cy = int(kx * w), int(ky * h)

                    is_valgus_error, status_msg, status_color = trainer.check_valgus(dev)
                    if is_valgus_error: trainer.mark_error()

                    cv2.circle(frame_front, (cx, cy), 12, status_color, cv2.FILLED)
                    cv2.putText(frame_front, status_msg, (cx + 20, cy + 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

                cv2.imshow("FRONT", frame_front)

            # ================= WIDOK BOCZNY =================
            if frame_side is not None:
                h, w, _ = frame_side.shape

                detector_side.find_pose(frame_side, draw=False)
                raw_landmarks = detector_side.get_landmarks()
                landmarks_side = smoother_side.smooth(raw_landmarks)

                if (do_heavy_check or cached_dist_side == "") and landmarks_side:
                    _, cached_dist_side = EnvironmentCheck.check_distance(landmarks_side)

                cv2.putText(frame_side, f"DYSTANS: {cached_dist_side}", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                side_data = processor.process_side_view(landmarks_side, side="left")

                if side_data:
                    knee_angle = side_data["knee_angle"]
                    torso_angle = side_data["torso_angle"]
                    shin_angle = side_data["shin_angle"]
                    ankle_spread = side_data["ankle_spread"]

                    is_torso_error, _, torso_color = trainer.check_torso(torso_angle)
                    is_knee_error, _, knee_color = trainer.check_knee_forward(shin_angle)

                    if is_torso_error or is_knee_error: trainer.mark_error()
                    reps, stage = trainer.update_reps(knee_angle, ankle_spread)

                    kx, ky = side_data["knee_point"]
                    ax, ay = side_data["ankle_point"]
                    sx, sy = side_data["shoulder_point"]
                    hx, hy = side_data["hip_point"]

                    cv2.line(frame_side, (int(sx * w), int(sy * h)), (int(hx * w), int(hy * h)), torso_color, 4)
                    cv2.line(frame_side, (int(hx * w), int(hy * h)), (int(kx * w), int(ky * h)), (255, 255, 255), 2)
                    cv2.line(frame_side, (int(kx * w), int(ky * h)), (int(ax * w), int(ay * h)), knee_color, 4)

                    cv2.putText(frame_side, f"{int(knee_angle)}", (int(kx * w) + 10, int(ky * h)),
                                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 0), 1)

                    panel_color = (0, 0, 255) if trainer.current_rep_failed and stage == "DOWN" else (0, 200, 0)
                    cv2.rectangle(frame_side, (0, 30), (180, 110), panel_color, cv2.FILLED)
                    cv2.putText(frame_side, f"REPS: {reps}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(frame_side, stage, (10, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                    error_y = 150
                    if is_torso_error:
                        cv2.putText(frame_side, "PLECY!", (10, error_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        error_y += 30
                    if is_knee_error:
                        cv2.putText(frame_side, "KOLANO!", (10, error_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                cv2.imshow("SIDE", frame_side)

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