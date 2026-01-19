import json
import os
import pyaudio
import threading
import time
from vosk import Model, KaldiRecognizer


class VoiceInput:
    def __init__(self):
        """
        Rozpoznawanie mowy OFFLINE (Vosk).
        Wersja finalna: Minimalna lista słów + Filtr pewności dla maksymalnej precyzji.
        """
        self.is_running = False
        self.thread = None
        self.last_command = None
        self.last_trigger_time = 0
        self.COOLDOWN = 1.0
        self.MIN_CONFIDENCE = 0.90

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.model_path = os.path.join(project_root, "model")

        if not os.path.exists(self.model_path):
            print(f"VOICE ERROR: Brak modelu")
            self.model = None
        else:
            from vosk import SetLogLevel
            SetLogLevel(-1)
            try:
                self.model = Model(self.model_path)
            except Exception as e:
                print(f"VOICE ERROR: {e}")
                self.model = None

    def start(self):
        if self.is_running or self.model is None: return
        self.is_running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        print("VOICE: Nasłuch aktywny (Tryb Final).")

    def _worker(self):
        p = pyaudio.PyAudio()
        stream = None
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                            input=True, frames_per_buffer=2000)
            stream.start_stream()

            # --- ZMIANA: Usunięto synonimy, żeby uniknąć błędów ---
            grammar = '["start", "stop", "pauza", "reset", "koniec", "trener", "[unk]"]'
            rec = KaldiRecognizer(self.model, 16000, grammar)
            rec.SetWords(True)

            while self.is_running:
                try:
                    data = stream.read(2000, exception_on_overflow=False)
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        if "result" in res:
                            self._process_strict_logic(res["result"], rec)
                except Exception:
                    break
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            p.terminate()

    def _process_strict_logic(self, result_list, rec):
        now = time.time()
        if now - self.last_trigger_time < self.COOLDOWN:
            return

        cmd_detected = None

        for item in result_list:
            word = item.get("word", "")
            conf = item.get("conf", 0.0)

            if conf < self.MIN_CONFIDENCE or word == "[unk]":
                continue

            # --- PRIORYTETY (Z uproszczoną listą słów) ---
            if word == "koniec":
                cmd_detected = "EXIT"
                break
            elif word == "stop" or word == "pauza":
                cmd_detected = "STOP"
                break
            elif word == "reset":
                cmd_detected = "RESET"
                break
            elif word == "start" or word == "trener":
                cmd_detected = "START"
                break

        if cmd_detected:
            print(f"VOICE AKCJA: {cmd_detected} (Pewność: {conf:.2f})")
            self.last_command = cmd_detected
            self.last_trigger_time = now
            rec.Reset()

    def get_command(self):
        cmd = self.last_command
        self.last_command = None
        return cmd

    def stop(self):
        self.is_running = False
        if self.thread: self.thread.join(timeout=1.0)