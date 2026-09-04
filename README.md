# mojV

![mojV](icon.svg)

Integracja Home Assistant dla danych szkolnych: plan lekcji, aktualna i następna lekcja, frekwencja, oceny, terminarz, uwagi i pochwały, wiadomości, osiągnięcia, zebrania, dni wolne, nauczyciele, tematy lekcji, automatyzacje i powiadomienia.

## Status

**HACS 0.11.0 — LIVE + rozszerzony School Hub + Notification Engine v2 + samodzielny mojV Auth Helper 0.1.9.**

Projekt jest rozdzielony na dwa niezależne repozytoria:

- **HACS / Core:** `https://github.com/gekon27/mojV`
- **Home Assistant App / browser fallback:** `https://github.com/gekon27/mojv-auth-helper`

Integracja obsługuje **1..N dzieci**. Nie zakłada stałej liczby uczniów na koncie.

## Jak działa logowanie

mojV zawsze zaczyna od lekkiego backendu HTTP. Chromium nie jest uruchamiany, jeżeli nie jest potrzebny.

Jeżeli portal wymaga pełnej przeglądarki, integracja automatycznie korzysta z lokalnej aplikacji **mojV Auth Helper 0.1.9**. Użytkownik nie wybiera backendu ręcznie.

**HTTP first → automatyczny helper fallback.**

## Aktualny zakres LIVE

W HACS 0.11.0 obsługiwane są rzeczywiste dane:

- automatyczne wykrywanie 1..N dzieci,
- plan lekcji,
- aktualna i następna lekcja,
- numer lekcji i czas do końca,
- sale, nauczyciele, zastępstwa i odwołane lekcje,
- frekwencja bieżąca,
- rozszerzone statystyki frekwencji ogólne i per przedmiot,
- usprawiedliwienia,
- oceny cząstkowe wraz z wagą, gdy backend ją zwraca,
- oceny proponowane i okresowe/końcowe,
- terminarz: sprawdziany, kartkówki, klasówki i zadania domowe,
- uwagi i pochwały,
- wiadomości wraz z treścią szczegółową,
- osiągnięcia,
- zebrania i konsultacje,
- dni wolne,
- publiczne informacje o szkole,
- lista nauczycieli,
- wychowawcy,
- szczęśliwy numerek,
- ważne dzisiaj,
- zrealizowane tematy lekcji,
- alerty i zdarzenia Home Assistant,
- panel boczny **Szkoła / School Hub**.

Każdy dodatkowy moduł jest pobierany niezależnie. Jeżeli jeden endpoint jest chwilowo niedostępny, pozostałe moduły nadal mogą się zaktualizować. mojV nie tworzy fikcyjnych rekordów zastępczych.

## Instalacja HACS

1. W HACS dodaj `https://github.com/gekon27/mojV` jako **Integration** w Custom repositories.
2. Wybierz `mojV` i zainstaluj wersję **0.11.0** lub nowszą.
3. Uruchom ponownie Home Assistant.
4. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację → mojV**.
5. Podaj dane konta szkolnego.

Po poprawnym logowaniu mojV wykryje wszystkich uczniów dostępnych na koncie i utworzy osobne urządzenie Home Assistant dla każdego z nich.

## mojV Auth Helper 0.1.9

Helper jest niezależną aplikacją Home Assistant i nie znajduje się w repozytorium HACS.

Instaluj go tylko wtedy, gdy Config Flow poinformuje, że konto wymaga pełnej przeglądarki.

1. Otwórz **Ustawienia → Apps / Aplikacje → App Store**.
2. Dodaj repozytorium `https://github.com/gekon27/mojv-auth-helper`.
3. Odśwież App Store.
4. Otwórz **mojV Auth Helper**.
5. Zainstaluj wersję **0.1.9** lub nowszą.
6. Uruchom aplikację i pozostaw automatyczny start włączony.
7. Wróć do konfiguracji integracji mojV i ponów logowanie.

Home Assistant pobiera gotowy publiczny obraz:

`ghcr.io/gekon27/mojv-auth-helper:0.1.9`

Obraz `0.1.9` jest publikowany jako manifest multi-arch dla `linux/amd64` i `linux/arm64` (`aarch64`). Pipeline publikacji zweryfikował oba obrazy, manifest platform oraz anonimowy pull bez poświadczeń GHCR.

## School Hub — panel boczny „Szkoła”

