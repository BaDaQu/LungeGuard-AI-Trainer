import cv2
import time
from src.utils.camera_handler import CameraHandler
from src.utils.landmark_smoother import LandmarkSmoother
from src.utils.environment_check import EnvironmentCheck
from src.utils.audio_manager import AudioManager
from src.utils.voice_input import VoiceInput  # NOWOŚĆ
from src.logic.pose_detector import PoseDetector
from src.logic.skeleton_processor import SkeletonProcessor
from src.logic.trainer_logic import TrainerLogic


def main():
    print("--- LungeGuard: Voice Control System ---")

    FRONT_CAM_ID = 0
    SIDE_CAM_URL = "http://192.168.33.8:8080/video"  # Wpisz IP

    cam_front = CameraHandler(source=FRONT_CAM_ID, name="FRONT", width=640, height=480)
    cam_side = CameraHandler(source=SIDE_CAM_URL, name="SIDE", width=640, height=480)

    detector_front = PoseDetector(complexity=0)
    detector_side = PoseDetector(complexity=0)

    smoother_front = LandmarkSmoother(alpha=0.65)
    smoother_side = LandmarkSmoother(alpha=0.65)

    processor = SkeletonProcessor()
    trainer = TrainerLogic()

    audio = AudioManager()
    audio.start()

    # NOWOŚĆ: Inicjalizacja nasłuchu
    voice = VoiceInput()
    voice.start()

    cam_front.start()
    cam_side.start()

    # ZMIENNA STANU APLIKACJI
    is_training_active = False  # Na początku pauza

    frame_count = 0
    cached_light_msg = ""
    cached_dist_front = ""
    cached_dist_side = ""
    last_reps_count = 0

    print("System gotowy. Powiedz 'START' aby zacząć.")

    try:
        while True:
            frame_front = cam_front.get_frame()
            frame_side = cam_side.get_frame()

            frame_count += 1
            do_heavy_check = (frame_count % 30 == 0)

            # --- OBSŁUGA KOMEND GŁOSOWYCH ---
            cmd = voice.get_command()

            if cmd:
                print(f"MAIN OTRZYMAŁ KOMENDĘ: {cmd}")

            if cmd == "EXIT":
                print("KOMENDA: KONIEC PROGRAMU")
                # Force=True jest ważne, żeby zdążył powiedzieć przed zamknięciem wątków
                audio.speak("Do widzenia", force=True)
                time.sleep(0.1)
                break  # <--- TO PRZERYWA PĘTLĘ I WYŁĄCZA PROGRAM

            elif cmd == "START":
                if not is_training_active:
                    is_training_active = True
                    audio.speak("Trening rozpoczęty", force=True)
                else:
                    print("IGNORUJĘ START - TRENING JUŻ TRWA")

            elif cmd == "STOP":
                if is_training_active:
                    is_training_active = False
                    audio.speak("Pauza", force=True)
                else:
                    print("IGNORUJĘ STOP - TRENING JUŻ ZATRZYMANY")

            elif cmd == "RESET":
                trainer.reps = 0
                trainer.stage = "UP"
                last_reps_count = 0
                is_training_active = False
                audio.speak("Licznik wyzerowany", force=True)

            # ================= WIDOK PRZEDNI =================
            if frame_front is not None:
                frame_front = cv2.flip(frame_front, 1)
                h, w, _ = frame_front.shape

                # Status Treningu (Wizualizacja)
                status_color = (0, 255, 0) if is_training_active else (0, 0, 255)
                status_text = "AKTYWNY" if is_training_active else "PAUZA (Powiedz START)"
                cv2.putText(frame_front, status_text, (w - 250, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

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

                cv2.putText(frame_front, f"DST: {cached_dist_front}", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                front_data = processor.process_front_view(landmarks_front)

                if front_data and is_training_active:  # Analizujemy tylko gdy aktywny
                    dev = front_data["valgus_deviation"]
                    kx, ky = front_data["knee_point"]
                    cx, cy = int(kx * w), int(ky * h)

                    is_valgus_error, status_msg, status_color = trainer.check_valgus(dev)

                    if is_valgus_error:
                        trainer.mark_error()
                        audio.speak("Kolano na zewnątrz")

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

                cv2.putText(frame_side, f"DST: {cached_dist_side}", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                side_data = processor.process_side_view(landmarks_side, side="left")

                if side_data:
                    knee_angle = side_data["knee_angle"]
                    torso_angle = side_data["torso_angle"]
                    shin_angle = side_data["shin_angle"]
                    ankle_spread = side_data["ankle_spread"]

                    # Rysowanie linii (Rysujemy zawsze, nawet na pauzie, żeby user widział co się dzieje)
                    kx, ky = side_data["knee_point"]
                    ax, ay = side_data["ankle_point"]
                    sx, sy = side_data["shoulder_point"]
                    hx, hy = side_data["hip_point"]

                    cv2.line(frame_side, (int(sx * w), int(sy * h)), (int(hx * w), int(hy * h)), (255, 255, 0), 3)
                    cv2.line(frame_side, (int(hx * w), int(hy * h)), (int(kx * w), int(ky * h)), (255, 255, 255), 2)
                    cv2.line(frame_side, (int(kx * w), int(ky * h)), (int(ax * w), int(ay * h)), (255, 255, 0), 3)

                    # LOGIKA TRENERA - TYLKO GDY AKTYWNY
                    if is_training_active:
                        is_torso_error, _, torso_color = trainer.check_torso(torso_angle)
                        is_knee_error, _, knee_color = trainer.check_knee_forward(shin_angle)

                        if is_torso_error:
                            trainer.mark_error()
                            audio.speak("Wyprostuj plecy")
                        if is_knee_error:
                            trainer.mark_error()
                            audio.speak("Kolano do tyłu")

                        reps, stage = trainer.update_reps(knee_angle, ankle_spread)

                        if reps > last_reps_count:
                            audio.speak(str(reps), force=True)
                            last_reps_count = reps

                        # Panel Licznika (Aktywny)
                        panel_color = (0, 0, 255) if trainer.current_rep_failed and stage == "DOWN" else (0, 200, 0)
                        cv2.rectangle(frame_side, (0, 30), (180, 110), panel_color, cv2.FILLED)
                        cv2.putText(frame_side, f"REP: {reps}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255),
                                    2)

                    else:
                        # Panel Licznika (Pauza - Szary)
                        cv2.rectangle(frame_side, (0, 30), (180, 110), (100, 100, 100), cv2.FILLED)
                        cv2.putText(frame_side, "PAUZA", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                cv2.imshow("SIDE", frame_side)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        voice.stop()  # Zatrzymaj mikrofon
        audio.stop()
        cam_front.stop()
        cam_side.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()