import cv2
import time
import queue  # Potrzebne do obsługi wyjątków Empty
import numpy as np
from src.utils.camera_handler import CameraHandler
from src.utils.landmark_smoother import LandmarkSmoother
from src.utils.environment_check import EnvironmentCheck
from src.utils.audio_manager import AudioManager
from src.utils.voice_input import VoiceInput
from src.logic.pose_detector import PoseDetector
from src.logic.skeleton_processor import SkeletonProcessor
from src.logic.trainer_logic import TrainerLogic
from src.database.db_manager import DatabaseManager

# Kolory
COL_WHITE = (255, 255, 255)
COL_GREEN = (0, 255, 0)
COL_RED = (0, 0, 255)
COL_YELLOW = (0, 255, 255)
COL_BLACK_BG = (40, 40, 40)


def draw_ui_header(frame, title, status_active, left_info, right_info=""):
    h, w, _ = frame.shape
    header_h = 60
    cv2.rectangle(frame, (0, 0), (w, header_h), COL_BLACK_BG, cv2.FILLED)

    status_text = "AKTYWNY" if status_active else "PAUZA"
    status_col = COL_GREEN if status_active else COL_YELLOW
    (tw, th), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_TRIPLEX, 0.8, 2)
    center_x = int((w - tw) / 2)
    cv2.putText(frame, status_text, (center_x, 40), cv2.FONT_HERSHEY_TRIPLEX, 0.8, status_col, 2)

    info_col = COL_GREEN if "OK" in left_info else COL_RED
    cv2.putText(frame, left_info, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, info_col, 1)

    if right_info:
        (rw, _), _ = cv2.getTextSize(right_info, cv2.FONT_HERSHEY_TRIPLEX, 1.0, 2)
        cv2.putText(frame, right_info, (w - rw - 20, 42), cv2.FONT_HERSHEY_TRIPLEX, 1.0, COL_WHITE, 2)
    cv2.line(frame, (0, header_h), (w, header_h), (100, 100, 100), 1)