Panel korzysta wyłącznie z publicznego snapshotu zapisanego w Home Assistant. Zmiana dziecka, widoku lub tygodnia nie powoduje dodatkowego logowania do portalu.

### Pulpit

Pulpit zbiera najważniejsze dane ucznia w jednym miejscu:

- aktualna lekcja i lokalny licznik minut do końca,
- numer lekcji, sala, nauczyciel i obecność,
- następna lekcja,
- liczba nieprzeczytanych wiadomości,
- ostatnia ocena wraz z wagą,
- ogólna frekwencja,
- najbliższy sprawdzian / kartkówka / zadanie,
- najbliższe zebranie,
- ostatnia uwaga lub pochwała,
- ostatnie osiągnięcie,
- szczęśliwy numerek,
- ważne dzisiaj,
- następny dzień wolny,
- liczba zapisanych powiadomień,
- stan ostatniej synchronizacji.

### Widoki

Dostępne są m.in.:

- **Pulpit** — agregat najważniejszych informacji,
- **Dzisiaj** — aktualna/następna lekcja, plan dnia, obecność i alerty,
- **Plan** — tydzień, wspólne sloty godzinowe, bieżąca linia czasu, zastępstwa i anulowania,
- **Frekwencja** — podsumowanie stanów i ostatnie wpisy,
- **Oceny** — oceny cząstkowe i klasyfikacyjne,
- **Terminarz** — nadchodzące i ostatnie sprawdziany/zadania,
- **Uwagi** — uwagi i pochwały,
- **Wiadomości** — odebrane wiadomości i ich treść,
- **Statystyki** — frekwencja ogólna i per przedmiot,
- **Osiągnięcia** — wyróżnienia i wyniki,
- **Zebrania** — spotkania, miejsce, opis i bezpieczne linki online,
- **Informacje** — szkoła, wychowawcy, nauczyciele, dni wolne, usprawiedliwienia i bieżące informacje,
- **Tematy** — zrealizowane tematy lekcji,
- **Aktywność** — jedna chronologiczna oś najważniejszych zdarzeń,
- **Powiadomienia** — lokalna historia Notification Engine v2.

Zakładki danych dodatkowych są dynamiczne i zależą od rzeczywiście dostępnych danych. Układ jest responsywny dla desktopu, tabletu i telefonu.

## Encje Home Assistant

Dla każdego ucznia HACS 0.11.0 tworzy szeroką powierzchnię encji. Bazowo są to m.in.:

- aktualna i następna lekcja,
- numer lekcji i minuty do końca,
- obecność i plan dnia,
- klasa i ostatnia synchronizacja,
- ostatnia ocena, liczba ocen i oceny końcowe,
- nadchodzące zadania i najbliższy termin,
- nieprzeczytane wiadomości i licznik wiadomości,
- licznik uwag i pochwał,
- frekwencja procentowa, nieobecności i spóźnienia,
- osiągnięcia,
- nadchodzące zebrania i najbliższe zebranie,
- szczęśliwy numerek,
- ważne dzisiaj,
- ostatni zrealizowany temat oraz historia zrealizowanych tematów,
- następny dzień wolny oraz lista dni wolnych,
- informacje o szkole,
- wychowawca i nauczyciele,
- usprawiedliwienia.

Dodatkowo tworzone są dynamiczne sensory **per przedmiot** dla frekwencji i ocen oraz sensory **per okres klasyfikacyjny**.

Binary sensory obejmują:

- trwa lekcja,
- lekcja kończy się w ciągu 5 minut,
- nieobecny teraz,
- spóźniony teraz,
- są nieprzeczytane wiadomości,
- zbliża się termin szkolny,
- zbliża się zebranie,
- jest „ważne dzisiaj”.

Dostępne są trzy kalendarze:

- plan lekcji,
- sprawdziany / zadania,
- zebrania.

Dodatkowo istnieje wspólny sensor liczby wykrytych uczniów.

## Notification Engine v2

mojV wykrywa nowe dane i istotne zmiany pomiędzy kolejnymi snapshotami. Pierwsza synchronizacja prawdziwego konta tworzy **baseline** i nie generuje lawiny historycznych alertów.

Obsługiwane typy alertów obejmują m.in.:

- nowe i zmienione oceny,
- uwagi i pochwały,
- wiadomości,
- nieobecności i spóźnienia,
- odwołania, zastępstwa i zmiany sali/godziny/nauczyciela,
- zbliżający się koniec lekcji,
- nowe i zbliżające się terminy szkolne,
- nowe i zbliżające się zebrania,
- nowe osiągnięcia.

