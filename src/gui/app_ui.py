import customtkinter as ctk


class AppUI:
    def __init__(self):
        """Konfiguracja głównego okna aplikacji."""
        self.root = ctk.CTk()
        self.root.title("LungeGuard AI Trainer")
        self.root.geometry("800x600")

        # Przykładowy element GUI
        self.label = ctk.CTkLabel(self.root, text="LungeGuard v1.0", font=("Arial", 20))
        self.label.pack(pady=20)

        print("DEBUG: GUI zainicjalizowane.")

    def run(self):
        """Uruchamia główną pętlę aplikacji."""
        self.root.mainloop()