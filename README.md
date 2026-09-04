# mojV

![mojV](icon.svg)

Integracja Home Assistant dla danych szkolnych: plan lekcji, aktualna i następna lekcja, frekwencja, oceny, terminarz, uwagi i pochwały, wiadomości, osiągnięcia, zebrania oraz automatyzacje.

## Status

**HACS 0.9.0 — LIVE + panel Szkoła + samodzielny mojV Auth Helper 0.1.8.**

Projekt jest rozdzielony na dwa niezależne repozytoria:

- **HACS / Core:** `https://github.com/gekon27/mojV`
- **Home Assistant App / browser fallback:** `https://github.com/gekon27/mojv-auth-helper`

Integracja obsługuje **1..N dzieci**. Nie zakłada stałej liczby uczniów na koncie.

## Jak działa logowanie

mojV zawsze zaczyna od lekkiego backendu HTTP. Chromium nie jest uruchamiany, jeżeli nie jest potrzebny.

Jeżeli portal wymaga pełnej przeglądarki, integracja automatycznie korzysta z lokalnej aplikacji **mojV Auth Helper 0.1.8**. Użytkownik nie wybiera backendu ręcznie.

Zasada pozostaje stała:

**HTTP first → automatyczny helper fallback.**

## Aktualny zakres LIVE

W HACS 0.9.0 działają rzeczywiste dane:

- automatyczne wykrywanie 1..N dzieci,
- plan lekcji,
- aktualna i następna lekcja,
- numer lekcji i czas do końca,
- sale i nauczyciele,
- zastępstwa i odwołane lekcje,
- frekwencja bieżąca,
- rozszerzone statystyki frekwencji ogólne i per przedmiot,
- oceny cząstkowe,
- oceny proponowane i okresowe/końcowe,
- terminarz: sprawdziany, kartkówki, klasówki i zadania domowe,
- uwagi i pochwały,
- wiadomości wraz z treścią szczegółową,
- osiągnięcia,
- zebrania i konsultacje,
- alerty Home Assistant,
- panel **Szkoła**.

Widoki zależne od dodatkowych modułów pojawiają się dopiero wtedy, gdy backend rzeczywiście zwróci dane. mojV nie tworzy fikcyjnych rekordów zastępczych.

## Instalacja HACS

1. W HACS dodaj `https://github.com/gekon27/mojV` jako **Integration** w Custom repositories.
2. Wybierz `mojV` i zainstaluj wersję **0.9.0** lub nowszą.
3. Uruchom ponownie Home Assistant.
4. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację → mojV**.
5. Podaj dane konta szkolnego.

Po poprawnym logowaniu mojV wykryje wszystkich uczniów dostępnych na koncie i utworzy osobne urządzenie Home Assistant dla każdego z nich.

## mojV Auth Helper 0.1.8

Helper jest niezależną aplikacją Home Assistant i nie znajduje się w repozytorium HACS.

### Instalacja helpera

Helper instaluj tylko wtedy, gdy Config Flow poinformuje, że konto wymaga pełnej przeglądarki.

1. Otwórz **Ustawienia → Apps / Aplikacje → App Store**.
2. Dodaj repozytorium `https://github.com/gekon27/mojv-auth-helper`.
3. Odśwież App Store.
4. Otwórz **mojV Auth Helper**.
5. Zainstaluj wersję **0.1.8** lub nowszą.
6. Uruchom aplikację i pozostaw automatyczny start włączony.
7. Wróć do konfiguracji integracji mojV i ponów logowanie.

Home Assistant pobiera gotowy publiczny obraz:

`ghcr.io/gekon27/mojv-auth-helper:0.1.8`

Obraz jest publikowany jako manifest multi-arch dla `linux/amd64` oraz `linux/arm64` (`aarch64`). Publikacja 0.1.8 została zweryfikowana także przez anonimowy pull bez poświadczeń GHCR.

## Bezpieczeństwo helpera i transportu

- Chromium, ChromeDriver i Xvfb działają w osobnym kontenerze,
- helper nie zapisuje hasła,
- cookies, tokeny, klucze sesji, mailbox keys i identyfikatory routingu pozostają wewnątrz warstwy transportu,
- surowe identyfikatory routingu wiadomości nie są przekazywane do Home Assistant; publiczne ID wiadomości jest stabilnym hashem,
- integracja HACS otrzymuje wyłącznie publiczny snapshot danych szkolnych,
- Core rekurencyjnie sprawdza payload helpera pod kątem niedozwolonych pól uwierzytelniających i routingu,
- helper nie wystawia portu do LAN,
- komunikacja odbywa się w wewnętrznej sieci Home Assistant,
- lokalizacja zapisywana w diagnostyce nie zawiera query string,
- screenshot diagnostyczny pozostaje lokalny i przed zapisem ma czyszczone wartości pól formularza,
- awaria pojedynczego modułu danych nie zatrzymuje pozostałych modułów.

