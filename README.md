# mojV

![mojV](icon.svg)

Integracja Home Assistant dla danych szkolnych: plan lekcji, aktualna i następna lekcja, frekwencja, oceny, terminarz, uwagi i pochwały, wiadomości, osiągnięcia, zebrania, dni wolne, nauczyciele, tematy lekcji, automatyzacje i powiadomienia.

## Status

**HACS 0.13.0 — LIVE + plan na 4 pełne tygodnie do przodu + School Hub + pełnoekranowy dashboard przeglądarkowy + szczegóły po kliknięciu + Notification Engine v2 + samodzielny mojV Auth Helper 0.1.10.**

Projekt jest rozdzielony na dwa niezależne repozytoria:

- **HACS / Core:** `https://github.com/gekon27/mojV`
- **Home Assistant App / browser fallback:** `https://github.com/gekon27/mojv-auth-helper`

Integracja obsługuje **1..N dzieci**. Nie zakłada stałej liczby uczniów na koncie.

## Jak działa logowanie

mojV zawsze zaczyna od lekkiego backendu HTTP. Chromium nie jest uruchamiany, jeżeli nie jest potrzebny.

Jeżeli portal wymaga pełnej przeglądarki, integracja automatycznie korzysta z lokalnej aplikacji **mojV Auth Helper 0.1.10**. Użytkownik nie wybiera backendu ręcznie.

**HTTP first → automatyczny helper fallback.**

## Aktualny zakres LIVE

W HACS 0.13.0 obsługiwane są rzeczywiste dane:

- automatyczne wykrywanie 1..N dzieci,
- plan lekcji od poprzedniego tygodnia przez tydzień bieżący do końca czwartego pełnego tygodnia do przodu,
- aktualna i następna lekcja,
- numer lekcji i czas do końca,
- sale, nauczyciele, zastępstwa i odwołane lekcje,
- frekwencja bieżąca,
- rozszerzone statystyki frekwencji ogólne i per przedmiot,
- usprawiedliwienia,
- oceny cząstkowe wraz z wagą, gdy backend ją zwraca,
- oceny proponowane i okresowe/końcowe,
- terminarz: sprawdziany, kartkówki, klasówki i zadania domowe wraz z pełną bezpieczną treścią, gdy źródło ją zwraca,
- uwagi i pochwały,
- wiadomości wraz z treścią szczegółową,
- osiągnięcia,
- zebrania i konsultacje,
- dni wolne,
- publiczne informacje o szkole,
- lista nauczycieli,
- wychowawcy,
- szczęśliwy numerek,
- ważne dzisiaj wraz z opisem, gdy jest dostępny,
- zrealizowane tematy lekcji,
- alerty i zdarzenia Home Assistant,
- panel boczny **Szkoła / School Hub**,
- pełnoekranowy, uwierzytelniony dashboard Home Assistant pod `/mojv-dashboard`.

Każdy dodatkowy moduł jest pobierany niezależnie. Jeżeli jeden endpoint jest chwilowo niedostępny, pozostałe moduły nadal mogą się zaktualizować. mojV nie tworzy fikcyjnych rekordów zastępczych.

## Instalacja HACS

1. W HACS dodaj `https://github.com/gekon27/mojV` jako **Integration** w Custom repositories.
2. Wybierz `mojV` i zainstaluj wersję **0.13.0** lub nowszą.
3. Uruchom ponownie Home Assistant.
4. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację → mojV**.
5. Podaj dane konta szkolnego.

Po poprawnym logowaniu mojV wykryje wszystkich uczniów dostępnych na koncie i utworzy osobne urządzenie Home Assistant dla każdego z nich.

## mojV Auth Helper 0.1.10

Helper jest niezależną aplikacją Home Assistant i nie znajduje się w repozytorium HACS.

Instaluj go tylko wtedy, gdy Config Flow poinformuje, że konto wymaga pełnej przeglądarki.