Kanały:

- persistent notification,
- event `mojv_notification`,
- kompatybilne starsze eventy dla wybranych zdarzeń,
- opcjonalny push do konkretnie wybranych encji `notify`.

Options Flow pozwala ustawić aktywne typy alertów, targety `notify`, próg końca lekcji, przypomnienia o zadaniach/zebraniach i godziny ciszy. Godziny ciszy wyciszają tylko push — historia i event bus nadal rejestrują alert.

Historia przechowuje maksymalnie 200 najnowszych, deduplikowanych rekordów na wpis konfiguracji.

## Bezpieczeństwo

- Chromium, ChromeDriver i Xvfb działają w osobnym kontenerze helpera,
- helper nie zapisuje hasła,
- cookies, tokeny, klucze sesji, mailbox keys i identyfikatory routingu pozostają wewnątrz warstwy transportu,
- surowe identyfikatory routingu wiadomości nie są przekazywane do Home Assistant,
- publiczne ID wiadomości jest stabilnym hashem,
- Core rekurencyjnie odrzuca niedozwolone pola uwierzytelniające/routingu w payloadzie helpera,
- panel, encje i historia powiadomień dostają wyłącznie publiczne dane potrzebne do działania,
- HACS 0.11.0 nie eksportuje wrażliwego profilu ucznia ani zdjęcia,
- awaria pojedynczego modułu danych lub pojedynczego targetu push nie zatrzymuje pozostałych modułów/odbiorców.

## Wydajność

- niezależne moduły są pobierane oddzielnie i z izolacją błędów,
- requesty są wykonywane współbieżnie tam, gdzie jest to bezpieczne,
- jeden `snapshot_builder` normalizuje dane niezależnie od backendu logowania,
- frontend nie odpytuje portalu przy lokalnym przełączaniu widoków,
- minutowy ticker powiadomień ocenia wyłącznie dane znajdujące się już w pamięci,
- Chromium pozostaje poza procesem Home Assistant Core.

## Diagnostyka

Przy starcie integracji HACS 0.11.0 w logu powinien pojawić się wpis:

`mojV integration version=0.11.0`

W logach helpera:

`mojV Auth Helper version=0.1.9`

Endpoint `/health` helpera raportuje status i wersję wewnątrz kontenera.

Nie publikuj loginu, hasła, cookies, tokenów, kluczy sesji ani kluczy routingu.

## Architektura

### `gekon27/mojV` — HACS

- `auth.py` — lekki flow logowania i wykrywanie potrzeby browser fallback,
- `helper_gateway.py` — komunikacja z helperem,
- `helper_protocol.py` — walidacja kontraktu i granicy sekretów,
- `school_api.py` — modułowe zapytania LIVE,
- `messages_api.py` — transport wiadomości,
- `parsers/` — normalizacja danych,
- `snapshot_builder.py` — wspólny snapshot,
- `models.py` — model danych,
- `sensor.py`, `binary_sensor.py`, `calendar.py` — powierzchnia encji HA,
- `notification_rules.py`, `notification_history.py`, `notifications.py` — Notification Engine v2,
- `config_flow.py` — logowanie oraz Options Flow,
- `panel_base.py` + `panel.py` — bezpieczny WebSocket payload School Hub,
- `frontend/school-panel.js` — bazowy panel,
- `frontend/school-panel-live.js` — widoki rozszerzonych modułów,
- `frontend/school-panel-hub-base.js` + `frontend/school-panel-hub.js` — School Hub, Pulpit, Aktywność, Powiadomienia, Informacje i Tematy.

### `gekon27/mojv-auth-helper` — Home Assistant App

Osobne repo zawiera metadata App Store, Dockerfile, Chromium/Xvfb runtime, rozszerzony snapshot LIVE, testy kontraktu, walidację obrazu i workflow publikujący publiczny obraz GHCR dla `amd64` oraz `aarch64`.

## CI / release

Repo HACS uruchamia:

- kompilację i testy Python,
- kontrolę składni czterech wykonywanych warstw panelu JavaScript,
- Hassfest,
- HACS validation,
- kontrolę spójności `manifest.json`, README i CHANGELOG,
- kontrolę zastrzeżonego nazewnictwa.

Budowanie i publikowanie helpera należy wyłącznie do `gekon27/mojv-auth-helper`.
