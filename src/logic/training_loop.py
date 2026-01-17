import cv2
import time
from src.utils.camera_handler import CameraHandler
from src.utils.landmark_smoother import LandmarkSmoother
from src.utils.environment_check import EnvironmentCheck
from src.utils.audio_manager import AudioManager
from src.utils.voice_input import VoiceInput
from src.logic.pose_detector import PoseDetector
from src.logic.skeleton_processor import SkeletonProcessor
from src.logic.trainer_logic import TrainerLogic
from src.database.db_manager import DatabaseManager


def run_training(user_id, side_camera_ip):
    """
    Główna pętla treningowa uruchamiana z przycisku w GUI.
    """
    print(f"--- START TRENINGU (User ID: {user_id}, IP: {side_camera_ip}) ---")

    # Inicjalizacja Bazy Danych i Sesji
    db = DatabaseManager()
    session_id = db.start_session(user_id)

    # Inicjalizacja Sprzętu
    cam_front = CameraHandler(source=0, name="FRONT", width=640, height=480)
    cam_side = CameraHandler(source=side_camera_ip, name="SIDE", width=640, height=480)

    # Inicjalizacja Logiki
    detector_front = PoseDetector(complexity=1)
    detector_side = PoseDetector(complexity=1)
    smoother_front = LandmarkSmoother(alpha=0.65)
    smoother_side = LandmarkSmoother(alpha=0.65)
    processor = SkeletonProcessor()
    trainer = TrainerLogic()

    # Audio & Voice
    audio = AudioManager()
    audio.start()
    voice = VoiceInput()
    voice.start()

    cam_front.start()
    cam_side.start()

    # Zmienne stanu
    is_training_active = False
    frame_count = 0
    cached_light_msg = ""
    cached_dist_front = ""
    cached_dist_side = ""
    last_reps_count = 0

    try:
        while True:
            frame_front = cam_front.get_frame()
            frame_side = cam_side.get_frame()

            frame_count += 1
            do_heavy_check = (frame_count % 30 == 0)

            # --- Obsługa Komend Głosowych ---
            cmd = voice.get_command()
            if cmd == "EXIT":
                audio.speak("Do widzenia", force=True)
                time.sleep(0.1)
                break
            elif cmd == "START":
                if not is_training_active:
                    is_training_active = True
                    audio.speak("Trening rozpoczęty", force=True)
            elif cmd == "STOP":
                if is_training_active:
                    is_training_active = False
                    audio.speak("Pauza", force=True)
            elif cmd == "RESET":
                trainer.reps = 0
                trainer.stage = "UP"
                last_reps_count = 0
                is_training_active = False
                audio.speak("Licznik wyzerowany", force=True)

            # --- ANALIZA FRONT ---
            if frame_front is not None:
                frame_front = cv2.flip(frame_front, 1)
                h, w, _ = frame_front.shape

                # Status
                status_text = "AKTYWNY" if is_training_active else "PAUZA"
                col = (0, 255, 0) if is_training_active else (0, 0, 255)
                cv2.putText(frame_front, status_text, (w - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)

                if do_heavy_check or cached_light_msg == "":
                    _, cached_light_msg = EnvironmentCheck.check_brightness(frame_front)
                if "OK" not in cached_light_msg:
                    cv2.putText(frame_front, cached_light_msg, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255),
                                2)

                detector_front.find_pose(frame_front, draw=False)
                raw_lm = detector_front.get_landmarks()
                lm_front = smoother_front.smooth(raw_lm)

                # Walidacja dystansu (Front)
                if (do_heavy_check or cached_dist_front == "") and lm_front:
                    _, cached_dist_front = EnvironmentCheck.check_distance(lm_front)
                cv2.putText(frame_front, f"DST: {cached_dist_front}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0), 1)

                front_data = processor.process_front_view(lm_front)
                if front_data and is_training_active:
                    dev = front_data["valgus_deviation"]
                    kx, ky = front_data["knee_point"]
                    cx, cy = int(kx * w), int(ky * h)

                    is_err, msg, col = trainer.check_valgus(dev)
                    if is_err:
                        trainer.mark_error()
                        audio.speak("Kolano na zewnątrz")
                        # Logowanie błędu do bazy
                        db.log_error(session_id, "Valgus")

                    cv2.circle(frame_front, (cx, cy), 12, col, cv2.FILLED)
                    cv2.putText(frame_front, msg, (cx + 20, cy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)

                cv2.imshow("LungeGuard - FRONT", frame_front)

            # --- ANALIZA SIDE ---
            if frame_side is not None:
                h, w, _ = frame_side.shape

                detector_side.find_pose(frame_side, draw=False)
                raw_lm_s = detector_side.get_landmarks()
                lm_side = smoother_side.smooth(raw_lm_s)

                if (do_heavy_check or cached_dist_side == "") and lm_side:
                    _, cached_dist_side = EnvironmentCheck.check_distance(lm_side)
                cv2.putText(frame_side, f"DST: {cached_dist_side}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0), 1)

                side_data = processor.process_side_view(lm_side, side="left")
                if side_data:
                    knee_ang = side_data["knee_angle"]
                    torso_ang = side_data["torso_angle"]
                    shin_ang = side_data["shin_angle"]
                    ank_spread = side_data["ankle_spread"]

                    # Rysowanie linii
                    kx, ky = side_data["knee_point"]
                    sx, sy = side_data["shoulder_point"]
                    hx, hy = side_data["hip_point"]
                    ax, ay = side_data["ankle_point"]

                    cv2.line(frame_side, (int(sx * w), int(sy * h)), (int(hx * w), int(hy * h)), (255, 255, 0),
                             3)  # Plecy
                    cv2.line(frame_side, (int(hx * w), int(hy * h)), (int(kx * w), int(ky * h)), (255, 255, 255),
                             2)  # Udo
                    cv2.line(frame_side, (int(kx * w), int(ky * h)), (int(ax * w), int(ay * h)), (255, 255, 0),
                             3)  # Piszczel

                    if is_training_active:
                        is_torso_err, _, _ = trainer.check_torso(torso_ang)
                        is_knee_err, _, _ = trainer.check_knee_forward(shin_ang)

                        if is_torso_err:
                            trainer.mark_error()
                            audio.speak("Wyprostuj plecy")
                            db.log_error(session_id, "Torso Inclination")
                        if is_knee_err:
                            trainer.mark_error()
                            audio.speak("Kolano do tyłu")
                            db.log_error(session_id, "Knee Over Toe")

                        reps, stage = trainer.update_reps(knee_ang, ank_spread)
                        if reps > last_reps_count:
                            audio.speak(str(reps), force=True)
                            last_reps_count = reps

                        # Panel Licznika
                        bg_col = (0, 0, 255) if trainer.current_rep_failed and stage == "DOWN" else (0, 200, 0)
                        cv2.rectangle(frame_side, (0, 30), (180, 110), bg_col, cv2.FILLED)
                        cv2.putText(frame_side, f"REPS: {reps}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255),
                                    2)
                        cv2.putText(frame_side, stage, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                cv2.imshow("LungeGuard - SIDE", frame_side)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        # Zapisanie wyników do bazy
        db.end_session(session_id, trainer.reps)
        print(f"--- KONIEC TRENINGU. Zapisano {trainer.reps} powtórzeń. ---")

        voice.stop()
        audio.stop()
        cam_front.stop()
        cam_side.stop()
        cv2.destroyAllWindows()