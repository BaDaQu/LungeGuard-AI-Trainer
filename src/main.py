import cv2
from src.utils.camera_handler import CameraHandler
from src.logic.pose_detector import PoseDetector
from src.logic.skeleton_processor import SkeletonProcessor
from src.logic.trainer_logic import TrainerLogic


def main():
    print("--- LungeGuard: Walidacja Powtórzeń ---")

    # ================= KONFIGURACJA =================
    FRONT_CAM_ID = 0
    SIDE_CAM_URL = "http://192.168.33.15:8080/video"
    # ================================================

    cam_front = CameraHandler(source=FRONT_CAM_ID, name="FRONT")
    cam_side = CameraHandler(source=SIDE_CAM_URL, name="SIDE")

    detector_front = PoseDetector(complexity=0)
    detector_side = PoseDetector(complexity=0)

    processor = SkeletonProcessor()
    trainer = TrainerLogic()

    cam_front.start()
    cam_side.start()
    print("System gotowy. Naciśnij 'q' aby wyjść.")

    try:
        while True:
            frame_front = cam_front.get_frame()
            frame_side = cam_side.get_frame()

            # === WIDOK PRZEDNI (Valgus) ===
            # Analizujemy przód najpierw, żeby zgłosić błąd do trenera przed aktualizacją licznika
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

                    is_valgus_error, status_msg, status_color = trainer.check_valgus(dev)

                    # JEŚLI BŁĄD -> Zgłaszamy do trenera (spalamy powtórzenie)
                    if is_valgus_error:
                        trainer.mark_error()

                    cv2.circle(frame_front, (cx, cy), 15, status_color, cv2.FILLED)
                    cv2.putText(frame_front, f"Dev: {dev:.3f}", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
                    cv2.putText(frame_front, status_msg, (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

                cv2.imshow("FRONT (Correction)", frame_front)

            # === WIDOK BOCZNY (Licznik + Plecy) ===
            if frame_side is not None:
                frame_side = cv2.resize(frame_side, (640, 480))

                frame_side, _ = detector_side.find_pose(frame_side)
                landmarks_side = detector_side.get_landmarks()
                side_data = processor.process_side_view(landmarks_side, side="left")

                if side_data:
                    knee_angle = side_data["knee_angle"]
                    torso_angle = side_data["torso_angle"]

                    is_torso_error, _, torso_color = trainer.check_torso(torso_angle)

                    # JEŚLI BŁĄD PLECÓW -> Zgłaszamy do trenera
                    if is_torso_error:
                        trainer.mark_error()

                    # Aktualizacja licznika (teraz trener wie, czy był błąd)
                    reps, stage = trainer.update_reps(knee_angle)

                    kx, ky = side_data["knee_point"]
                    h, w, _ = frame_side.shape

                    # Wizualizacja Panelu
                    # Zmieniamy kolor panelu na czerwony, jeśli powtórzenie jest już "spalone"
                    panel_color = (0, 0, 255) if trainer.current_rep_failed and stage == "DOWN" else (0, 255, 0)

                    cv2.rectangle(frame_side, (0, 0), (220, 100), panel_color, cv2.FILLED)
                    cv2.putText(frame_side, str(reps), (20, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 3)
                    cv2.putText(frame_side, stage, (100, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    cv2.putText(frame_side, f"Back: {int(torso_angle)}", (10, 140),
                                cv2.FONT_HERSHEY_DUPLEX, 1, torso_color, 2)

                    ckx, cky = int(kx * w), int(ky * h)
                    cv2.putText(frame_side, f"{int(knee_angle)}", (ckx, cky - 40),
                                cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 2)

                cv2.imshow("SIDE (Trainer)", frame_side)

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