1. Otwórz **Ustawienia → Apps / Aplikacje → App Store**.
2. Dodaj repozytorium `https://github.com/gekon27/mojv-auth-helper`.
3. Odśwież App Store.
4. Otwórz **mojV Auth Helper**.
5. Zainstaluj wersję **0.1.10** lub nowszą.
6. Uruchom aplikację i pozostaw automatyczny start włączony.
7. Wróć do konfiguracji integracji mojV i ponów logowanie.

Home Assistant pobiera gotowy publiczny obraz:

`ghcr.io/gekon27/mojv-auth-helper:0.1.10`

Obraz `0.1.10` jest publikowany jako manifest multi-arch dla `linux/amd64` i `linux/arm64` (`aarch64`). Pipeline publikacji weryfikuje oba obrazy, manifest platform oraz anonimowy pull bez poświadczeń GHCR.

## School Hub — panel boczny „Szkoła”

Panel korzysta wyłącznie z publicznego snapshotu zapisanego w Home Assistant. Zmiana dziecka, widoku lub tygodnia nie powoduje dodatkowego logowania do portalu. HACS 0.13.0 pozwala lokalnie przeglądać poprzedni tydzień, tydzień bieżący i cztery pełne tygodnie do przodu bez dodatkowego requestu przy zmianie tygodnia.

Od HACS 0.12.0 backend panelu deduplikuje uczniów po stabilnym `student_id`. Jeżeli ten sam uczeń występuje w więcej niż jednym aktywnym wpisie konfiguracji, do interfejsu trafia tylko najświeższy snapshot i nie pojawiają się podwójne przyciski dziecka.

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
- **Plan** — tydzień, wspólne sloty godzinowe, bieżąca linia czasu, zastępstwa i anulowania; lekcja bieżąca, odbyta, przyszła i odwołana mają osobne stany wizualne i tekstowe znaczniki; nawigacja obejmuje poprzedni tydzień oraz cztery pełne tygodnie do przodu,
- **Frekwencja** — podsumowanie stanów i ostatnie wpisy,
- **Oceny** — oceny cząstkowe i klasyfikacyjne,
- **Terminarz** — nadchodzące i ostatnie sprawdziany/zadania; lista pokazuje skrót opisu, a kliknięcie otwiera pełną treść,
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

### Szczegóły po kliknięciu

W HACS 0.12.0 Terminarz, zadania domowe, sprawdziany/kartkówki oraz wpisy „Ważne dzisiaj” korzystają ze wspólnego widoku szczegółów:

- na liście widoczny jest krótki, bezpiecznie escapowany podgląd,
- kliknięcie lub aktywacja klawiaturą otwiera dialog z pełną treścią dostępną LIVE,
- `Esc`, przycisk zamknięcia lub kliknięcie tła zamyka dialog,
- fokus wraca do elementu, który otworzył szczegóły,
- na telefonie dialog działa jak pełnoszeroki bottom sheet,
- surowy HTML ze źródła nie jest wstrzykiwany do DOM.

Jeżeli źródło nie udostępnia dodatkowej treści, interfejs pokazuje neutralny komunikat „Brak dodatkowej treści”.

## Dashboard przeglądarkowy

HACS 0.12.0 rejestruje drugi, pełnoekranowy panel Home Assistant:

`/mojv-dashboard`

Dashboard:

- pozostaje za standardowym uwierzytelnianiem Home Assistant,
- nie ma osobnego loginu, tokenu ani publicznego API,
- korzysta z tego samego bezpiecznego payloadu i renderera co School Hub,
- obsługuje ten sam wybór dziecka i te same widoki,
- jest przeznaczony do desktopu, tabletu lub przeglądarki kioskowej,
- może być otwarty przyciskiem **Otwórz dashboard** z School Hub.

## Encje Home Assistant

