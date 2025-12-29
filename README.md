# LungeGuard – Inteligentny asystent treningu wykroków

**LungeGuard** to aplikacja desktopowa wspierająca trening siłowy poprzez analizę techniki wykonywania wykroków (lunges) w czasie rzeczywistym. System wykorzystuje Computer Vision (MediaPipe) oraz algorytmy geometryczne do wykrywania błędów w postawie i zapewniania głosowego feedbacku użytkownikowi.

## 🚀 Główne założenia projektu

*   **Analiza 3D:** Wykorzystanie modelu MediaPipe Pose do śledzenia punktów kluczowych sylwetki.
*   **Architektura modułowa:** Przejrzysty podział na warstwę logiczną (AI), interfejs (GUI) oraz narzędzia (Kamera/Audio).
*   **Interfejs graficzny:** Nowoczesne GUI oparte o bibliotekę `CustomTkinter`.
*   **Kompatybilność:** Przystosowanie do pracy na systemie Windows (z obsłuą specyficznych wersji bibliotek).

## 🛠️ Stos technologiczny

*   **Język:** Python 3.10 (Zalecany ze względu na stabilność MediaPipe)
*   **Computer Vision:** OpenCV, Google MediaPipe (v0.10.9)
*   **GUI:** CustomTkinter
*   **Audio (Planowane):** PyAudio, pyttsx3, SpeechRecognition
*   **Inne:** NumPy, Pillow

## 📂 Struktura projektu

Projekt oparty jest na architekturze modułowej, co ułatwia jego rozwój i utrzymanie:

```text
LungeGuard-AI-Trainer/
├── src/
│   ├── gui/           # Warstwa prezentacji (Okna, Widgety)
│   ├── logic/         # Logika biznesowa (Detekcja pozy, Trener)
│   ├── utils/         # Narzędzia pomocnicze (Obsługa kamery)
│   └── main.py        # Punkt wejścia aplikacji
├── assets/            # Pliki graficzne i ikony
├── database/          # Lokalne bazy danych (SQLite)
├── requirements.txt   # Zależności projektu
└── README.md          # Dokumentacja
```

## ⚙️ Instalacja i uruchomienie

Ze względu na specyficzne wymagania biblioteki MediaPipe na systemach Windows, zaleca się korzystanie z **Pythona 3.10**.

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/BaDaQu/LungeGuard-AI-Trainer.git
    cd LungeGuard-AI-Trainer
    ```

2.  **Utwórz wirtualne środowisko (venv):**
    ```bash
    python -m venv .venv
    # Aktywacja (Windows):
    .venv\Scripts\activate
    ```

3.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```
    *Uwaga: Plik requirements wymusza kompatybilną wersję `protobuf==3.20.3`, aby uniknąć błędów na Windows.*

4.  **Uruchom aplikację:**
    ```bash
    python src/main.py
    ```

## 👨‍💻 Autor
**Bartłomiej Raj (BaDaQu)**

*Stan projektu: Faza deweloperska - gotowa architektura i szkielet aplikacji.*
