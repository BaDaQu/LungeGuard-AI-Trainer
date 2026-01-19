# LungeGuard – Inteligentny asystent treningu wykroków 🏋️‍♂️👁️

**LungeGuard** to zaawansowany system wizyjny czasu rzeczywistego, wspierający poprawną technikę wykonywania wykroków (lunges). Aplikacja wykorzystuje architekturę **Dual-View** (dwie kamery) oraz algorytmy sztucznej inteligencji (**MediaPipe Pose**) do analizy biomechanicznej ruchu. System pełni rolę "Cyber Trenera" – liczy powtórzenia, wykrywa błędy techniczne i reaguje głosowo, a po treningu generuje szczegółowe raporty z wykresami i nagraniem wideo.

---

## 🚀 Główne Funkcjonalności

### 1. Analiza Biomechaniczna 3D (Dual-View)
System przetwarza obraz z dwóch perspektyw jednocześnie, aby wyeliminować problem okluzji (zasłaniania kończyn):
*   **Kamera Frontowa (Laptop):** Analiza stabilności kolana i wykrywanie błędu koślawienia (**Valgus**).
*   **Kamera Boczna (Smartfon IP):** Analiza głębokości wykroku, kąta zgięcia kolana, pochylenia tułowia (**Torso Inclination**) oraz wysunięcia kolana (**Knee-Over-Toe**).

### 2. Inteligentny Licznik z systemem Anti-Cheat
*   **Maszyna Stanów:** Algorytm zlicza powtórzenie tylko po wykonaniu pełnego cyklu ruchu (Kąt < 95° w dole, > 160° w górze).
*   **Hip Drop Detection:** System ignoruje "oszukane" powtórzenia (np. unoszenie kolana w miejscu - "Skip A"). Aby zaliczyć ruch, środek ciężkości (biodro) musi fizycznie obniżyć się względem pozycji startowej.

### 3. Interfejs Głosowy (Offline)
*   **Voice Control (Vosk):** Pełne sterowanie aplikacją bez użycia rąk. Komendy są przetwarzane lokalnie na urządzeniu (brak opóźnień sieciowych).
*   **Audio Feedback (TTS):** Trener na bieżąco koryguje błędy (np. *"Wyprostuj plecy!"*, *"Kolano na zewnątrz!"*) oraz głośno liczy powtórzenia.

### 4. Raportowanie i Analiza Post-Treningowa
*   **Baza Danych (SQLite):** Pełna historia treningów dla wielu użytkowników.
*   **Wykresy Wydajności:** Po sesji generowany jest wykres pracy kolana w czasie, z naniesionymi czerwonymi punktami w momentach popełnienia błędu.
*   **Video Replay:** Każda sesja jest nagrywana (60 FPS). Użytkownik może odtworzyć nagranie z nałożonymi liniami analitycznymi lub wyeksportować je do pliku `.avi`.

---

## 🛠️ Stos Technologiczny

*   **Język:** Python 3.10
*   **Computer Vision:** OpenCV, MediaPipe Pose (Google)
*   **GUI:** CustomTkinter (Nowoczesny interfejs okienkowy)
*   **Audio:** Vosk (Speech-to-Text), Pyttsx3 (Text-to-Speech)
*   **Data Science:** NumPy (Obliczenia wektorowe), Matplotlib (Wykresy), SQLite (Baza danych)
*   **Wielowątkowość:** `threading` & `queue` (Separacja logiki, renderowania UI, obsługi kamer i audio)

---

## ⚙️ Instrukcja Instalacji

### 1. Wymagania wstępne
*   Python 3.10 (Zalecane ze względu na stabilność MediaPipe na Windows).
*   Telefon z systemem Android i aplikacją **IP Webcam**.

### 2. Instalacja zależności
```bash
git clone https://github.com/BaDaQu/LungeGuard.git
cd LungeGuard
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 3. Pobranie modelu mowy (Wymagane!)
Aplikacja korzysta z modelu offline **Vosk**.
1.  Pobierz model `vosk-model-small-pl-0.22` ze strony: [Vosk Models](https://alphacephei.com/vosk/models).
2.  Wypakuj archiwum.
3.  Zmień nazwę folderu na `model` i umieść go w głównym katalogu projektu.
   *(Struktura powinna wyglądać tak: `LungeGuard/model/`)*.

---

## 🖥️ Instrukcja Użytkowania

### Konfiguracja Kamery (Smartfon)
1.  Uruchom aplikację **IP Webcam** na telefonie.
2.  W ustawieniach "Video preferences":
    *   **Video resolution:** Ustaw na **640x480** (Kluczowe dla płynności!).
    *   **Quality:** Ustaw na **20**.
3.  Kliknij "Start server" i odczytaj adres IP (np. `http://192.168.0.15:8080`).

### Uruchomienie Aplikacji
```bash
python src/main.py
```

### Obsługa w 3 krokach:
1.  **Dashboard:** Wybierz swoje imię (lub dodaj nowe), wpisz adres IP telefonu i kliknij **ROZPOCZNIJ SESJĘ**.
2.  **Trening:**
    *   Stań w kadrze obu kamer.
    *   Powiedz **"START"** (lub "Trener start"), aby rozpocząć.
    *   Ćwicz. System będzie liczył i korygował.
    *   Powiedz **"STOP"** (Pauza) lub **"KONIEC"** (Zakończenie i zapis).
3.  **Analiza:** Po zakończeniu zobaczysz wykres. W zakładce "Historia" możesz kliknąć **WIDEO**, aby obejrzeć powtórkę.

---

## 🗣️ Komendy Głosowe

| Komenda | Działanie |
| :--- | :--- |
| **"START"** / **"ZACZNIJ"** | Uruchamia analizę i licznik powtórzeń. |
| **"STOP"** / **"PAUZA"** | Wstrzymuje licznik (tryb podglądu). |
| **"RESET"** | Zeruje licznik powtórzeń do 0. |
| **"KONIEC"** / **"WYJŚCIE"** | Kończy trening, zapisuje dane do bazy i wraca do menu głównego. |

---

## 👨‍💻 Zespół Projektowy
Projekt zrealizowany w ramach przedmiotu "Projekt Zespołowy".

*   **Bartłomiej Raj (BaDaQu)** – *Lider, Architektura, AI & Logic Core, Frontend, UX, Analiza danych*
*   **Bartłomiej Jedyk** – *Testing*
*   **Marcel Podlecki** – *Testing, Ekspert domenowy*
*   **Wojciech Stochmiałek** – *Testing*
