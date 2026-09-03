# mojV

![mojV](icon.svg)

Integracja Home Assistant skoncentrowana na planie lekcji, bieżącej/następnej lekcji, frekwencji, ocenach, terminarzu i automatyzacjach szkolnych.

## Status

**HACS 0.8.0 — LIVE + panel Szkoła z ocenami i terminarzem + helper przeglądarkowy 0.1.6.**

Wersja 0.8.0 zachowuje obsługę **1..N dzieci**, rzeczywisty plan lekcji i frekwencję, a do LIVE dodaje **oceny cząstkowe, oceny proponowane/końcowe oraz terminarz: sprawdziany, kartkówki, klasówki i zadania domowe**.

Panel **Szkoła** pozostaje lekką aplikacją: główny DOM jest tworzony raz, zegar i postęp lekcji aktualizują się lokalnie co 10 sekund, a zmiana dziecka, widoku lub tygodnia nie powoduje dodatkowego logowania ani pobierania danych z portalu szkolnego.

mojV zawsze najpierw próbuje lekkiego logowania HTTP. Jeżeli portal wymaga pełnej przeglądarki, integracja automatycznie przełącza się na lokalną aplikację **mojV Auth Helper** z Chromium. Użytkownik nie wybiera backendu ręcznie.

## Czy helper jest wymagany?

**Nie dla każdego konta.** Integracja najpierw próbuje działać bez helpera.

Jeżeli konto przechodzi lekkie logowanie HTTP, wystarcza sama integracja HACS. Jeżeli portal wymaga pełnej weryfikacji przeglądarkowej, potrzebny jest **mojV Auth Helper**. Po jednorazowej instalacji helper uruchamia się automatycznie i mojV sam wybiera właściwy backend.

Chromium nie jest osadzany w integracji HACS. Dzięki temu Core pozostaje lekki, a cięższa warstwa przeglądarkowa działa w osobnym, izolowanym kontenerze.

## mojV Auth Helper 0.1.6

Helper jest małą aplikacją Home Assistant uruchamianą tylko dla kont wymagających pełnej przeglądarki.

Zasady bezpieczeństwa:

- Chromium działa wyłącznie wewnątrz osobnego kontenera,
- hasło jest używane do logowania, ale helper go nie zapisuje,
- cookies, tokeny, klucze sesji i identyfikatory routingu pozostają w helperze,
- integracja HACS otrzymuje wyłącznie publiczne dane szkolne,
- cały payload helpera jest rekurencyjnie kontrolowany pod kątem niedozwolonych pól uwierzytelniających,
- helper nie wystawia portu do sieci LAN,
- komunikacja odbywa się w wewnętrznej sieci Home Assistant,
- obraz jest publikowany jako prebuilt multi-arch dla `amd64` i `aarch64`,
- logi diagnostyczne nie zawierają loginu, hasła, cookies, tokenów ani parametrów zapytań,
- diagnostyczny screenshot pozostaje lokalny, a przed jego zapisem wartości pól `input` są czyszczone.

W 0.1.6 helper zwraca plan, frekwencję, okresy klasyfikacyjne, oceny i terminarz. Poszczególne moduły są izolowane — błąd ocen lub terminarza nie powinien blokować planu i frekwencji.

## Instalacja 0.8.0

### 1. Integracja HACS

1. W HACS dodaj `https://github.com/gekon27/mojV` jako **Integration** w Custom repositories, jeżeli repo nie jest jeszcze dodane.
2. Wybierz `mojV` → **Download / Redownload / Update**.
3. Zainstaluj wersję **0.8.0** lub nowszą.
4. Uruchom ponownie Home Assistant.

HACS instaluje integrację jako:

`/homeassistant/custom_components/mojv`

### 2. Helper — tylko gdy jest potrzebny

Jeżeli Config Flow poinformuje, że portal wymaga pełnej przeglądarki:

