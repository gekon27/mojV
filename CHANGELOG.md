# Changelog

## [0.14.0] - 2026-09-04

- skorygowano horyzont planu do dokładnie czterech tygodni łącznie: poprzedni (`-1`), bieżący (`0`) oraz dwa kolejne (`+1`, `+2`); Core i browser fallback używają tego samego zakresu,
- Plan otrzymał jawny stan **Przerwa** pomiędzy lekcjami, osobne stany wizualne i tekstowe **Teraz / Odbyta / Odwołana** oraz mocniej przygaszony wygląd lekcji zakończonych,
- zakładki **Oceny** i **Wiadomości** są stałe i nie znikają przy pustych danych; Wiadomości pokazują neutralny pusty stan,
- widok **Tematy** umożliwia sortowanie po dacie rosnąco/malejąco, a **Informacje** zostały przeniesione za Tematy,
- dodano drukowanie planu, frekwencji i dedykowanego widoku statystyk z regułami `@media print`,
- Terminarz zawsze pobiera dedykowane szczegóły dla obsługiwanych sprawdzianów/kartkówek/klasówek/zadań, dzięki czemu skrót z listy nie może zastąpić pełnej treści,
- Terminarz pokazuje typ wpisu, przedmiot, nauczyciela, datę utworzenia gdy portal rozróżnia ją od terminu, termin wykonania/wydarzenia oraz opis; kliknięcie otwiera pełny, bezpieczny dialog szczegółów,
- dla zadania domowego `terminOdpowiedzi` jest terminem wykonania, a odrębne `data` z payloadu szczegółowego może zostać zachowane jako data utworzenia/wpisu; dla sprawdzianu bez osobnego pola utworzenia mojV nie zgaduje wartości i pokazuje brak danych,
- kalendarz **Terminarz szkolny** otrzymał te same bezpieczne metadane nauczyciela, daty utworzenia/terminu i opisu,
- pełne opisy są czyszczone do tekstu i escapowane w UI; odpowiedzi ucznia, jego załączniki oraz auth/session/mailbox/routing fields pozostają poza publicznym payloadem,
- helper **0.1.11** został opublikowany jako publiczny obraz multi-arch i zawsze wzbogaca obsługiwane wpisy Terminarza z dedykowanych endpointów szczegółów; publikacja potwierdziła manifest platform oraz anonimowy pull,
- zachowano adaptacyjne odświeżanie LIVE: około 2 min po najbliższym końcu lekcji i maksymalnie 60 min poza taką granicą,
- końcowy funkcjonalny gate przed release przechodzi 145 testów Python, 7 kontroli składni JavaScript, Hassfest i HACS.

## [0.13.0] - 2026-09-04

- rozszerzono zakres planu lekcji w bezpośrednim HTTP do poprzedniego tygodnia, tygodnia bieżącego oraz czterech pełnych tygodni do przodu,
- ten sam zakres dat wdrożono w samodzielnym mojV Auth Helper 0.1.10, dzięki czemu HTTP-first i Chromium fallback zachowują parity,
- Plan w School Hub i `/mojv-dashboard` pozwala lokalnie przechodzić od poprzedniego tygodnia do czwartego przyszłego tygodnia bez dodatkowego requestu do portalu przy zmianie tygodnia,
- rozszerzony horyzont nadal korzysta z pojedynczego requestu `PlanZajec` na ucznia podczas pełnego odświeżenia,
- zachowano adaptacyjne odświeżanie LIVE z 0.12.0: pełny refresh około 2 min po najbliższym końcu lekcji oraz maksymalnie co 60 min poza taką granicą,
- dodano testy RED→GREEN dla dokładnego zakresu dat requestu, nawigacji do `+4` oraz parity browser fallback,
- funkcjonalny Core przechodzi 135 testów, 7 kontroli składni JavaScript, Hassfest i HACS,
- granica bezpieczeństwa nie została zmieniona; szerszy plan nie dodaje nowych danych uwierzytelniających ani routingu do publicznego snapshotu.

