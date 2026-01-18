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
        Tryb Hybrydowy: Maksymalna czułość gramatyki + ścisły filtr pewności.
        """
        self.is_running = False
        self.thread = None
        self.last_command = None
        self.last_trigger_time = 0
        self.COOLDOWN = 1.0

        # PROG PEWNOŚCI: 0.9 oznacza, że AI musi być niemal pewne, że to komenda.
        # To zapobiega wyzwalaniu START/STOP podczas zwykłej rozmowy.
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
        print("VOICE: Nasłuch aktywny (Stabilny + Czuły).")

    def _worker(self):
        p = pyaudio.PyAudio()
        stream = None
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                            input=True, frames_per_buffer=2000)
            stream.start_stream()

            # SZTYWNA GRAMATYKA = Najwyższa czułość na wybrane słowa
            grammar = '["start", "zacznij", "stop", "pauza", "reset", "zeruj", "koniec", "wyjście", "[unk]"]'
            rec = KaldiRecognizer(self.model, 16000, grammar)
            rec.SetWords(True)  # Wymagane do pobrania 'conf' (pewności)

            while self.is_running:
                try:
                    data = stream.read(2000, exception_on_overflow=False)

                    if rec.AcceptWaveform(data):
                        # Reagujemy tylko na PEŁNY WYNIK (po krótkiej ciszy)
                        # To eliminuje lag i dublowanie z wyników cząstkowych
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
        """Sprawdza pewność każdego słowa i dopasowuje do komendy."""
        now = time.time()
        if now - self.last_trigger_time < self.COOLDOWN:
            return

        cmd_detected = None

        # Iterujemy po słowach w zdaniu
        for item in result_list:
            word = item.get("word", "")
            conf = item.get("conf", 0.0)

            # Jeśli pewność jest za niska -> ignoruj (to pewnie rozmowa lub szum)
            if conf < self.MIN_CONFIDENCE or word == "[unk]":
                continue

            # --- PRIORYTETY ZGODNIE Z INSTRUKCJĄ ---
            if word in ["koniec", "wyjście"]:
                cmd_detected = "EXIT"
                break  # Wyjście ma najwyższy priorytet
            elif word in ["stop", "pauza"]:
                cmd_detected = "STOP"
                break
            elif word in ["reset", "zeruj"]:
                cmd_detected = "RESET"
                break
            elif word in ["start", "zacznij"]:
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