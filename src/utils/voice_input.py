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
        Wersja ze stabilnym czyszczeniem bufora szumów.
        """
        self.is_running = False
        self.thread = None
        self.last_command = None
        self.last_trigger_time = 0
        self.COOLDOWN = 0.8  # Lekko zwiększony cooldown dla stabilności

        # --- ŚCIEŻKA ABSOLUTNA ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.model_path = os.path.join(project_root, "model")

        if not os.path.exists(self.model_path):
            print(f"VOICE ERROR: Brak folderu '{self.model_path}'!")
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
        print("VOICE: Nasłuch aktywny (Stabilny).")

    def _worker(self):
        p = pyaudio.PyAudio()
        stream = None

        try:
            # Zwiększony bufor (4000) - stabilniej przy obciążonym CPU
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                            input=True, frames_per_buffer=4000)
            stream.start_stream()

            grammar = '["start", "stop", "pauza", "koniec", "reset", "trener", "wyjście", "zacznij"]'
            rec = KaldiRecognizer(self.model, 16000, grammar)

            while self.is_running:
                try:
                    data = stream.read(4000, exception_on_overflow=False)

                    # 1. Sprawdzamy PEŁNY wynik (koniec zdania/cisza)
                    # To kluczowe: AcceptWaveform czyści bufor Voska!
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        text = res.get("text", "")
                        if text:
                            # Jeśli coś złapał na koniec zdania, też to obsłuż
                            self._process_fast_command(text, rec)

                    # 2. Sprawdzamy WYNIK CZĄSTKOWY (w trakcie mówienia)
                    else:
                        partial = json.loads(rec.PartialResult())
                        text = partial.get("partial", "")
                        if text:
                            self._process_fast_command(text, rec)

                except Exception:
                    break

        except Exception as e:
            print(f"VOICE CRASH: {e}")

        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            p.terminate()
            print("VOICE: Wyłączono.")

    def _process_fast_command(self, text, rec):
        """Analizuje tekst."""
        now = time.time()
        if now - self.last_trigger_time < self.COOLDOWN:
            return

        cmd_detected = None

        if "stop" in text or "pauza" in text or "koniec" in text or "wyjście" in text:
            # Rozróżnienie STOP od EXIT robimy w main.py na podstawie tekstu,
            # ale tutaj upraszczamy do tokenów
            if "koniec" in text or "wyjście" in text:
                cmd_detected = "EXIT"
            else:
                cmd_detected = "STOP"

        elif "start" in text or "zacznij" in text or "trener" in text:
            cmd_detected = "START"

        elif "reset" in text:
            cmd_detected = "RESET"

        if cmd_detected:
            print(f"VOICE: Wykryto -> {cmd_detected}")
            self.last_command = cmd_detected
            self.last_trigger_time = now

            # AGRESYWNY RESET:
            # Po wykryciu komendy czyścimy bufor, żeby nie "mielił" dalej tego samego dźwięku
            rec.Reset()

    def get_command(self):
        cmd = self.last_command
        self.last_command = None
        return cmd

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)