## [0.12.0] - 2026-09-04

- naprawiono podwójne wpisy uczniów w School Hub: backend deduplikuje publiczne wiersze po stabilnym `student_id`, zachowuje deterministyczną kolejność i wybiera najświeższy snapshot bez ślepego łączenia pól z dwóch wpisów konfiguracji,
- dodano uwierzytelniony, pełnoekranowy dashboard Home Assistant pod `/mojv-dashboard`; dashboard reuse’uje istniejący `mojv-school-panel`, ten sam bezpieczny WebSocket `mojv/panel` i standardowe logowanie Home Assistant,
- School Hub otrzymał akcję **Otwórz dashboard** bez uruchamiania dodatkowego pollera ani osobnego API,
- Terminarz, zadania domowe, sprawdziany i kartkówki pokazują krótki preview treści, a kliknięcie otwiera pełny bezpieczny opis dostępny LIVE,
- wpisy „Ważne dzisiaj” mogą zachować whitelistowany dłuższy opis z normalizowanego payloadu i korzystają z tego samego dialogu szczegółów,
- dialog szczegółów obsługuje klawiaturę, `Esc`, przywracanie fokusu, zamknięcie tłem oraz mobilny wariant bottom-sheet; surowy zdalny HTML nie jest wstrzykiwany do DOM,
- Plan rozróżnia stany `current`, `completed`, `upcoming` i `cancelled`; użytkownik widzi tekstowe znaczniki **Teraz**, **Odbyta** i **Odwołana**, więc semantyka nie zależy wyłącznie od koloru,
- zastępstwo pozostaje niezależnym badge’em i może występować równocześnie ze stanem czasowym lekcji,
- klasy stanów są stosowane w planie dnia i tygodniowym, a ticker lokalnie aktualizuje je wraz z upływem czasu bez requestów do portalu,
- dodano czysty `panel_students.py` oraz testy RED→GREEN deduplikacji, pełnych opisów, dialogów szczegółów, stanów lekcji, dashboardu i pokrycia CI,
- CI sprawdza składnię wszystkich siedmiu wykonywanych modułów JavaScript School Hub/dashboardu,
- pełny pre-release gate przechodzi 127 testów Python, kontrolę spójności wersji i zastrzeżonego nazewnictwa, Hassfest oraz HACS,
- granica bezpieczeństwa pozostaje bez zmian: dashboard i szczegóły nie otrzymują credentials, cookies, session/mailbox/routing keys, danych rodziców ani wrażliwego profilu ucznia,
- helper pozostaje w wersji `0.1.9`; zmiany 0.12.0 nie wymagają nowego runtime browser fallback.

## [0.11.0] - 2026-09-04

- rozszerzono bezpieczną warstwę LIVE o dni wolne, usprawiedliwienia, nauczycieli, publiczne informacje o szkole, szczęśliwy numerek, „ważne dzisiaj”, wychowawców i zrealizowane tematy lekcji,
- nowe moduły są pobierane niezależnie z izolacją błędów; awaria pojedynczego endpointu nie blokuje pozostałych danych ucznia,
- wspólny model i `snapshot_builder` przekazują nowe moduły identycznie dla lekkiego HTTP i browser fallback,
- samodzielny **mojV Auth Helper 0.1.9** uzyskał parity dla nowych modułów przy zachowaniu granicy bezpieczeństwa i obsługi 1..N dzieci,
- helper 0.1.9 został opublikowany jako publiczny obraz multi-arch `amd64` + `arm64`; pipeline potwierdził manifest platform i anonimowy pull bez poświadczeń GHCR,
- wrażliwy profil ucznia i zdjęcie pozostają poza publicznym snapshotem, panelem i powierzchnią encji,
- rozszerzono `sensor.py` do 33 bazowych sensorów per uczeń oraz dynamicznych sensorów frekwencji/ocen per przedmiot i ocen per okres klasyfikacyjny,
- rozszerzono `binary_sensor.py` do 8 praktycznych flag per uczeń: lekcja trwa/kończy się, nieobecność, spóźnienie, wiadomości, pilny termin, pilne zebranie i „ważne dzisiaj”,
- dodano trzy kalendarze: plan lekcji, sprawdziany/zadania oraz zebrania,
- School Hub otrzymał widoki **Informacje** i **Tematy**, a Pulpit pokazuje dodatkowo szczęśliwy numerek, ważne dzisiaj i następny dzień wolny,
- rozdzielono duży kod panelu na stabilne warstwy `panel_base.py` + `panel.py` oraz `school-panel-hub-base.js` + `school-panel-hub.js`, bez zmiany istniejących widoków Pulpit/Aktywność/Powiadomienia,
- CI sprawdza składnię wszystkich czterech wykonywanych modułów JavaScript panelu,
- pełny zestaw Core przechodzi 109 testów Python, kontrolę zastrzeżonego nazewnictwa, Hassfest i HACS,
- README, manifest i changelog zsynchronizowane do `0.11.0`; dokumentacja wskazuje opublikowany helper `0.1.9`.