1. Otwórz **Ustawienia → Apps / Aplikacje → App Store**.
2. Dodaj repozytorium `https://github.com/gekon27/mojV` do repozytoriów aplikacji, jeżeli nie jest jeszcze dodane.
3. Odśwież App Store.
4. Otwórz **mojV Auth Helper**.
5. Zainstaluj lub zaktualizuj helper do wersji **0.1.6**.
6. Uruchom helper i pozostaw automatyczne uruchamianie przy starcie włączone.
7. Wróć do **Ustawienia → Urządzenia i usługi → Dodaj integrację → mojV** i ponów logowanie.

Home Assistant pobiera gotowy obraz `ghcr.io/gekon27/mojv-auth-helper`; nie musi budować helpera lokalnie.

## Konfiguracja konta

Po restarcie Home Assistant:

1. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację → mojV**.
2. Wybierz **Konto szkolne**.
3. Podaj login, alias lub e-mail oraz hasło.
4. mojV automatycznie wykryje wszystkie dzieci dostępne na koncie.

Po sukcesie wpis integracji będzie nazwany np. `mojV — 2 dzieci`, a każde dziecko otrzyma osobne urządzenie Home Assistant. Liczba dzieci nie jest zakładana z góry.

Tryb **Demo** pozostaje dostępny jako niezależny test lokalny.

## Panel „Szkoła”

Po załadowaniu integracji mojV automatycznie rejestruje pozycję **Szkoła** w lewym menu Home Assistant.

W 0.8.0 dostępne są:

- **Dzisiaj** — aktualna i następna lekcja, sala, nauczyciel, numer lekcji, obecność, postęp lekcji i najbliższy alert/zadanie,
- **Plan** — pełny układ poniedziałek–piątek, wspólne sloty godzinowe, aktualna linia czasu i nawigacja poprzedni/bieżący/następny tydzień,
- **Frekwencja** — podsumowanie obecności, nieobecności, spóźnień, usprawiedliwień i zwolnień oraz ostatnie wpisy,
- **Oceny** — najnowsze oceny cząstkowe, opisy/kategorie oraz klasyfikacja proponowana i końcowa,
- **Terminarz** — nadchodzące sprawdziany, kartkówki, klasówki i zadania domowe oraz ostatnie terminy,
- **Uwagi** — zakładka pojawia się tylko, gdy backend faktycznie zwraca rzeczywiste dane uwag.

Zakładki **Oceny**, **Terminarz** i **Uwagi** są dynamiczne — nie pojawiają się jako puste atrapy.

Ticker interfejsu działa co 10 sekund **lokalnie w przeglądarce**. Nie wywołuje logowania ani dodatkowych requestów do portalu. Przełączanie dziecka, widoku i tygodnia także używa danych już znajdujących się w pamięci panelu.

Układ jest responsywny dla desktopu, tabletu i telefonu, a poziome przewijanie na małym ekranie jest ograniczone do tabeli planu.

## Aktualny zakres LIVE

W 0.8.0 działają:

- automatyczne wykrywanie 1..N dzieci,
- plan lekcji,
- frekwencja,
- stan aktualnej i następnej lekcji,
- zastępstwa i odwołane lekcje,
- alerty wynikające z planu i frekwencji,
- oceny cząstkowe,
- oceny proponowane i okresowe/końcowe,
- terminarz: sprawdziany, kartkówki, klasówki i zadania domowe,
- panel **Dzisiaj / Plan / Frekwencja / Oceny / Terminarz**.

Kolejne moduły LIVE to: uwagi, wiadomości, osiągnięcia, zebrania oraz rozszerzone statystyki frekwencji. Pojawią się dopiero po uzyskaniu prawdziwych danych — mojV nie wypełnia braków fikcyjnymi rekordami.

## Encje Home Assistant

Dla każdego dziecka integracja tworzy osobne urządzenie Home Assistant oraz podstawowe encje:

- `sensor` — aktualna lekcja,
- `sensor` — następna lekcja,
- `sensor` — numer lekcji,
- `sensor` — minuty do końca,
- `sensor` — obecność,
- `sensor` — plan dnia,
- `sensor` — ostatnia synchronizacja,
- `binary_sensor` — czy trwa lekcja,
- `binary_sensor` — czy lekcja kończy się w ciągu 5 minut,
- `calendar` — plan lekcji.

