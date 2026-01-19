"""
LungeGuard - Inteligentny asystent treningu wykroków.
Plik startowy aplikacji.
"""

from src.gui.app_ui import AppUI


def main():
    """Punkt wejścia aplikacji - inicjalizacja i uruchomienie GUI."""
    app = AppUI()
    app.run()


if __name__ == "__main__":
    main()