## [0.10.0] - 2026-09-04

- przebudowano panel boczny **Szkoła** do pełnego **School Hub** z domyślnym widokiem **Pulpit**,
- Pulpit agreguje aktualną/następną lekcję, czas do końca, obecność, liczbę wiadomości, ostatnią ocenę wraz z wagą, frekwencję, najbliższy termin i zebranie, ostatnią uwagę/pochwałę, osiągnięcie i synchronizację,
- dodano widok **Aktywność** łączący w jednej osi oceny, klasyfikację, uwagi/pochwały, wiadomości, terminarz, zebrania, osiągnięcia i frekwencję,
- dodano widok **Powiadomienia** z lokalną historią maksymalnie 200 deduplikowanych alertów per wpis konfiguracji,
- dodano badge dla nieprzeczytanych wiadomości, nadchodzących terminów/zebrań i historii alertów,
- frontend 0.10.0 jest trzecią cienką warstwą `school-panel-hub.js`; nie wprowadza osobnego pollera ani dodatkowego logowania,
- dodano **Notification Engine v2** z czystymi regułami w `notification_rules.py`, historią w `notification_history.py` i transportem HA w `notifications.py`,
- wykrywane są: nowe oceny, zmiany ocen proponowanych/końcowych, uwagi, pochwały, wiadomości, nieobecności, spóźnienia, odwołania, zastępstwa, zmiany sali/godziny/nauczyciela, nowe terminy, zebrania i osiągnięcia,
- dodano przypomnienia czasowe: koniec lekcji, zbliżający się sprawdzian/zadanie oraz zebranie,
- przypomnienia czasowe korzystają z lokalnego tickera co 1 minutę i nie powodują requestu ani ponownego logowania do portalu,
- pierwsza synchronizacja prawdziwego konta tworzy baseline i nie generuje lawiny historycznych alertów,
- każdy alert ma stabilny `event_id`; historia trwale blokuje duplikaty po odświeżeniu i restarcie,
- dodano wspólny event `mojv_notification`, zachowując kompatybilne eventy `mojv_lesson_late`, `mojv_lesson_absent`, `mojv_new_grade` i `mojv_new_remark`,
- persistent notifications i event bus działają niezależnie od opcjonalnego push,
- dodano Options Flow z wyborem 16 typów alertów, konkretnych encji `notify`, progów 5 min / 24 h / 24 h oraz godzin ciszy,
- godziny ciszy wyciszają tylko push; historia, persistent notification i event bus nadal rejestrują alert,
- awaria pojedynczego targetu push jest izolowana i nie blokuje pozostałych odbiorców,
- dodano polskie i angielskie tłumaczenia Options Flow i nazw typów powiadomień,
- historia, panel i eventy nie zawierają cookies, tokenów, mailbox/session keys ani surowych identyfikatorów routingu,
- „szczęśliwy numerek” nie jest prezentowany, dopóki rzeczywiste źródło LIVE nie zostanie osobno potwierdzone i przetestowane,
- CI sprawdza `school-panel.js`, `school-panel-live.js` i `school-panel-hub.js`, testy Python, Hassfest i HACS,
- README, manifest i changelog zsynchronizowane do `0.10.0`; helper pozostaje w wersji `0.1.8`.