Dodatkowo powstaje wspólny sensor liczby wykrytych uczniów. Rozszerzone dane ocen i terminarza są obecnie dostępne w modelu mojV i panelu **Szkoła**; osobne encje dla kolejnych modułów mogą być dodawane bez zmiany architektury pobierania.

## Alerty i zdarzenia

mojV publikuje zdarzenia Home Assistant:

- `mojv_lesson_late` — spóźnienie,
- `mojv_lesson_absent` — nieobecność,
- `mojv_new_grade` — nowa ocena,
- `mojv_new_remark` — nowa uwaga.

Zdarzenia można wykorzystać w dowolnej automatyzacji Home Assistant.

## Wydajność

- moduły planu, frekwencji i terminarza są pobierane niezależnie,
- oceny są pobierane według rzeczywistych okresów klasyfikacyjnych,
- niezależne requesty są wykonywane współbieżnie tam, gdzie jest to bezpieczne,
- błąd pojedynczego modułu nie anuluje pozostałych,
- frontend nie pobiera danych przy każdej zmianie widoku,
- zegar i postęp lekcji są przeliczane lokalnie,
- jeden wspólny `snapshot_builder` eliminuje podwójną logikę pomiędzy HTTP i helperem.

## Diagnostyka

Jeżeli logowanie albo integracja się nie załaduje:

1. Otwórz **Ustawienia → System → Dzienniki** i wyszukaj `mojv`.
2. Po starcie integracji szukaj wpisu `mojV integration version=0.8.0 mode=... auth_backend=...`.
3. Jeżeli używany jest helper, otwórz **Ustawienia → Apps / Aplikacje → mojV Auth Helper → Logi**.
4. Po starcie helpera pierwszy wpis powinien zawierać `mojV Auth Helper version=0.1.6`.
5. W logu helpera szukaj etapów `login-page`, `username-submitted`, `password-submitted`, `diary-links`, `student-app`, `context`; przy wolnym linku mogą wystąpić `diary-link-load-timeout` lub `diary-link-failed`.
6. Przy błędzie helper może zapisać lokalny plik `/data/mojv_auth_error.png`; wartości pól formularza są czyszczone przed wykonaniem zrzutu.

Nie publikuj hasła, cookies, tokenów ani kluczy sesji.

## Architektura

### Integracja HACS

- `auth.py` — lekki flow logowania i wykrywanie potrzeby pełnej przeglądarki,
- `helper_gateway.py` — komunikacja z lokalnym helperem przez Supervisor,
- `helper_protocol.py` — rekurencyjna walidacja kontraktu i sekretów,
- `school_api.py` — modułowe i izolowane zapytania danych,
- `parsers/grades.py` — oceny cząstkowe oraz klasyfikacja,
- `parsers/schoolwork.py` — terminarz i czyszczenie treści,
- `parsers/timetable.py` — plan i frekwencja przy lekcjach,
- `snapshot_builder.py` — jeden wspólny builder danych dla wszystkich backendów logowania,
- `client.py` — obsługa trybu demo, HTTP i helpera,
- `coordinator.py` — kontrolowane odświeżanie,
- `models.py` — wspólny model szkolny,
- `logic.py` — lokalna logika czasu i agregacja frekwencji,
- `panel.py` — backend WebSocket panelu,
- `frontend/school-panel.js` — szybki lokalny frontend panelu,
- `notifications.py` — alerty i eventy,
- `sensor.py`, `binary_sensor.py`, `calendar.py` — standardowe encje HA,
- `config_flow.py` — konfiguracja GUI,
- `diagnostics.py` — diagnostyka.

### mojV Auth Helper

- `mojv_auth_helper/Dockerfile` — Chromium, ChromeDriver i Xvfb,
- `mojv_auth_helper/config.yaml` — gotowy obraz GHCR,
- `rootfs/app/server.py` — prywatne API helpera, logowanie i rozszerzony snapshot,
- `rootfs/app/auth_runtime.py` — wewnętrzny routing uczniów i filtracja danych publicznych.

## Multi-student

Integracja nie zakłada dwóch dzieci na sztywno. Konto jest traktowane jako kolekcja **1..N uczniów**, a każde dziecko dostaje własne urządzenie, encje i dane.
