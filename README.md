# LungeGuard – Inteligentny asystent treningu wykroków

**LungeGuard** to zaawansowany system wizyjny wspierający trening siłowy. Aplikacja wykorzystuje dwie kamery (Laptop + Smartfon) oraz algorytmy sztucznej inteligencji (MediaPipe Pose) do analizy techniki wykonywania wykroków w czasie rzeczywistym. System nie tylko liczy powtórzenia, ale przede wszystkim pełni rolę surowego trenera – unieważnia powtórzenia wykonane z błędem technicznym.

## 🚀 Możliwości systemu (Aktualny stan)

### 1. Analiza Dual-View (2 Kamery)
System przetwarza obraz z dwóch perspektyw jednocześnie:
*   **Widok z przodu (Front):** Analiza stabilności kolana.
*   **Widok z boku (Side):** Analiza głębokości, postawy pleców i wychylenia kolana.

### 2. Wykrywanie błędów w czasie rzeczywistym
LungeGuard monitoruje 3 kluczowe błędy techniczne. Jeśli którykolwiek wystąpi, system sygnalizuje błąd (czerwony kolor) i blokuje zaliczenie powtórzenia:
*   ❌ **Koślawienie kolana (Valgus):** Wykrywanie uciekania kolana do wewnątrz (Widok Front).
*   ❌ **Garbienie się (Torso Inclination):** Wykrywanie nadmiernego pochylenia tułowia powyżej 20° (Widok Side).
*   ❌ **Przeciążenie kolana (Knee-Over-Toe):** Wykrywanie nadmiernego wysunięcia kolana przed palce stopy – kąt piszczeli > 40° (Widok Side).

### 3. Inteligentny Licznik (Maszyna Stanów)
*   Działa w oparciu o maszynę stanów (States: `UP` / `DOWN`).
*   Zalicza powtórzenie tylko wtedy, gdy wykonano pełny zakres ruchu (kąt kolana < 95° w dole, > 160° w górze) **ORAZ** nie wykryto żadnego błędu w trakcie ruchu.

## 🛠️ Stos technologiczny

*   **Język:** Python 3.10
*   **AI / Computer Vision:** MediaPipe Pose (Google), OpenCV
*   **Matematyka:** NumPy, autorskie algorytmy geometryczne (obliczanie wektorów i kątów stawowych)
*   **Architektura:** Modułowa (Separacja logiki `TrainerLogic`, procesora danych `SkeletonProcessor` i warstwy prezentacji).
*   **Sprzęt:** Laptop (Server/Processing) + Smartfon (IP Camera).

## 📂 Struktura projektu

```text
LungeGuard/
├── src/
│   ├── logic/
│   │   ├── geometry_utils.py      # Biblioteka matematyczna (kąty)
│   │   ├── pose_detector.py       # Wrapper na MediaPipe
│   │   ├── skeleton_processor.py  # Normalizacja danych i obliczenia biomechaniczne
│   │   └── trainer_logic.py       # Mózg systemu (Maszyna stanów, Walidacja)
│   ├── utils/
│   │   └── camera_handler.py      # Wielowątkowa obsługa kamer (USB + IP)
│   └── main.py                    # Główna pętla programu i wizualizacja
├── assets/
└── requirements.txt
```

## ⚙️ Instalacja i uruchomienie

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/BaDaQu/LungeGuard.git
    cd LungeGuard
    ```

2.  **Przygotuj środowisko:**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    ```
    *Projekt wymaga wymuszenia starszej wersji `protobuf==3.20.3` dla poprawnego działania MediaPipe na Windows.*

3.  **Skonfiguruj kamerę w telefonie:**
    *   Zainstaluj aplikację **IP Webcam** na Androidzie.
    *   Ustaw rozdzielczość wideo na **640x480** (dla płynności).
    *   Uruchom serwer i odczytaj adres IP.

4.  **Uruchom aplikację:**
    *   Otwórz `src/main.py`.
    *   Edytuj zmienną `SIDE_CAM_URL`, wpisując adres IP telefonu.
    *   Uruchom: `python src/main.py`

## 👨‍💻 Autor
Projekt realizowany w ramach zaliczenia przedmiotu.

**Bartłomiej Raj (BaDaQu)**
**Bartłomiej Jedyk**
**Marcel Podlecki**'
**Wojciech Stochmiałek**