## [0.9.0] - 2026-09-04

- dodano rzeczywiste moduły LIVE: uwagi/pochwały, wiadomości, osiągnięcia i zebrania,
- rozszerzono frekwencję o statystyki ogólne oraz per przedmiot,
- wiadomości są pobierane z osobnego tenantu i łączone z treścią szczegółową,
- surowe `globalKeySkrzynka` i `apiGlobalKey` nie opuszczają warstwy transportu; publiczne ID wiadomości jest stabilnym hashem,
- Core rekurencyjnie odrzuca mailbox/session/routing fields również w zagnieżdżonych payloadach helpera,
- panel **Szkoła** otrzymał dynamiczne widoki **Wiadomości**, **Statystyki**, **Osiągnięcia** i **Zebrania**; zakładki pojawiają się tylko przy prawdziwych danych,
- helper `0.1.8` uzyskał parity z bezpośrednim HTTP dla nowych modułów przy zachowaniu HTTP-first i automatycznego fallbacku,
- zachowano obsługę 1..N dzieci oraz izolację błędów per moduł,
- CI sprawdza obie warstwy JavaScript panelu, testy Python, Hassfest i HACS,
- dodano testy RED→GREEN dla kontraktu panelu, sekretów/routingu i helpera `0.1.8`,
- README, manifest i changelog zsynchronizowane do `0.9.0`.

## [0.8.1] - 2026-09-04

- zakończone atomowe rozdzielenie HACS i browser-auth: `mojV` jest ponownie czystym repozytorium integracji Home Assistant,
- `mojV Auth Helper` został przeniesiony do osobnego repozytorium `https://github.com/gekon27/mojv-auth-helper`,
- helper podniesiony do `0.1.7`; zachowano ten sam kontrakt runtime i automatyczny fallback po lekkim HTTP,
- osobne repo helpera ma własne metadata App Store, README/DOCS/CHANGELOG, testy, CI oraz publikowanie GHCR,
- potwierdzono build i uruchomienie obrazu `amd64`, `/health`, Xvfb, Chromium i ChromeDriver,
- potwierdzono build `aarch64`, publikację manifestu multi-arch i anonimowy pull `ghcr.io/gekon27/mojv-auth-helper:0.1.7`,
- z repo HACS usunięto `repository.yaml`, katalog `mojv_auth_helper/`, workflow publikowania helpera i testy zależne od plików aplikacji,
- zachowano `helper_gateway.py` i `helper_protocol.py`, ponieważ są częścią lekkiej integracji i obsługują automatyczny fallback,
- CI HACS nie buduje już Chromium; sprawdza wyłącznie Core, panel, testy, Hassfest i HACS,
- README zaktualizowany do instalacji helpera z osobnego repozytorium,
- README, manifest i changelog zsynchronizowane do `0.8.1`.

## [0.8.0] - 2026-09-03