Dla każdego ucznia HACS 0.12.0 tworzy szeroką powierzchnię encji. Bazowo są to m.in.:

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
- panel, dashboard, encje i historia powiadomień dostają wyłącznie publiczne dane potrzebne do działania,
- pełne treści są whitelistowane i renderowane jako bezpieczny tekst; surowy zdalny HTML nie trafia bezpośrednio do DOM,
- HACS 0.12.0 nie eksportuje wrażliwego profilu ucznia ani zdjęcia,
- dashboard przeglądarkowy korzysta ze standardowego uwierzytelniania Home Assistant i nie wprowadza osobnego magazynu poświadczeń,
- awaria pojedynczego modułu danych lub pojedynczego targetu push nie zatrzymuje pozostałych modułów/odbiorców.

## Wydajność

- niezależne moduły są pobierane oddzielnie i z izolacją błędów,
- requesty są wykonywane współbieżnie tam, gdzie jest to bezpieczne,
- jeden `snapshot_builder` normalizuje dane niezależnie od backendu logowania,
- pełny plan na sześciotygodniowy zakres cache (poprzedni + bieżący + 4 przyszłe tygodnie) nadal jest pobierany jednym requestem `PlanZajec` na ucznia podczas pełnego odświeżenia,
- adaptacyjne odświeżanie LIVE ustawia następny pełny refresh około 2 min po najbliższym końcu lekcji, a poza taką granicą nie czeka dłużej niż 60 minut,
- frontend nie odpytuje portalu przy lokalnym przełączaniu widoków lub tygodni planu,
- dashboard przeglądarkowy reuse’uje ten sam komponent i payload zamiast uruchamiać drugi poller,
- minutowy ticker powiadomień ocenia wyłącznie dane znajdujące się już w pamięci,
- Chromium pozostaje poza procesem Home Assistant Core.

## Diagnostyka

Przy starcie integracji HACS 0.13.0 w logu powinien pojawić się wpis:

`mojV integration version=0.13.0`

W logach helpera:

`mojV Auth Helper version=0.1.10`

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
- `refresh_policy.py` — adaptacyjna polityka pełnego odświeżania LIVE,
- `sensor.py`, `binary_sensor.py`, `calendar.py` — powierzchnia encji HA,
- `notification_rules.py`, `notification_history.py`, `notifications.py` — Notification Engine v2,
- `config_flow.py` — logowanie oraz Options Flow,
- `panel_students.py` — deterministyczna deduplikacja publicznych wierszy uczniów,
- `panel_base.py` + `panel.py` — bezpieczny WebSocket payload School Hub i rejestracja paneli,
- `frontend/school-panel.js` — bazowy panel,
- `frontend/school-panel-live.js` — widoki rozszerzonych modułów,
- `frontend/school-panel-hub-base.js` + `frontend/school-panel-hub.js` — School Hub, Pulpit, Aktywność, Powiadomienia, Informacje i Tematy,
- `frontend/school-panel-details.js` — bezpieczne preview i dialogi pełnej treści,
- `frontend/school-panel-lesson-states.js` — klasyfikacja i wizualizacja stanów lekcji oraz nawigacja po rozszerzonym horyzoncie planu,
- `frontend/school-dashboard.js` — pełnoekranowy wrapper przeglądarkowy reuse’ujący School Hub.

### `gekon27/mojv-auth-helper` — Home Assistant App

Osobne repo zawiera metadata App Store, Dockerfile, Chromium/Xvfb runtime, rozszerzony snapshot LIVE, testy kontraktu, walidację obrazu i workflow publikujący publiczny obraz GHCR dla `amd64` oraz `aarch64`.

## CI / release

Repo HACS uruchamia:

- kompilację i testy Python,
- kontrolę składni siedmiu wykonywanych modułów JavaScript panelu/dashboardu,
- Hassfest,
- HACS validation,
- kontrolę spójności `manifest.json`, README i CHANGELOG,
- kontrolę zastrzeżonego nazewnictwa.

Budowanie i publikowanie helpera należy wyłącznie do `gekon27/mojv-auth-helper`.
