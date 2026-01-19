import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import threading
import sys
import queue
import cv2
import os
import json
import shutil
from datetime import datetime
from src.database.db_manager import DatabaseManager
from src.logic.training_loop import run_training
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class AppUI:
    def __init__(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("LungeGuard AI Trainer")

        self.window_width = 1100
        self.window_height = 800
        self._center_window()

        self.db = DatabaseManager()
        self.users_map = {}

        self.stop_event = threading.Event()
        self.command_queue = queue.Queue()
        self.training_thread = None
        self.report_data = None

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        self._init_dashboard_view()
        self._init_training_view()

        self.show_dashboard()

    def _center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_c = int((screen_width / 2) - (self.window_width / 2))
        y_c = int((screen_height / 2) - (self.window_height / 2))
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x_c}+{y_c}")

    def _init_dashboard_view(self):
        self.frame_dashboard = ctk.CTkFrame(self.main_container, fg_color="transparent")

        ctk.CTkLabel(self.frame_dashboard, text="LungeGuard", font=("Roboto", 40, "bold")).pack(pady=20)

        # Config User
        config_frame = ctk.CTkFrame(self.frame_dashboard)
        config_frame.pack(pady=5, padx=20, fill="x")
        row1 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row1.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(row1, text="Użytkownik:", font=("Arial", 16)).pack(side="left")
        self.user_var = ctk.StringVar(value="Wybierz...")
        self.option_user = ctk.CTkOptionMenu(row1, variable=self.user_var, command=self._on_user_change, width=200)
        self.option_user.pack(side="left", padx=20)
        ctk.CTkButton(row1, text="+ Nowy", width=80, command=self._add_user_dialog).pack(side="right")

        # Tabs
        self.tabview = ctk.CTkTabview(self.frame_dashboard)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)
        self.tab_train = self.tabview.add("Start")
        self.tab_settings = self.tabview.add("Ustawienia")
        self.tab_history = self.tabview.add("Historia")
        self.tab_help = self.tabview.add("Instrukcja")

        # --- ZAKŁADKA START ---
        lbl_ip = ctk.CTkLabel(self.tab_train, text="IP Kamery Bocznej (Telefon):")
        lbl_ip.pack(pady=(20, 5))
        self.entry_ip = ctk.CTkEntry(self.tab_train, placeholder_text="http://...", width=350)
        self.entry_ip.insert(0, "http://192.168.33.8:8080/video")
        self.entry_ip.pack(pady=5)

        self.btn_start = ctk.CTkButton(self.tab_train, text="ROZPOCZNIJ SESJĘ",
                                       font=("Roboto", 20, "bold"), height=60, fg_color="green",
                                       hover_color="darkgreen",
                                       command=self._start_session)
        self.btn_start.pack(pady=(40, 10), padx=60, fill="x")

        self.btn_exit_dash = ctk.CTkButton(self.tab_train, text="ZAMKNIJ PROGRAM",
                                           font=("Roboto", 14, "bold"), height=40, fg_color="#c0392b",
                                           hover_color="#a93226",
                                           command=self._on_close)
        self.btn_exit_dash.pack(pady=10, padx=60, fill="x")

        # Inicjalizacja pozostałych zakładek
        self._setup_settings_tab()
        self._setup_history_tab()
        self._setup_help_tab()

        self.lbl_status = ctk.CTkLabel(self.frame_dashboard, text="Gotowy.", text_color="gray")
        self.lbl_status.pack(pady=5)

    def _setup_help_tab(self):
        """Tworzy zawartość zakładki z instrukcją."""
        scroll = ctk.CTkScrollableFrame(self.tab_help)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. SETUP
        ctk.CTkLabel(scroll, text="1. Konfiguracja Sprzętu", font=("Arial", 18, "bold"), text_color="#3498db").pack(
            anchor="w", pady=(10, 5))
        msg_setup = (
            "• Kamera Frontowa (Laptop): Ustaw ją naprzeciwko siebie.\n"
            "• Kamera Boczna (Telefon): Ustaw ją z boku, na wysokości kolan/bioder.\n"
            "• Aplikacja IP Webcam: W telefonie ustaw jakość wideo na 20 i rozdzielczość 640x480.\n"
            "• Upewnij się, że widać całą sylwetkę na obu kamerach."
        )
        ctk.CTkLabel(scroll, text=msg_setup, justify="left", font=("Arial", 14)).pack(anchor="w", padx=10)

        # 2. KOMENDY GŁOSOWE
        ctk.CTkLabel(scroll, text="2. Sterowanie Głosem (Komendy)", font=("Arial", 18, "bold"),
                     text_color="#3498db").pack(anchor="w", pady=(20, 5))

        commands = [
            ("START", "Rozpoczyna trening i analizę."),
            ("STOP / PAUZA", "Zatrzymuje licznik (tryb podglądu)."),
            ("RESET", "Zeruje licznik powtórzeń."),
            ("KONIEC", "Kończy trening, zapisuje dane i wraca do menu.")
        ]

        for cmd, desc in commands:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=cmd, font=("Consolas", 14, "bold"), width=150, anchor="w", text_color="orange").pack(
                side="left", padx=10)
            ctk.CTkLabel(row, text=desc, font=("Arial", 14), anchor="w").pack(side="left")

        # 3. WYKRYWANE BŁĘDY
        ctk.CTkLabel(scroll, text="3. Wykrywane Błędy", font=("Arial", 18, "bold"), text_color="#3498db").pack(
            anchor="w", pady=(20, 5))
        # --- TUTAJ BYŁ BŁĄD (MINUS) --- NAPRAWIONE:
        msg_errors = (
            "• Valgus (Przód): Uciekanie kolana do wewnątrz.\n"
            "• Plecy (Bok): Nadmierne pochylenie tułowia do przodu.\n"
            "• Kolano (Bok): Wysuwanie kolana zbyt mocno przed palce (przy zgięciu)."
        )
        ctk.CTkLabel(scroll, text=msg_errors, justify="left", font=("Arial", 14)).pack(anchor="w", padx=10)

    def _setup_settings_tab(self):
        frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text="Poziom Trudności:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 5))
        self.diff_var = ctk.StringVar(value="Medium")
        ctk.CTkSegmentedButton(frame, values=["Easy", "Medium", "Hard"], variable=self.diff_var).pack(fill="x",
                                                                                                      pady=(0, 20))
        self.audio_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(frame, text="Głos Trenera (TTS)", variable=self.audio_var).pack(anchor="w", pady=10)
        self.voice_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(frame, text="Sterowanie Głosem (Start/Stop)", variable=self.voice_var).pack(anchor="w", pady=10)

    def _setup_history_tab(self):
        headers = ctk.CTkFrame(self.tab_history, height=30)
        headers.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(headers, text="Data", width=150, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="Powtórzenia", width=100).pack(side="left", padx=5)
        ctk.CTkLabel(headers, text="Błędy", width=100).pack(side="left", padx=5)
        self.scroll_history = ctk.CTkScrollableFrame(self.tab_history)
        self.scroll_history.pack(fill="both", expand=True, padx=5, pady=5)

    def _init_training_view(self):
        self.frame_training = ctk.CTkFrame(self.main_container, fg_color="transparent")
        top_bar = ctk.CTkFrame(self.frame_training, height=50)
        top_bar.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(top_bar, text="SESJA AKTYWNA", font=("Roboto", 20, "bold"), text_color="red").pack(side="left",
                                                                                                        padx=20)
        self.btn_back = ctk.CTkButton(top_bar, text="ZAKOŃCZ TRENING", fg_color="#c0392b", hover_color="#a93226",
                                      font=("Roboto", 14, "bold"), command=self._stop_session)
        self.btn_back.pack(side="right", padx=20, pady=5)

        self.video_container = ctk.CTkFrame(self.frame_training, fg_color="black")
        self.video_container.pack(fill="both", expand=True, padx=10, pady=5)
        self.video_container.grid_columnconfigure(0, weight=1, uniform="group1")
        self.video_container.grid_columnconfigure(1, weight=1, uniform="group1")
        self.video_container.grid_rowconfigure(0, weight=1)
        self.lbl_cam_front = ctk.CTkLabel(self.video_container, text="Kamera Frontowa", font=("Arial", 16))
        self.lbl_cam_front.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.lbl_cam_side = ctk.CTkLabel(self.video_container, text="Kamera Boczna", font=("Arial", 16))
        self.lbl_cam_side.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        control_bar = ctk.CTkFrame(self.frame_training, height=60)
        control_bar.pack(fill="x", padx=10, pady=10, side="bottom")
        ctk.CTkButton(control_bar, text="START (Wznów)", fg_color="green",
                      command=lambda: self.command_queue.put("START")).pack(side="left", padx=20, expand=True)
        ctk.CTkButton(control_bar, text="PAUZA", fg_color="orange",
                      command=lambda: self.command_queue.put("STOP")).pack(side="left", padx=20, expand=True)
        ctk.CTkButton(control_bar, text="RESET LICZNIKA", fg_color="gray",
                      command=lambda: self.command_queue.put("RESET")).pack(side="left", padx=20, expand=True)

    def show_dashboard(self):
        self.frame_training.pack_forget()
        self.frame_dashboard.pack(fill="both", expand=True)
        self._refresh_user_list()
        self._center_window()
        if self.report_data:
            self._show_summary_window(self.report_data)
            self.report_data = None

    def show_training(self):
        self.frame_dashboard.pack_forget()
        self.frame_training.pack(fill="both", expand=True)
        self._center_window()
        self.lbl_cam_front.configure(image=None, text="Łączenie...")
        self.lbl_cam_side.configure(image=None, text="Łączenie...")

    def _start_session(self):
        name = self.user_var.get()
        ip = self.entry_ip.get()
        if name not in self.users_map:
            self.lbl_status.configure(text="BŁĄD: Wybierz użytkownika!", text_color="red")
            return
        user_id = self.users_map[name]

        config = {"difficulty": self.diff_var.get(), "audio": self.audio_var.get(), "voice": self.voice_var.get()}
        self.show_training()
        self.stop_event.clear()
        with self.command_queue.mutex: self.command_queue.queue.clear()

        self.training_thread = threading.Thread(
            target=run_training,
            args=(user_id, ip, self.stop_event, self._update_video_callback, config, self.command_queue),
            daemon=True
        )
        self.training_thread.start()

    def _stop_session(self):
        self.command_queue.put("EXIT")

    def _update_video_callback(self, img_front, img_side, status, data=None):
        if self.stop_event.is_set() and status != "SESSION_DONE": return
        if status == "SESSION_DONE":
            self.report_data = data
            self.stop_event.set()
            self.root.after(0, self.show_dashboard)
            return
        if status == "EXIT_APP":
            self.root.after(0, self._on_close)
            return
        self.root.after(0, lambda: self._update_ui_on_main(img_front, img_side))

    def _update_ui_on_main(self, img_front, img_side):
        if not self.lbl_cam_front.winfo_exists() or self.stop_event.is_set(): return
        cw = self.video_container.winfo_width()
        ch = self.video_container.winfo_height()
        tw = max((cw // 2) - 10, 320)
        th = int(tw * 0.75)
        if th > ch - 10: th = ch - 10; tw = int(th * 1.33)

        if img_front is not None:
            cimg = ctk.CTkImage(light_image=Image.fromarray(img_front), size=(tw, th))
            self.lbl_cam_front.configure(image=cimg, text="")
            self.lbl_cam_front.image = cimg
        if img_side is not None:
            cimg = ctk.CTkImage(light_image=Image.fromarray(img_side), size=(tw, th))
            self.lbl_cam_side.configure(image=cimg, text="")
            self.lbl_cam_side.image = cimg

    def _play_video(self, video_path):
        if not video_path: return

        # Okno opcji
        win = ctk.CTkToplevel(self.root)
        win.title("Nagranie sesji")
        win.geometry("450x220")
        win.attributes('-topmost', True)

        ctk.CTkLabel(win, text="Zarządzanie nagraniem wideo", font=("Roboto", 16, "bold")).pack(pady=15)

        def play():
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened(): return

            window_name = "Replay (Nacisnij 'q' aby zamknac)"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 800, 600)
            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

            while True:
                # Sprawdzenie czy okno zostało zamknięte przez 'X'
                # Jeśli getWindowProperty zwróci < 1, oznacza to że okno nie istnieje
                try:
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        break
                except:
                    break

                ret, frame = cap.read()
                if not ret:  # Koniec filmu -> przewiń do początku (loop) lub wyjdź
                    break

                cv2.imshow(window_name, frame)

                # Czekamy na 'q'
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break

            cap.release()

            # BEZPIECZNE ZAMYKANIE:
            # Używamy try-except, aby zignorować błąd, jeśli okno już nie istnieje
            try:
                cv2.destroyWindow(window_name)
            except:
                pass

        def download():
            import shutil
            from tkinter import filedialog, messagebox

            original_filename = os.path.basename(video_path)
            save_path = filedialog.asksaveasfilename(
                defaultextension=".avi",
                initialfile=original_filename,
                title="Wybierz miejsce zapisu"
            )

            if save_path:
                try:
                    shutil.copy(video_path, save_path)
                    messagebox.showinfo("Sukces", "Pomyślnie zapisano plik!")
                except Exception as e:
                    messagebox.showerror("Błąd", f"Nie udało się skopiować pliku: {e}")

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="ODTWÓRZ", fg_color="#3498db", command=play).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="POBIERZ", fg_color="#2ecc71", command=download).pack(side="left", padx=10)

        ctk.CTkButton(win, text="Zamknij", command=win.destroy).pack(pady=10)

    def _parse_and_show_chart(self, graph_json_str):
        try:
            data = json.loads(graph_json_str)
            self._show_summary_window(data)
        except Exception as e:
            print(f"JSON ERROR: {e}")

    def _show_summary_window(self, data):
        if not data or not data["angles"]: return

        # 1. Konfiguracja rozmiaru okna
        win_w = 1000
        win_h = 800  # Zwiększone, aby pomieścić legendę pod wykresem i duży guzik

        win = ctk.CTkToplevel(self.root)
        win.title("Podsumowanie Treningu")

        # 2. Logika centrowania okna na środku ekranu
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        pos_x = int((screen_w / 2) - (win_w / 2))
        pos_y = int((screen_h / 2) - (win_h / 2))

        win.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        win.attributes('-topmost', True)  # Zawsze na wierzchu

        ctk.CTkLabel(win, text="Wykres Kąta Kolana (Bok)", font=("Roboto", 24, "bold")).pack(pady=10)

        # Przygotowanie danych
        times = np.array([d[0] for d in data["angles"]])
        values = np.array([d[1] for d in data["angles"]])

        # Tworzenie figury
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        ax.plot(times, values, label="Kąt Kolana", color="blue", linewidth=2, zorder=1)

        # Rysowanie błędów na linii
        if data["errors"]:
            raw_err_times = [e[0] for e in data["errors"]]
            filtered_err_times = []
            last_t = -1
            for t in raw_err_times:
                if t - last_t > 0.5:
                    filtered_err_times.append(t)
                    last_t = t

            if len(filtered_err_times) > 0 and len(times) > 0:
                err_y = np.interp(filtered_err_times, times, values)
                ax.scatter(filtered_err_times, err_y, color="red", s=80, label="Błędy", zorder=5, edgecolors='black')

        # Stylistyka wykresu
        ax.set_xlabel("Czas (s)")
        ax.set_ylabel("Kąt (stopnie)")
        ax.grid(True, alpha=0.3)

        # Progi maszyny stanów
        ax.axhline(y=95, color='green', linestyle='--', alpha=0.5, label="Próg Dół (<95)")
        ax.axhline(y=160, color='orange', linestyle='--', alpha=0.5, label="Próg Góra (>160)")

        # Legenda POD wykresem (estetyczny układ)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize='10', frameon=True)

        plt.tight_layout()
        fig.subplots_adjust(bottom=0.2)  # Zostawiamy miejsce na legendę

        # Osadzenie w Tkinter
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

        # Duży, widoczny przycisk zamknięcia
        ctk.CTkButton(win, text="ZAMKNIJ", width=300, height=50,
                      font=("Roboto", 18, "bold"),
                      command=win.destroy).pack(pady=20)

    def _refresh_user_list(self):
        users = self.db.get_users()
        self.users_map = {name: uid for uid, name in users}
        names = list(self.users_map.keys())
        if names:
            self.option_user.configure(values=names)
            current = self.user_var.get()
            if current == "Wybierz..." or current not in names:
                self.user_var.set(names[0])
            self._refresh_history()
        else:
            self.option_user.configure(values=["Brak"])
            self.user_var.set("Brak")

    def _refresh_history(self):
        for w in self.scroll_history.winfo_children(): w.destroy()
        name = self.user_var.get()
        if name not in self.users_map: return
        history = self.db.get_user_history(self.users_map[name])
        for row in history:
            d, r, e, vid_path, graph_str = row
            f = ctk.CTkFrame(self.scroll_history)
            f.pack(fill="x", pady=2)
            try:
                dt = datetime.strptime(str(d).split('.')[0], "%Y-%m-%d %H:%M:%S").strftime("%d.%m %H:%M")
            except:
                dt = str(d)
            ctk.CTkLabel(f, text=dt, width=150, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(f, text=str(r), width=60, text_color="#2ecc71" if r > 5 else "white").pack(side="left", padx=5)
            ctk.CTkLabel(f, text=str(e), width=60, text_color="#e74c3c" if e > 0 else "gray").pack(side="left", padx=5)
            state_vid = "normal" if vid_path and os.path.exists(vid_path) else "disabled"
            ctk.CTkButton(f, text="WIDEO", width=60, height=25, fg_color="#3498db", state=state_vid,
                          command=lambda v=vid_path: self._play_video(v)).pack(side="left", padx=5)
            state_graph = "normal" if graph_str else "disabled"
            ctk.CTkButton(f, text="WYKRES", width=60, height=25, fg_color="#9b59b6", state=state_graph,
                          command=lambda g=graph_str: self._parse_and_show_chart(g)).pack(side="left", padx=5)

    def _add_user_dialog(self):
        d = ctk.CTkInputDialog(text="Imię:", title="Nowy")
        n = d.get_input()
        if n:
            self.db.add_user(n)
            self._refresh_user_list()
            self.user_var.set(n)
            self._refresh_history()

    def _on_user_change(self, _):
        self._refresh_history()

    def _on_close(self):
        print("Zamykanie aplikacji...")
        self.stop_event.set()
        self.root.quit()
        self.root.destroy()
        sys.exit()

    def run(self):
        self.root.mainloop()