- dodane rzeczywiste dane LIVE ocen cząstkowych oraz ocen proponowanych i okresowych/końcowych,
- dodane rzeczywiste dane LIVE terminarza: sprawdziany, kartkówki, klasówki i zadania domowe,
- plan lekcji wysyła pełny aktualny zakres danych wymagany przez endpoint,
- nowy wspólny `snapshot_builder` normalizuje dane identycznie dla lekkiego backendu HTTP i helpera Chromium,
- parser ocen obsługuje okresy klasyfikacyjne, opisy/kategorie oraz daty ISO i polski format daty,
- parser terminarza mapuje typy zdarzeń, preferuje termin odpowiedzi i czyści HTML przed przekazaniem danych do Home Assistant,
- błędy modułów są izolowane: awaria ocen lub terminarza nie zatrzymuje planu ani frekwencji,
- helper 0.1.6 pobiera rozszerzony snapshot bez eksportowania identyfikatorów routingu, kluczy sesji, cookies lub tokenów,
- Core rekurencyjnie sprawdza cały payload helpera i odrzuca niedozwolone pola uwierzytelniające także w zagnieżdżonych danych,
- panel **Szkoła** otrzymał osobne widoki **Oceny** i **Terminarz**,
- widok ocen pokazuje najnowsze oceny oraz klasyfikację proponowaną i końcową,
- terminarz rozdziela nadchodzące zdarzenia od ostatnich terminów i wyróżnia pilne zadania,
- ekran **Dzisiaj** pokazuje najbliższe zadanie, gdy nie ma pilniejszego alertu lekcji/frekwencji,
- zachowana szybka architektura Panelu v2: DOM tworzony raz, ticker 10 s i lokalne przełączanie dziecka/widoku/tygodnia,
- dodane testy RED→GREEN parserów, klienta API, kontraktu helpera, filtracji sekretów, wspólnego buildera oraz panelu,
- README, manifest i changelog zsynchronizowane do `0.8.0`.

## [0.7.0] - 2026-09-03

- przebudowany panel **Szkoła** do architektury aplikacyjnej z DOM tworzonym jeden raz zamiast pełnego rerenderu przy każdym odświeżeniu,
- lokalny zegar i postęp lekcji aktualizują się co 10 s bez zapytań WebSocket i bez dodatkowego logowania,
- dodane osobne widoki **Dzisiaj**, **Plan** i **Frekwencja** oraz dynamiczne zakładki **Oceny** i **Uwagi** tylko wtedy, gdy istnieją rzeczywiste dane,
- przełączanie dziecka i widoku odbywa się całkowicie lokalnie na już pobranym payloadzie,
- plan obsługuje lokalną nawigację poprzedni / bieżący / następny tydzień bez pobierania danych z portalu,
- plan tygodniowy grupuje lekcje po rzeczywistych slotach godzinowych niezależnie od daty, dzięki czemu te same godziny od poniedziałku do piątku zajmują wspólny wiersz,
- dodana linia aktualnego czasu, wyróżnienie trwającej lekcji, anulowania i zastępstwa,
- dodany backendowy agregat frekwencji pomijający odwołane lekcje i rozdzielający wszystkie obsługiwane stany,
- przebudowany responsywny wygląd z wykorzystaniem zmiennych motywu Home Assistant; poziome przewijanie na telefonie jest ograniczone do tabeli planu,
- nie dodano nowych zależności frontendowych ani kodu skopiowanego z repo referencyjnego,
- dodane testy regresyjne architektury renderowania, lokalnego tickera, lokalnej nawigacji tygodnia, grupowania slotów i agregacji frekwencji,
- README, manifest i changelog zsynchronizowane do `0.7.0`.

## [0.6.4] - 2026-09-03

- integracja zapisuje przy starcie numer wersji z własnego `manifest.json`,
- log Core pokazuje także tryb pracy i backend uwierzytelniania bez ujawniania danych logowania,
- helper zapisuje przy starcie numer wersji obrazu przekazany przez `MOJV_HELPER_VERSION`,
- helper podniesiony do `0.1.5`, aby App Store jednoznacznie widział zmianę,
- README, manifest i changelog zsynchronizowane do `0.6.4`.

## [0.6.3] - 2026-09-03

- zsynchronizowana wersja integracji HACS z aktualnym helperem `0.1.4`,
- nowy release HACS wymusza widoczną aktualizację po zmianach browser-auth,
- helper akceptuje poprawne przekierowanie na host ucznia bez wymagania ścieżki `/App/...`,
- zachowane timeout recovery, Xvfb, Chromium i bezpieczna diagnostyka etapów logowania,
- README, manifest i changelog zsynchronizowane do `0.6.3`.

## [0.6.2] - 2026-09-03