def draw_label(frame, text, x, y, color=COL_WHITE, bg_color=(0, 0, 0)):
    (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    cv2.rectangle(frame, (x, y - th - 5), (x + tw + 6, y + base), bg_color, cv2.FILLED)
    cv2.putText(frame, text, (x + 3, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def run_training(user_id, side_camera_ip, stop_event, gui_callback, config, command_queue):
    """
    Pętla treningowa.
    :param command_queue: Kolejka z komendami z GUI (przyciski).
    """
    print(f"--- START (User: {user_id}, Config: {config}) ---")

    db = DatabaseManager()
    session_id = db.start_session(user_id)

    cam_front = CameraHandler(source=0, name="FRONT", width=640, height=480)
    cam_side = CameraHandler(source=side_camera_ip, name="SIDE", width=640, height=480)

    detector_front = PoseDetector(complexity=0)
    detector_side = PoseDetector(complexity=0)
    smoother_front = LandmarkSmoother(alpha=0.65)
    smoother_side = LandmarkSmoother(alpha=0.65)
    processor = SkeletonProcessor()

    trainer = TrainerLogic()
    trainer.set_difficulty(config.get("difficulty", "Medium"))

    audio = None
    if config.get("audio", True):
        audio = AudioManager()
        audio.start()

    voice = None
    if config.get("voice", True):
        voice = VoiceInput()
        voice.start()

    cam_front.start()
    cam_side.start()

    is_training_active = False
    frame_count = 0
    cached_light_msg = "SWIATLO OK"
    cached_dist_front = "DYSTANS OK"
    cached_dist_side = "DYSTANS OK"
    last_reps_count = 0

    last_db_log_time = {}
    DB_LOG_COOLDOWN = 2.0

    try:
        while not stop_event.is_set():
            frame_front = cam_front.get_frame()
            frame_side = cam_side.get_frame()

            frame_count += 1
            do_heavy_check = (frame_count % 30 == 0)
            current_time = time.time()

            # --- ODCZYT KOMEND (GŁOS + GUI) ---
            cmd = None

            # 1. Sprawdź kolejkę GUI (ma priorytet nad głosem, bo to świadome kliknięcie)
            try:
                if not command_queue.empty():
                    cmd = command_queue.get_nowait()
            except queue.Empty:
                pass

            # 2. Jeśli brak komendy z GUI, sprawdź głos (jeśli włączony)
            if not cmd and voice:
                cmd = voice.get_command()

            # --- WYKONANIE KOMENDY ---
            if cmd:
                print(f"KOMENDA: {cmd}")

                if cmd == "EXIT":
                    if audio: audio.speak("Do widzenia", force=True)
                    time.sleep(1.5)
                    if gui_callback: gui_callback(None, None, "SESSION_DONE")
                    break
                elif cmd == "START":
                    if not is_training_active:
                        is_training_active = True
                        if audio: audio.speak("Trening rozpoczęty", force=True)
                elif cmd == "STOP":
                    if is_training_active:
                        is_training_active = False
                        if audio: audio.speak("Pauza", force=True)
                elif cmd == "RESET":
                    trainer.reps = 0
                    trainer.stage = "UP"
                    last_reps_count = 0
                    is_training_active = False
                    if audio: audio.speak("Licznik wyzerowany", force=True)

            # --- ANALIZA WIDEO ---
            # (Reszta kodu bez zmian - kopiuj z poprzedniej wersji lub zostaw tak jak jest)
            # DLA PEWNOŚCI WKLEJAM SKRÓCONĄ WERSJĘ DO KOPIOWANIA:

            if frame_front is not None:
                frame_front = cv2.flip(frame_front, 1)
                h, w, _ = frame_front.shape

                if do_heavy_check or cached_light_msg == "SWIATLO OK":
                    _, cached_light_msg = EnvironmentCheck.check_brightness(frame_front)

                detector_front.find_pose(frame_front, draw=False)
                raw_lm = detector_front.get_landmarks()
                lm_front = smoother_front.smooth(raw_lm)

                if (do_heavy_check or cached_dist_front == "DYSTANS OK") and lm_front:
                    _, cached_dist_front = EnvironmentCheck.check_distance(lm_front)

                draw_ui_header(frame_front, "FRONT", is_training_active,
                               cached_light_msg if "OK" not in cached_light_msg else cached_dist_front)

                front_data = processor.process_front_view(lm_front)
                if front_data and is_training_active:
                    dev = front_data["valgus_deviation"]
                    kx, ky = front_data["knee_point"]
                    cx, cy = int(kx * w), int(ky * h)

                    is_err, msg, col = trainer.check_valgus(dev)
                    if is_err:
                        trainer.mark_error()
                        if audio: audio.speak("Kolano na zewnątrz")
                        last_log = last_db_log_time.get("Valgus", 0)
                        if current_time - last_log > DB_LOG_COOLDOWN:
                            db.log_error(session_id, "Valgus")
                            last_db_log_time["Valgus"] = current_time

                    cv2.circle(frame_front, (cx, cy), 15, col, cv2.FILLED)
                    cv2.circle(frame_front, (cx, cy), 17, COL_WHITE, 2)
                    if is_err: draw_label(frame_front, msg, cx + 25, cy, col)

            if frame_side is not None:
                h, w, _ = frame_side.shape
                detector_side.find_pose(frame_side, draw=False)
                raw_lm_s = detector_side.get_landmarks()
                lm_side = smoother_side.smooth(raw_lm_s)

                if (do_heavy_check or cached_dist_side == "DYSTANS OK") and lm_side:
                    _, cached_dist_side = EnvironmentCheck.check_distance(lm_side)

                side_data = processor.process_side_view(lm_side, side="left")
                reps_text = f"REPS: {trainer.reps}"
                draw_ui_header(frame_side, "SIDE", is_training_active, cached_dist_side, reps_text)

                if side_data:
                    knee_ang = side_data["knee_angle"]
                    torso_ang = side_data["torso_angle"]
                    shin_ang = side_data["shin_angle"]
                    ank_spread = side_data["ankle_spread"]
                    hip_y = side_data["hip_y"]

                    kx, ky = side_data["knee_point"]
                    sx, sy = side_data["shoulder_point"]
                    hx, hy = side_data["hip_point"]
                    ax, ay = side_data["ankle_point"]

                    cv2.line(frame_side, (int(sx * w), int(sy * h)), (int(hx * w), int(hy * h)), COL_YELLOW, 3)
                    cv2.line(frame_side, (int(hx * w), int(hy * h)), (int(kx * w), int(ky * h)), COL_WHITE, 2)
                    cv2.line(frame_side, (int(kx * w), int(ky * h)), (int(ax * w), int(ay * h)), COL_YELLOW, 3)
                    draw_label(frame_side, f"{int(knee_ang)}", int(kx * w) + 15, int(ky * h), COL_WHITE, (0, 0, 0))

                    if is_training_active:
                        is_torso_err, _, _ = trainer.check_torso(torso_ang)
                        is_knee_err, _, _ = trainer.check_knee_forward(shin_ang, knee_ang)

                        if is_torso_err:
                            trainer.mark_error()
                            if audio: audio.speak("Wyprostuj plecy")
                            draw_label(frame_side, "PLECY!", int(hx * w), int(hy * h) - 20, COL_RED)

                            last_log = last_db_log_time.get("Torso", 0)
                            if current_time - last_log > DB_LOG_COOLDOWN:
                                db.log_error(session_id, "Torso Inclination")
                                last_db_log_time["Torso"] = current_time

                        if is_knee_err:
                            trainer.mark_error()
                            if audio: audio.speak("Kolano do tyłu")
                            draw_label(frame_side, "KOLANO!", int(ax * w), int(ay * h), COL_RED)

                            last_log = last_db_log_time.get("Knee", 0)
                            if current_time - last_log > DB_LOG_COOLDOWN:
                                db.log_error(session_id, "Knee Over Toe")
                                last_db_log_time["Knee"] = current_time

                        reps, stage = trainer.update_reps(knee_ang, ank_spread, hip_y)
                        if reps > last_reps_count:
                            if audio: audio.speak(str(reps), force=True)
                            last_reps_count = reps

            if gui_callback:
                img_front_rgb = cv2.cvtColor(frame_front, cv2.COLOR_BGR2RGB) if frame_front is not None else None
                img_side_rgb = cv2.cvtColor(frame_side, cv2.COLOR_BGR2RGB) if frame_side is not None else None
                gui_callback(img_front_rgb, img_side_rgb, "RUNNING")

    except Exception as e:
        print(f"THREAD ERROR: {e}")
    finally:
        db.end_session(session_id, trainer.reps)
        if voice: voice.stop()
        if audio: audio.stop()
        cam_front.stop()
        cam_side.stop()
        print("--- KONIEC SESJI ---")