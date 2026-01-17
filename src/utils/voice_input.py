import json
import os
import pyaudio
import threading
import time
from vosk import Model, KaldiRecognizer


class VoiceInput:
    def __init__(self):
        """
        Rozpoznawanie mowy OFFLINE (Vosk) z naprawioną ścieżką.
        """
        self.is_running = False
        self.thread = None
        self.last_command = None
        self.last_trigger_time = 0
        self.COOLDOWN = 0.5

        # --- NAPRAWA ŚCIEŻKI (ABSOLUTE PATH) ---
        # Pobieramy ścieżkę do tego pliku (voice_input.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Wychodzimy 2 piętra w górę: src/utils -> src -> ROOT
        project_root = os.path.dirname(os.path.dirname(current_dir))
        # Sklejamy pełną ścieżkę do folderu model
        self.model_path = os.path.join(project_root, "model")

        print(f"VOICE DEBUG: Szukam modelu w: {self.model_path}")
        # ----------------------------------------

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
        print("VOICE: Nasłuch aktywny (Tryb Szybki).")

    def _worker(self):
        p = pyaudio.PyAudio()
        # Mniejszy bufor (2000 zamiast 4000) = szybsza reakcja
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=2000)
        stream.start_stream()

        # --- KLUCZOWA ZMIANA: GRAMATYKA ---
        # Zmuszamy model, żeby słyszał TYLKO te słowa. Ignoruje szum i inne gadanie.
        grammar = '["start", "stop", "pauza", "koniec", "reset", "trener"]'
        rec = KaldiRecognizer(self.model, 16000, grammar)

        while self.is_running:
            try:
                data = stream.read(2000, exception_on_overflow=False)

                # Vosk zwraca True (koniec zdania) lub False (w trakcie)
                if rec.AcceptWaveform(data):
                    # Pełny wynik (rzadziej używany przy szybkim sterowaniu)
                    pass
                else:
                    # --- KLUCZOWA ZMIANA: PARTIAL RESULTS ---
                    # Czytamy to co słychać "teraz", zanim skończysz mówić
                    partial_json = json.loads(rec.PartialResult())
                    partial_text = partial_json.get("partial", "")

                    if partial_text:
                        self._process_fast_command(partial_text, rec)

            except Exception:
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

    def _process_fast_command(self, text, rec):
        """Analizuje tekst natychmiastowo."""
        now = time.time()
        if now - self.last_trigger_time < self.COOLDOWN:
            return

        cmd_detected = None

        # 1. Priorytet: ZAMKNIĘCIE PROGRAMU
        if "koniec" in text or "wyjście" in text:
            cmd_detected = "EXIT"

        # 2. PAUZA TRENINGU (bez wyłączania apki)
        elif "stop" in text or "pauza" in text or "zatrzymaj" in text:
            cmd_detected = "STOP"

        # 3. START
        elif "start" in text or "zacznij" in text or "graj" in text:
            cmd_detected = "START"

        elif "reset" in text:
            cmd_detected = "RESET"

        if cmd_detected:
            print(f"VOICE (FAST): Wykryto -> {cmd_detected}")
            self.last_command = cmd_detected
            self.last_trigger_time = now
            rec.Reset()
    def get_command(self):
        cmd = self.last_command
        self.last_command = None
        return cmd

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()