- poprawiony browser-auth na podstawie porównania z działającym rozwiązaniem referencyjnym bez kopiowania jego kodu,
- helper 0.1.2 uruchamia Chromium z wirtualnym ekranem Xvfb i klasycznym `--headless` zamiast `--headless=new`,
- dodane kontrolowane opóźnienie pomiędzy wysłaniem loginu i etapem hasła,
- dodane bezpieczne etapy diagnostyczne `login-page`, `username-submitted`, `password-submitted`, `diary-links`, `student-app`, `context`,
- logowana lokalizacja strony nie zawiera query string ani danych uwierzytelniających,
- przy błędzie helper zapisuje lokalny screenshot po wyczyszczeniu wartości pól formularza,
- `/health` raportuje wersję helpera przekazaną podczas budowania obrazu,
- CI sprawdza obecność Xvfb, start Chromium oraz zgodność wersji `/health`,
- README, manifest i changelog zsynchronizowane do 0.6.2.

## [0.6.1] - 2026-09-03

- helper przeglądarkowy jest publikowany jako gotowy obraz GHCR zamiast budowania lokalnie na Home Assistant,
- dodany prebuilt multi-arch image dla `amd64` i `aarch64`,
- usunięta zależność instalacji helpera od dostępu Home Assistant do PyPI podczas lokalnego `docker build`,
- `mojv_auth_helper/config.yaml` wskazuje teraz bezpośrednio obraz `ghcr.io/gekon27/mojv-auth-helper`,
- dodany workflow publikujący obrazy helpera do GHCR,
- CI wymusza obecność prebuilt image w konfiguracji aplikacji,
- README i manifest zsynchronizowane do wersji 0.6.1.

## [0.6.0] - 2026-09-03

- dodany opcjonalny lokalny **mojV Auth Helper** z Chromium dla kont wymagających pełnej przeglądarki,
- integracja automatycznie próbuje lekkiego logowania HTTP i przełącza się na helper tylko wtedy, gdy jest to wymagane,
- helper utrzymuje cookies i klucze sesji wyłącznie we własnym kontenerze,
- helper nie zapisuje hasła i nie zwraca do Home Assistant cookies, tokenów ani kluczy sesji,
- komunikacja integracja ↔ helper odbywa się wyłącznie w wewnętrznej sieci Home Assistant,
- helper zwraca tylko dane ucznia, plan lekcji i frekwencję,
- dodane automatyczne wykrywanie uruchomionego helpera przez Supervisor,
- dodane czytelne komunikaty `helper_required` i `helper_failed` w Config Flow,
- pole logowania obsługuje login, alias lub e-mail,
- dodane testy kontraktu helpera, bramki Supervisor i filtracji sekretów,
- dodana paczka aplikacji Home Assistant w `mojv_auth_helper/`,
- dodana walidacja wersji README / manifest / CHANGELOG.

## [0.5.2] - 2026-09-03

- poprawiony pełny flow logowania HTTP,
- dodany etap identyfikacji konta przed finalnym logowaniem,
- dodana obsługa formularzy przekazania SSO,
- dodane rozpoznawanie klucza aplikacji z adresu dziennika,
- dodana obsługa odpowiedzi kontekstu opakowanych w `data` / `result`,
- rozszerzona bezpieczna diagnostyka wykrywania uczniów,
- dodane testy regresyjne dla aktualnego flow logowania,
- przygotowane automatyczne tagowanie/release dla HACS,
- synchronizacja wersji README / manifest / CHANGELOG wymuszana przez CI.

## [0.5.1] - 2026-09-03

- dodana migracja starszego wpisu konfiguracji,
- identyfikator dziennika przestał być wymagany do utworzenia kontekstu ucznia,
- poprawiona diagnostyka `no_students`.

## [0.5.0] - 2026-09-03

- przebudowany panel boczny **Szkoła**,
- pełny plan poniedziałek-piątek,
- zakładki wielu dzieci,
- aktualna i następna lekcja,
- frekwencja i alerty,
- sekcje ocen i uwag,
- branding mojV.