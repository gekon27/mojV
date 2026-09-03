# mojV

![mojV](icon.svg)

Integracja Home Assistant skoncentrowana na planie lekcji, bieżącej/następnej lekcji, frekwencji, ocenach, uwagach i automatyzacjach szkolnych.

## Status

**HACS 0.7.0 — LIVE + szybki panel Szkoła v2 + helper przeglądarkowy 0.1.5.**

Wersja 0.7.0 zachowuje obsługę **1..N dzieci**, rzeczywisty plan lekcji i frekwencję, a panel **Szkoła** przebudowuje do szybszej architektury aplikacyjnej. Główny DOM jest tworzony raz, zegar i postęp lekcji aktualizują się lokalnie co 10 sekund, a zmiana dziecka, widoku lub tygodnia nie powoduje dodatkowego logowania ani pobierania danych z portalu szkolnego.

Helper 0.1.5 uruchamia Chromium w środowisku z wirtualnym ekranem Xvfb i klasycznym trybem headless. Po przekierowaniu SSO nie wymaga konkretnej końcowej ścieżki aplikacji: wystarcza poprawny host ucznia i tenant w pierwszym segmencie ścieżki. Nadal izoluje timeouty renderera dla poszczególnych linków dziennika oraz nie ujawnia sekretów w diagnostyce.

mojV zawsze najpierw próbuje lekkiego logowania bez dodatkowego kontenera. Jeżeli portal wymaga pełnej przeglądarki, integracja automatycznie przełącza się na lokalną aplikację **mojV Auth Helper** z Chromium. Użytkownik nie wybiera backendu logowania ręcznie.

## mojV Auth Helper

Helper jest potrzebny tylko wtedy, gdy portal szkolny wymaga pełnej przeglądarki. Działa jako mała aplikacja Home Assistant obok integracji HACS.

Zasady bezpieczeństwa helpera:

- Chromium działa wyłącznie wewnątrz osobnego kontenera,
- hasło jest używane do logowania, ale nie jest zapisywane przez helper,
- cookies, tokeny i klucze sesji pozostają w helperze,
- integracja HACS nie otrzymuje cookies ani kluczy sesji,
- do integracji wracają tylko dane ucznia, plan lekcji i frekwencja,
- helper nie wystawia portu do sieci LAN,
- komunikacja z Home Assistant odbywa się w wewnętrznej sieci systemu,
- obraz helpera jest budowany w GitHub Actions i publikowany jako prebuilt multi-arch image dla `amd64` i `aarch64`,
- log diagnostyczny zapisuje tylko etapy logowania i bezpieczną lokalizację strony bez parametrów zapytania,
- diagnostyczny screenshot jest lokalny i przed zapisem helper czyści wartości pól `input`.

## Instalacja 0.7.0

### 1. Integracja HACS

1. W HACS dodaj `https://github.com/gekon27/mojV` jako **Integration** w Custom repositories, jeżeli repo nie jest jeszcze dodane.
2. Wybierz `mojV` → **Download / Redownload / Update**.
3. Zainstaluj wersję **0.7.0** lub nowszą.
4. Uruchom ponownie Home Assistant.

HACS instaluje integrację jako:

`/homeassistant/custom_components/mojv`

### 2. Lokalny helper przeglądarkowy

Jeżeli Config Flow poinformuje, że portal wymaga pełnej przeglądarki:

1. Otwórz **Ustawienia → Apps / Aplikacje → App Store**.
2. Dodaj repozytorium `https://github.com/gekon27/mojV` do repozytoriów aplikacji, jeżeli nie jest jeszcze dodane.
3. Odśwież App Store.
4. Otwórz **mojV Auth Helper**.
5. Zainstaluj lub zaktualizuj helper do wersji **0.1.5**. Home Assistant pobiera gotowy obraz `ghcr.io/gekon27/mojv-auth-helper`, zamiast budować Dockerfile lokalnie.
6. Uruchom helper i pozostaw automatyczne uruchamianie przy starcie włączone.
7. Wróć do **Ustawienia → Urządzenia i usługi → Dodaj integrację → mojV**.
8. Wybierz **Konto szkolne** i ponownie podaj login/alias/e-mail oraz hasło.

mojV sam wykryje uruchomiony helper i użyje go tylko wtedy, gdy zwykłe logowanie zostanie zatrzymane przez weryfikację wymagającą przeglądarki.

## Konfiguracja konta

Po restarcie Home Assistant:

1. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację → mojV**.
2. Wybierz **Konto szkolne**.
3. Podaj login, alias lub e-mail oraz hasło.
4. mojV automatycznie wykryje wszystkie dzieci dostępne na koncie.

Po sukcesie wpis integracji będzie nazwany np. `mojV — 2 dzieci`, a każde dziecko otrzyma osobne urządzenie Home Assistant.

Tryb **Demo** pozostaje dostępny jako niezależny test lokalny.

## Panel „Szkoła” v2

Po załadowaniu integracji mojV automatycznie rejestruje pozycję **Szkoła** w lewym menu Home Assistant.

W 0.7.0 panel działa jak lekka aplikacja zamiast przebudowywać cały interfejs przy każdym ticku. Zawiera:

