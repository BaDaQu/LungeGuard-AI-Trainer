import customtkinter as ctk
from PIL import Image
import threading
import sys
from datetime import datetime
from src.database.db_manager import DatabaseManager
from src.logic.training_loop import run_training


class AppUI:
    def __init__(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("LungeGuard AI Trainer")
        self.root.geometry("1100x700")

        self.db = DatabaseManager()
        self.users_map = {}

        self.stop_event = threading.Event()
        self.training_thread = None

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        self._init_dashboard_view()
        self._init_training_view()

        self.show_dashboard()

    def _init_dashboard_view(self):
        self.frame_dashboard = ctk.CTkFrame(self.main_container, fg_color="transparent")

        ctk.CTkLabel(self.frame_dashboard, text="LungeGuard", font=("Roboto", 40, "bold")).pack(pady=30)

        # Config
        config_frame = ctk.CTkFrame(self.frame_dashboard)
        config_frame.pack(pady=10, padx=20, fill="x")

        row1 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row1.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(row1, text="Użytkownik:", font=("Arial", 16)).pack(side="left")
        self.user_var = ctk.StringVar(value="Wybierz...")
        self.option_user = ctk.CTkOptionMenu(row1, variable=self.user_var, command=self._on_user_change, width=200)
        self.option_user.pack(side="left", padx=20)
        ctk.CTkButton(row1, text="+ Nowy", width=80, command=self._add_user_dialog).pack(side="right")

        row2 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row2.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(row2, text="Kamera IP:", font=("Arial", 16)).pack(side="left")
        self.entry_ip = ctk.CTkEntry(row2, width=300)
        self.entry_ip.insert(0, "http://192.168.33.8:8080/video")
        self.entry_ip.pack(side="left", padx=35)

        # History
        hist_frame = ctk.CTkFrame(self.frame_dashboard)
        hist_frame.pack(pady=20, padx=20, fill="both", expand=True)
        ctk.CTkLabel(hist_frame, text="Ostatnie Treningi", font=("Arial", 18, "bold")).pack(pady=10)

        headers = ctk.CTkFrame(hist_frame, height=30)
        headers.pack(fill="x", padx=10)
        ctk.CTkLabel(headers, text="Data", width=200, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(headers, text="Powtórzenia", width=100).pack(side="left")
        ctk.CTkLabel(headers, text="Błędy", width=100).pack(side="left")

        self.scroll_history = ctk.CTkScrollableFrame(hist_frame)
        self.scroll_history.pack(fill="both", expand=True, padx=10, pady=10)

        self.btn_start = ctk.CTkButton(self.frame_dashboard, text="ROZPOCZNIJ SESJĘ",
                                       font=("Roboto", 20, "bold"), height=60, fg_color="green",
                                       hover_color="darkgreen",
                                       command=self._start_session)
        self.btn_start.pack(pady=20, padx=40, fill="x")

        self.lbl_status = ctk.CTkLabel(self.frame_dashboard, text="Gotowy.", text_color="gray")
        self.lbl_status.pack(pady=5)

    def _init_training_view(self):
        self.frame_training = ctk.CTkFrame(self.main_container, fg_color="transparent")

        top_bar = ctk.CTkFrame(self.frame_training, height=60)
        top_bar.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_bar, text="SESJA AKTYWNA", font=("Roboto", 20, "bold"), text_color="red").pack(side="left",
                                                                                                        padx=20)

        self.btn_stop = ctk.CTkButton(top_bar, text="ZAKOŃCZ TRENING", fg_color="#c0392b", hover_color="#a93226",
                                      font=("Roboto", 14, "bold"), command=self._stop_session)
        self.btn_stop.pack(side="right", padx=20, pady=10)

        self.video_container = ctk.CTkFrame(self.frame_training, fg_color="black")
        self.video_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.video_container.grid_columnconfigure(0, weight=1, uniform="group1")
        self.video_container.grid_columnconfigure(1, weight=1, uniform="group1")
        self.video_container.grid_rowconfigure(0, weight=1)

        self.lbl_cam_front = ctk.CTkLabel(self.video_container, text="Kamera Frontowa\n(Łączenie...)",
                                          font=("Arial", 16))
        self.lbl_cam_front.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        self.lbl_cam_side = ctk.CTkLabel(self.video_container, text="Kamera Boczna\n(Łączenie...)", font=("Arial", 16))
        self.lbl_cam_side.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

    def show_dashboard(self):
        self.frame_training.pack_forget()
        self.frame_dashboard.pack(fill="both", expand=True)
        self._refresh_user_list()

    def show_training(self):
        self.frame_dashboard.pack_forget()
        self.frame_training.pack(fill="both", expand=True)
        self.lbl_cam_front.configure(image=None, text="Łączenie...")
        self.lbl_cam_side.configure(image=None, text="Łączenie...")

    def _start_session(self):
        name = self.user_var.get()
        ip = self.entry_ip.get()

        if name not in self.users_map:
            self.lbl_status.configure(text="BŁĄD: Wybierz użytkownika!", text_color="red")
            return

        user_id = self.users_map[name]
        self.show_training()

        self.stop_event.clear()
        self.training_thread = threading.Thread(
            target=run_training,
            args=(user_id, ip, self.stop_event, self._update_video_callback),
            daemon=True
        )
        self.training_thread.start()

    def _stop_session(self):
        if self.training_thread and self.training_thread.is_alive():
            self.stop_event.set()

        self.show_dashboard()
        self.lbl_status.configure(text="Trening zakończony. Dane zapisane.", text_color="green")

    def _update_video_callback(self, img_front, img_side, status):
        """Odbiera klatki i statusy."""

        # --- FIX 1: Ignoruj update'y jeśli zatrzymaliśmy trening ---
        # Zapobiega 'duchom' z poprzedniego wątku, które próbują rysować na zamkniętym oknie
        if self.stop_event.is_set():
            return

        if status == "SESSION_DONE":
            self.root.after(0, self._stop_session)
            return

        if status == "EXIT_APP":
            self.root.after(0, self._on_close)
            return

        self.root.after(0, lambda: self._update_ui_on_main(img_front, img_side))

    def _update_ui_on_main(self, img_front, img_side):
        # Sprawdzamy czy widgety istnieją i czy wątek nie został w międzyczasie zatrzymany
        if not self.lbl_cam_front.winfo_exists() or self.stop_event.is_set():
            return

        container_w = self.video_container.winfo_width()
        container_h = self.video_container.winfo_height()

        target_w = (container_w // 2) - 10
        if target_w < 100: target_w = 320
        target_h = int(target_w * 0.75)

        if target_h > container_h - 10:
            target_h = container_h - 10
            target_w = int(target_h * 1.33)

        if img_front is not None:
            pil_img = Image.fromarray(img_front)
            ctk_img = ctk.CTkImage(light_image=pil_img, size=(target_w, target_h))
            self.lbl_cam_front.configure(image=ctk_img, text="")
            # --- FIX 2: Zapobieganie Garbage Collection ---
            # Musimy przypisać obraz do widgetu, inaczej Python go usunie przed wyświetleniem
            self.lbl_cam_front.image = ctk_img

        if img_side is not None:
            pil_img = Image.fromarray(img_side)
            ctk_img = ctk.CTkImage(light_image=pil_img, size=(target_w, target_h))
            self.lbl_cam_side.configure(image=ctk_img, text="")
            # --- FIX 2: Zapobieganie Garbage Collection ---
            self.lbl_cam_side.image = ctk_img

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
            d, r, e = row
            f = ctk.CTkFrame(self.scroll_history)
            f.pack(fill="x", pady=2)
            try:
                dt = datetime.strptime(str(d).split('.')[0], "%Y-%m-%d %H:%M:%S").strftime("%d.%m %H:%M")
            except:
                dt = str(d)

            ctk.CTkLabel(f, text=dt, width=200, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(f, text=f"{r} powt.", width=100, text_color="#2ecc71" if r > 5 else "white").pack(side="left")
            ctk.CTkLabel(f, text=f"{e} błędów", width=100, text_color="#e74c3c" if e > 0 else "gray").pack(side="left")

    def _on_user_change(self, _):
        self._refresh_history()

    def _add_user_dialog(self):
        d = ctk.CTkInputDialog(text="Imię:", title="Nowy")
        n = d.get_input()
        if n:
            self.db.add_user(n)
            self._refresh_user_list()
            self.user_var.set(n)
            self._refresh_history()

    def _on_close(self):
        print("Zamykanie aplikacji...")
        self.stop_event.set()
        self.root.quit()
        self.root.destroy()
        sys.exit()

    def run(self):
        self.root.mainloop()