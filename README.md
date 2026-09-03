# mojV

![mojV](icon.svg)

Integracja Home Assistant skoncentrowana na planie lekcji, bieżącej/następnej lekcji, frekwencji, ocenach, uwagach i automatyzacjach szkolnych.

## Status

**HACS 0.6.2 — LIVE + panel Szkoła + poprawiony helper przeglądarkowy 0.1.3.**

Wersja 0.6.2 zachowuje obsługę **1..N dzieci**, rzeczywisty plan lekcji i frekwencję oraz poprawia logowanie przez **mojV Auth Helper** na kontach zatrzymywanych przez weryfikację wymagającą pełnej przeglądarki.

Helper 0.1.3 uruchamia Chromium w środowisku z wirtualnym ekranem Xvfb i klasycznym trybem headless. Dodatkowo izoluje timeouty renderera dla poszczególnych linków dziennika: jeżeli jeden link ładuje się zbyt długo, wcześniej wykryte konteksty i uczniowie nie są odrzucani, a helper próbuje zatrzymać niedokończone ładowanie przez `window.stop()` i kontynuować bez ujawniania sekretów.

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

## Instalacja 0.6.2

### 1. Integracja HACS

1. W HACS dodaj `https://github.com/gekon27/mojV` jako **Integration** w Custom repositories, jeżeli repo nie jest jeszcze dodane.
2. Wybierz `mojV` → **Download / Redownload / Update**.
3. Zainstaluj wersję **0.6.2** lub nowszą.
4. Uruchom ponownie Home Assistant.

HACS instaluje integrację jako:

`/homeassistant/custom_components/mojv`

### 2. Lokalny helper przeglądarkowy

Jeżeli Config Flow poinformuje, że portal wymaga pełnej przeglądarki:

1. Otwórz **Ustawienia → Apps / Aplikacje → App Store**.
2. Dodaj repozytorium `https://github.com/gekon27/mojV` do repozytoriów aplikacji, jeżeli nie jest jeszcze dodane.
3. Odśwież App Store.
4. Otwórz **mojV Auth Helper**.
5. Zainstaluj lub zaktualizuj helper do wersji **0.1.3**. Home Assistant pobiera gotowy obraz `ghcr.io/gekon27/mojv-auth-helper`, zamiast budować Dockerfile lokalnie.
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

## Panel „Szkoła”

Po załadowaniu integracji mojV automatycznie rejestruje pozycję **Szkoła** w lewym menu Home Assistant.

Panel zawiera:

- zakładki do przełączania pomiędzy wykrytymi dziećmi,
- pełny plan lekcji poniedziałek–piątek,
- wyróżnienie dzisiejszego dnia i aktualnej lekcji,
- aktualną i następną lekcję,
- numer lekcji, salę i nauczyciela,
- pierścień postępu lekcji oraz czas do końca,
- stan frekwencji przy każdej lekcji,
- alerty o nieobecności, spóźnieniu i zbliżającym się końcu lekcji,
- sekcje ocen, uwag i powiadomień,
- responsywny układ desktop / tablet / telefon,
- własny branding mojV.

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

W 0.6.2 działającą podstawą LIVE pozostają:

- automatyczne wykrywanie 1..N dzieci,
- plan lekcji,
- frekwencja,
- stan aktualnej/następnej lekcji,
- alerty wynikające z planu i frekwencji.

Oceny, uwagi, terminarz, wiadomości i kolejne moduły są rozwijane na tej samej modularnej warstwie danych.

## Diagnostyka

Jeżeli logowanie albo integracja się nie załaduje:

1. Otwórz **Ustawienia → System → Dzienniki** i wyszukaj `mojv`.
2. Jeżeli używany jest helper, otwórz **Ustawienia → Apps / Aplikacje → mojV Auth Helper → Logi**.
3. Ponów próbę logowania.
4. W helperze 0.1.3 szukaj etapów `login-page`, `username-submitted`, `password-submitted`, `diary-links`, `student-app`, `context`, a przy wolnym linku także `diary-link-load-timeout` lub `diary-link-failed`.
5. Przy błędzie helper może zapisać lokalny plik `/data/mojv_auth_error.png`; wartości pól formularza są czyszczone przed wykonaniem zrzutu.

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
- `logic.py` — lokalna logika czasu lekcji i stanów panelu,
- `panel.py` — backend panelu i WebSocket,
- `frontend/school-panel.js` — panel **Szkoła**,
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