- szybkie lokalne przełączanie wszystkich wykrytych dzieci,
- osobne widoki **Dzisiaj**, **Plan** i **Frekwencja**,
- dynamiczne zakładki **Oceny** i **Uwagi** tylko wtedy, gdy backend faktycznie zwraca te dane,
- aktualną i następną lekcję,
- numer lekcji, salę i nauczyciela,
- lokalnie aktualizowany pierścień postępu oraz czas do końca lekcji,
- plan poniedziałek–piątek ułożony według wspólnych slotów godzinowych,
- lokalną nawigację **poprzedni / bieżący / następny tydzień** bez requestu do portalu,
- linię aktualnego czasu w bieżącym tygodniu,
- wyróżnienie aktualnego dnia i trwającej lekcji,
- oznaczenia zastępstw i odwołanych lekcji,
- status obecności przy lekcjach,
- podsumowanie obecności, nieobecności, spóźnień, usprawiedliwień i zwolnień,
- listę ostatnich wpisów frekwencji,
- wygląd oparty o zmienne motywu Home Assistant z akcentem mojV,
- responsywny układ desktop / tablet / telefon; na telefonie poziome przewijanie jest ograniczone do samej tabeli planu.

Ticker interfejsu działa co 10 sekund **lokalnie w przeglądarce** i nie wywołuje logowania ani zapytania WebSocket. Przełączanie dziecka, widoku i tygodnia również używa danych znajdujących się już w pamięci panelu.

Sekcje wymagające danych, których LIVE jeszcze nie pobiera, nie są uzupełniane fikcyjnymi danymi.

## Encje Home Assistant

Dla każdego dziecka integracja tworzy osobne urządzenie Home Assistant oraz:

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

Dodatkowo powstaje wspólny sensor liczby wykrytych uczniów.

## Alerty i zdarzenia

mojV publikuje zdarzenia Home Assistant:

- `mojv_lesson_late` — spóźnienie,
- `mojv_lesson_absent` — nieobecność,
- `mojv_new_grade` — nowa ocena,
- `mojv_new_remark` — nowa uwaga.

Zdarzenia można podpiąć do `notify.mobile_app_*`, głośnika, komunikatora albo dowolnej automatyzacji HA.

## Aktualny zakres LIVE

W 0.7.0 działającą podstawą LIVE pozostają:

- automatyczne wykrywanie 1..N dzieci,
- plan lekcji w zakresie pobranym przez snapshot,
- frekwencja,
- stan aktualnej/następnej lekcji,
- alerty wynikające z planu i frekwencji,
- szybki panel **Dzisiaj / Plan / Frekwencja**.

Oceny, uwagi, terminarz/prace domowe, wiadomości, osiągnięcia i zebrania są kolejnym etapem LIVE. Modele są już rozdzielone modułowo; nowe moduły będą pojawiały się w panelu dopiero po uzyskaniu prawdziwych danych.

## Diagnostyka

Jeżeli logowanie albo integracja się nie załaduje:

1. Otwórz **Ustawienia → System → Dzienniki** i wyszukaj `mojv`.
2. Po starcie integracji szukaj wpisu w rodzaju `mojV integration version=0.7.0 mode=... auth_backend=...`.
3. Jeżeli używany jest helper, otwórz **Ustawienia → Apps / Aplikacje → mojV Auth Helper → Logi**.
4. Po starcie helpera pierwszy wpis aplikacji powinien zawierać `mojV Auth Helper version=0.1.5`.
5. Ponów próbę logowania.
6. W helperze 0.1.5 szukaj etapów `login-page`, `username-submitted`, `password-submitted`, `diary-links`, `student-app`, `context`, a przy wolnym linku także `diary-link-load-timeout` lub `diary-link-failed`.
7. Przy błędzie helper może zapisać lokalny plik `/data/mojv_auth_error.png`; wartości pól formularza są czyszczone przed wykonaniem zrzutu.

Nie publikuj hasła ani cookies. mojV nie powinien zapisywać tych danych do logów.

## Branding

Od Home Assistant 2026.3 custom integrations mogą dostarczać branding lokalnie. mojV zawiera własny `custom_components/mojv/brand/icon.png`.

## Architektura

### Integracja HACS

- `auth.py` — lekki flow logowania i wykrywanie potrzeby pełnej przeglądarki,
- `helper_gateway.py` — bezpieczna komunikacja z lokalnym helperem przez Supervisor,
- `helper_protocol.py` — walidacja sekretów i kontraktu helpera,
- `school_api.py` — modułowe zapytania danych dla lekkiej sesji,
- `parsers/` — niezależne parsery odpowiedzi,
- `client.py` — scala dane niezależnie od backendu logowania,
- `coordinator.py` — kontrolowane odświeżanie danych,
- `models.py` — wspólny model szkolny,
- `logic.py` — lokalna logika czasu lekcji i agregacja stanów frekwencji,
- `panel.py` — backend panelu i WebSocket,
- `frontend/school-panel.js` — jednorazowy shell, lokalny stan i widoki panelu **Szkoła**,
- `notifications.py` — alerty i eventy,
- `sensor.py`, `binary_sensor.py`, `calendar.py` — standardowe encje HA,
- `config_flow.py` — konfiguracja GUI,
- `diagnostics.py` — diagnostyka.

### mojV Auth Helper

- `mojv_auth_helper/Dockerfile` — obraz z Chromium, ChromeDriver i Xvfb budowany w CI,
- `mojv_auth_helper/config.yaml` — wskazuje gotowy obraz GHCR pobierany przez Supervisor,
- `rootfs/app/server.py` — prywatne API helpera, obsługa przeglądarki i diagnostyka etapów,
- `rootfs/app/auth_runtime.py` — parser kontekstu i filtracja danych publicznych.

## Multi-student

Integracja nie zakłada dwóch dzieci na sztywno. Konto jest traktowane jako kolekcja **1..N uczniów**, a każde dziecko dostaje własne urządzenie, encje i plan.
