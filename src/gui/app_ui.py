import customtkinter as ctk
from src.database.db_manager import DatabaseManager
from src.logic.training_loop import run_training
import sys  # Potrzebne do całkowitego zamknięcia procesu


class AppUI:
    def __init__(self):
        """Konfiguracja głównego okna aplikacji."""
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("LungeGuard AI Trainer")
        self.root.geometry("600x600")  # Zwiększyłem lekko wysokość, żeby zmieścić przycisk

        self.db = DatabaseManager()
        self.selected_user_id = None

        # Obsługa zamknięcia przez "X"
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._setup_ui()

    def _setup_ui(self):
        # --- TYTUŁ ---
        self.lbl_title = ctk.CTkLabel(self.root, text="LungeGuard", font=("Roboto", 32, "bold"))
        self.lbl_title.pack(pady=20)

        # --- WYBÓR UŻYTKOWNIKA ---
        self.frame_user = ctk.CTkFrame(self.root)
        self.frame_user.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.frame_user, text="Wybierz użytkownika:").pack(side="left", padx=10)

        self.user_var = ctk.StringVar(value="Wybierz...")
        self.option_user = ctk.CTkOptionMenu(self.frame_user, variable=self.user_var)
        self.option_user.pack(side="left", padx=10)

        self.btn_add_user = ctk.CTkButton(self.frame_user, text="+ Nowy", width=60, command=self._add_user_dialog)
        self.btn_add_user.pack(side="right", padx=10)

        # --- KONFIGURACJA KAMERY ---
        self.frame_config = ctk.CTkFrame(self.root)
        self.frame_config.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.frame_config, text="IP Kamery Bocznej (Telefon):").pack(anchor="w", padx=10, pady=5)

        self.entry_ip = ctk.CTkEntry(self.frame_config, placeholder_text="np. http://192.168.33.8:8080/video")
        # Tu możesz wpisać swoje domyślne IP dla wygody
        self.entry_ip.insert(0, "http://192.168.33.8:8080/video")
        self.entry_ip.pack(fill="x", padx=10, pady=5)

        # --- PRZYCISK START ---
        self.btn_start = ctk.CTkButton(self.root, text="ROZPOCZNIJ TRENING",
                                       font=("Roboto", 16, "bold"),
                                       height=50, fg_color="green", hover_color="darkgreen",
                                       command=self._start_training)
        self.btn_start.pack(pady=(30, 10), padx=40, fill="x")

        # --- NOWOŚĆ: PRZYCISK WYJŚCIE ---
        self.btn_exit = ctk.CTkButton(self.root, text="WYJŚCIE",
                                      font=("Roboto", 14, "bold"),
                                      height=40, fg_color="#c0392b", hover_color="#a93226",  # Czerwony
                                      command=self._on_close)
        self.btn_exit.pack(pady=10, padx=40, fill="x")

        # --- STOPKA ---
        self.lbl_status = ctk.CTkLabel(self.root, text="Gotowy do działania.", text_color="gray")
        self.lbl_status.pack(side="bottom", pady=10)

        self._refresh_user_list()

    def _refresh_user_list(self):
        """Pobiera użytkowników z bazy."""
        users = self.db.get_users()
        self.users_map = {name: uid for uid, name in users}

        user_names = list(self.users_map.keys())
        if user_names:
            self.option_user.configure(values=user_names)
            self.user_var.set(user_names[0])
        else:
            self.option_user.configure(values=["Brak użytkowników"])
            self.user_var.set("Brak użytkowników")

    def _add_user_dialog(self):
        dialog = ctk.CTkInputDialog(text="Podaj imię nowego użytkownika:", title="Nowy Użytkownik")
        new_name = dialog.get_input()
        if new_name:
            self.db.add_user(new_name)
            self._refresh_user_list()
            self.user_var.set(new_name)
            self.lbl_status.configure(text=f"Dodano użytkownika: {new_name}")

    def _start_training(self):
        name = self.user_var.get()
        ip = self.entry_ip.get()

        if name not in self.users_map:
            self.lbl_status.configure(text="BŁĄD: Wybierz poprawnego użytkownika!", text_color="red")
            return

        user_id = self.users_map[name]

        self.lbl_status.configure(text="Uruchamianie kamer...", text_color="orange")
        self.root.update()
        self.root.withdraw()  # Ukryj okno

        try:
            run_training(user_id, ip)
        except Exception as e:
            print(f"CRASH: {e}")
        finally:
            self.root.deiconify()  # Pokaż okno z powrotem
            self.lbl_status.configure(text="Trening zakończony. Dane zapisane.", text_color="green")

    def _on_close(self):
        """Bezpieczne zamknięcie aplikacji."""
        print("Zamykanie aplikacji...")
        self.root.destroy()
        sys.exit()

    def run(self):
        self.root.mainloop()