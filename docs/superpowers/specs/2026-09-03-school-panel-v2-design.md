# School Panel v2 — design

## Cel

Przebudować panel **Szkoła** w mojV tak, aby był szybszy, czytelniejszy i bardziej funkcjonalny, bez pogarszania stabilności działającego logowania. Panel ma prezentować realne dane szkolne w sposób aplikacyjny, a moduły bez danych mają pozostać ukryte zamiast pokazywać atrapy.

## Zakres etapu 1 — Panel Szkoła v2

- Jeden inicjalizowany raz DOM zamiast pełnego `shadowRoot.innerHTML` przy każdym odświeżeniu.
- Cache ostatniego payloadu i selektywne aktualizacje widoków.
- Lokalne odświeżanie zegara/progressu lekcji co 10 s bez zdalnego pobierania danych.
- Zdalne pobieranie panelu tylko przy pierwszym wejściu, ręcznym odświeżeniu oraz po zmianie danych koordynatora.
- Widoki: **Dzisiaj**, **Plan**, **Frekwencja**. Dodatkowe zakładki pojawiają się tylko wtedy, gdy backend zwraca odpowiadające im realne dane.
- Plan tygodniowy z nawigacją poprzedni / bieżący / następny tydzień.
- W planie: godziny, numer lekcji, przedmiot, sala, nauczyciel, obecność, zastępstwo, przeniesienie i odwołanie.
- Linia aktualnego czasu w bieżącym tygodniu.
- Responsywny układ desktop / tablet / telefon.
- Styl oparty o zmienne motywu Home Assistant z własnym akcentem mojV; mniej ciężkich gradientów i cieni.

## Zakres etapu 2 — Live Data v2

Rozszerzyć helper i modele integracji o kolejne rzeczywiste moduły, po jednym, z osobnymi testami parserów:

- oceny,
- terminarz / prace domowe,
- uwagi,
- wiadomości,
- osiągnięcia,
- zebrania.

Każdy moduł musi być pozyskany z realnego źródła konta. Brak danych nie może być zastępowany danymi demonstracyjnymi w trybie LIVE.

## Architektura frontendu

`school-panel.js` zostaje głównym web componentem, ale zostaje podzielony logicznie na trzy warstwy:

1. **Shell** — tworzony raz: topbar, wybór dziecka, nawigacja widoków, kontenery sekcji.
2. **State** — `_data`, aktywne dziecko, aktywny widok, offset tygodnia, znaczniki wersji danych.
3. **Renderers** — małe metody aktualizujące konkretne kontenery: today, schedule, attendance i moduły opcjonalne.

Renderowanie ma być idempotentne. Jeżeli payload nie zmienił się, panel nie przebudowuje list i tabel; aktualizuje wyłącznie elementy zależne od czasu.

## Przepływ danych

Home Assistant coordinator pozostaje jedynym miejscem okresowego pobierania danych zewnętrznych. WebSocket `mojv/panel` zwraca gotowy model do prezentacji. Frontend nie odpytuje portalu szkolnego i nie powoduje dodatkowego logowania.

WebSocket ma otrzymać argument `week_offset` (`-1`, `0`, `1`) i zwracać tydzień wskazany przez UI. Dla danych już znajdujących się w snapshotcie zmiana tygodnia nie może uruchamiać nowego logowania.

## Wydajność

- DOM shell tworzony dokładnie raz na cykl życia komponentu.
- Event listenery rejestrowane raz.
- Brak pełnego `innerHTML` całego panelu przy ticku czasu.
- `requestAnimationFrame` dla aktualizacji pozycji linii czasu.
- 10-sekundowy lokalny ticker tylko dla czasu i progressu.
- Widoki nieaktywne nie są przebudowywane.
- Preferencja dla CSS Grid/Flex bez bibliotek frontendowych i bez nowych zależności runtime.

## UX

### Dzisiaj

Najważniejszy ekran. Pokazuje aktualną lekcję, następną lekcję, czas do końca, numer lekcji, salę, nauczyciela i stan obecności. Pod spodem krótkie podsumowanie dnia i bieżące alerty.

### Plan

Tabela 5 dni × sloty godzinowe. Bieżący dzień i lekcja są wyróżnione. Linia czasu pokazuje pozycję w planie. Nawigacja tygodnia jest dostępna bez przeładowania całej strony.

### Frekwencja

Podsumowanie obecności, nieobecności, spóźnień i zwolnień dla danych dostępnych w aktualnym snapshotcie oraz lista wpisów z datą/lekcją.

### Moduły opcjonalne

Oceny, terminarz, wiadomości, uwagi, osiągnięcia i zebrania pojawiają się w nawigacji dopiero, gdy backend zwraca niepustą kolekcję lub jawny stan dostępności modułu.

## Licencje i repo referencyjne

Repo referencyjne jest GPL-3.0. Nie kopiujemy jego plików JS/CSS ani fragmentów implementacji. Wykorzystujemy wyłącznie obserwowane idee UX, zachowania i fakty dotyczące struktury danych/API, a kod mojV pozostaje implementacją własną.

## Bezpieczeństwo

- Frontend nie otrzymuje hasła, cookies ani kluczy sesji.
- Logi nie zawierają loginu, hasła, cookies ani tokenów.
- Dane diagnostyczne są ograniczone do typów odpowiedzi, liczników i bezpiecznych etapów.
- Nazwy techniczne portalu nie są używane w nazwach komponentów, plików, opisach UI ani dokumentacji projektu.

## Kryteria akceptacji etapu 1

- Panel działa w LIVE i DEMO.
- Przełączanie dziecka nie wykonuje nowego requestu WebSocket, jeśli dane są już w pamięci.
- Ticker 10 s nie wykonuje requestu WebSocket.
- Plan pozwala zmienić tydzień w zakresie `-1..1`.
- Aktualna lekcja i bieżący dzień są jednoznacznie widoczne.
- Mobile nie wymaga przewijania całego dashboardu w poziomie; poziome przewijanie jest dopuszczalne wyłącznie wewnątrz tabeli planu.
- `node --check` przechodzi.
- Testy Python, Hassfest i HACS przechodzą.

## Kryteria akceptacji etapu 2

Każdy nowy moduł ma własny parser/testy, dane LIVE pochodzą z prawdziwego endpointu i są prezentowane w UI bez atrap. Awaria pojedynczego modułu nie może blokować planu i frekwencji.