## Panel „Szkoła”

Panel jest lekką aplikacją frontendową. Główny DOM jest tworzony raz, a zegar i postęp lekcji aktualizują się lokalnie co 10 sekund. Zmiana dziecka, widoku lub tygodnia korzysta z danych już pobranych do pamięci i nie powoduje kolejnego logowania.

Dostępne widoki:

- **Dzisiaj** — aktualna/następna lekcja, sala, nauczyciel, numer lekcji, obecność, postęp i najbliższy alert,
- **Plan** — tydzień, wspólne sloty godzinowe, bieżąca linia czasu, zastępstwa i anulowania,
- **Frekwencja** — podsumowanie stanów i ostatnie wpisy,
- **Oceny** — oceny cząstkowe i klasyfikacyjne,
- **Terminarz** — nadchodzące i ostatnie sprawdziany/zadania,
- **Uwagi** — uwagi i pochwały,
- **Wiadomości** — odebrane wiadomości i ich treść,
- **Statystyki** — frekwencja ogólna i per przedmiot,
- **Osiągnięcia** — wyróżnienia i wyniki,
- **Zebrania** — spotkania, miejsce, opis i bezpieczne linki online.

Widoki **Oceny**, **Terminarz**, **Uwagi**, **Wiadomości**, **Statystyki**, **Osiągnięcia** i **Zebrania** są dynamiczne i są pokazywane tylko wtedy, gdy istnieją rzeczywiste dane dla danego ucznia.

Układ jest responsywny dla desktopu, tabletu i telefonu.

## Encje Home Assistant

Dla każdego ucznia powstają m.in.:

- sensor aktualnej lekcji,
- sensor następnej lekcji,
- sensor numeru lekcji,
- sensor minut do końca,
- sensor obecności,
- sensor planu dnia,
- sensor ostatniej synchronizacji,
- binary sensor trwającej lekcji,
- binary sensor końca lekcji w ciągu 5 minut,
- kalendarz planu lekcji.

Dodatkowo dostępny jest wspólny sensor liczby wykrytych uczniów.

## Zdarzenia

mojV publikuje zdarzenia Home Assistant:

- `mojv_lesson_late`,
- `mojv_lesson_absent`,
- `mojv_new_grade`,
- `mojv_new_remark`.

## Wydajność

- niezależne moduły są pobierane oddzielnie,
- requesty są wykonywane współbieżnie tam, gdzie jest to bezpieczne,
- błąd jednego modułu nie anuluje pozostałych,
- jeden `snapshot_builder` normalizuje dane niezależnie od backendu logowania,
- frontend nie odpytuje portalu przy lokalnym przełączaniu widoków,
- Chromium pozostaje poza procesem Home Assistant Core.

## Diagnostyka

### Integracja

W **Ustawienia → System → Dzienniki** wyszukaj `mojv`. Przy starcie HACS 0.9.0 powinien pojawić się wpis:

`mojV integration version=0.9.0`

### Helper

W logach aplikacji pierwszy wpis powinien zawierać:

`mojV Auth Helper version=0.1.8`

Endpoint zdrowia helpera zwraca status i wersję pod `/health` wewnątrz kontenera.

Nie publikuj loginu, hasła, cookies, tokenów, kluczy sesji ani kluczy routingu.

## Architektura

### `gekon27/mojV` — HACS

- `auth.py` — lekki flow logowania i wykrywanie potrzeby browser fallback,
- `helper_gateway.py` — komunikacja z aplikacją helpera,
- `helper_protocol.py` — walidacja kontraktu oraz granicy sekretów/routingu,
- `school_api.py` — modułowe zapytania LIVE,
- `messages_api.py` — transport wiadomości,
- `parsers/` — normalizacja danych szkolnych,
- `snapshot_builder.py` — wspólny snapshot,
- `client.py` — klient integracji,
- `coordinator.py` — odświeżanie,
- `models.py` — model danych,
- `logic.py` — logika czasu i frekwencji,
- `panel.py` + `frontend/school-panel.js` + `frontend/school-panel-live.js` — panel Szkoła,
- `notifications.py` — alerty i eventy,
- `sensor.py`, `binary_sensor.py`, `calendar.py` — encje HA.

### `gekon27/mojv-auth-helper` — Home Assistant App

Osobne repo zawiera metadata App Store, Dockerfile, Chromium/Xvfb runtime, rozszerzony snapshot LIVE, testy kontraktu, walidację obrazu i workflow publikujący publiczny obraz GHCR dla `amd64` i `aarch64`.

## CI / release

Repo HACS uruchamia:

- kompilację i testy Python,
- kontrolę składni obu warstw panelu JavaScript,
- Hassfest,
- HACS validation,
- kontrolę spójności `manifest.json`, README i CHANGELOG.

Budowanie i publikowanie helpera należy wyłącznie do `gekon27/mojv-auth-helper`.
