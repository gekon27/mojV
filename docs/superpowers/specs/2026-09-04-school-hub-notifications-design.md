# mojV 0.10.0 — School Hub + Notification Engine v2

## Cel

Rozszerzyć `mojV` o pełny panel boczny „Szkoła” oraz konfigurowalny system powiadomień, wykorzystując wyłącznie rzeczywiste dane LIVE. Zachować HTTP-first, automatyczny browser fallback, obsługę 1..N dzieci i obecne granice bezpieczeństwa.

## Zakres funkcjonalny

### School Hub

Panel boczny otrzymuje widok `Pulpit` jako agregat najważniejszych danych ucznia:
- aktualna lekcja, czas do końca, numer lekcji, sala, nauczyciel i obecność,
- następna lekcja,
- postęp dnia,
- liczba nieprzeczytanych wiadomości,
- najnowsza ocena,
- najbliższy sprawdzian/kartkówka/zadanie,
- najbliższe zebranie,
- ostatnia uwaga lub pochwała,
- ogólna frekwencja,
- ostatnie osiągnięcie,
- ostatnia synchronizacja,
- bieżące alerty planu: zastępstwo, odwołanie, zmiana sali/godziny jeśli dane backendu to potwierdzają.

Panel zachowuje dotychczasowe widoki i rozszerza je o:
- `Aktywność` — wspólna chronologiczna oś zdarzeń LIVE,
- `Powiadomienia` — lokalna historia powiadomień mojV.

Zakładki związane z modułem pozostają dynamiczne i są pokazywane tylko wtedy, gdy istnieją rzeczywiste dane. Dopuszczalne są liczniki/badge, np. liczba nieprzeczytanych wiadomości lub nadchodzących zdarzeń.

### Notification Engine v2

System wykrywa i emituje zdarzenia dla:
- nowej oceny,
- zmiany oceny proponowanej/okresowej,
- nowej uwagi,
- nowej pochwały,
- nowej wiadomości,
- nieobecności,
- spóźnienia,
- odwołania lekcji,
- zastępstwa,
- zmiany sali/godziny,
- zbliżającego się końca lekcji,
- nowego zadania/sprawdzianu/kartkówki,
- zbliżającego się zadania/sprawdzianu/kartkówki,
- nowego zebrania,
- zbliżającego się zebrania,
- nowego osiągnięcia.

Pierwsza synchronizacja LIVE tworzy baseline i nie generuje lawiny powiadomień dla danych historycznych.

Każdy alert ma:
- stabilny `event_id`,
- `student_id`, `student_name`,
- `kind`, `priority`,
- `title`, `message`,
- `created_at`,
- bezpieczne `data` bez sekretów.

### Kanały

Zawsze:
- `persistent_notification` Home Assistant,
- event na `hass.bus`.

Opcjonalnie:
- push do wybranych serwisów/encji `notify` wskazanych w Options Flow.

Nie wysyłać automatycznie na wszystkie telefony. Użytkownik wybiera odbiorców.

### Options Flow

Dodać ustawienia niezwiązane z logowaniem:
- włączone typy powiadomień,
- lista docelowych serwisów/encji `notify`,
- minuty przed końcem lekcji, domyślnie 5,
- minuty/godziny przed zadaniem/sprawdzianem, domyślnie 24 h,
- minuty/godziny przed zebraniem, domyślnie 24 h,
- opcjonalne godziny ciszy.

Brak konfiguracji push nie może blokować persistent notifications ani eventów.

## Historia

Nowy `NotificationHistory` przechowuje maksymalnie 200 rekordów na wpis konfiguracji w `Store`. Rekordy są posortowane malejąco po czasie. Historia nie zawiera danych logowania, cookies, mailbox/session/routing keys ani surowych identyfikatorów wiadomości.

Panel może odczytać historię przez istniejący WebSocket `mojv/panel` jako bezpieczne pole `notifications`.

## Architektura

### Backend

- `notification_rules.py` — czyste reguły różnicowe i time-based, bez efektów ubocznych,
- `notification_history.py` — ograniczona historia i serializacja,
- `notifications.py` — orkiestracja, baseline, persistent notification, event bus i opcjonalny push,
- `config_flow.py` — Options Flow,
- `panel.py` — serializacja historii i agregatów panelu.

`notifications.py` nie może zawierać logiki porównawczej dla każdego typu; deleguje ją do `notification_rules.py`.

### Frontend

Nie rozbudowywać głównego `school-panel.js` o kolejne setki linii. Dalsze rozszerzenia 0.10.0 umieścić w osobnym module `school-panel-hub.js`, który importuje `school-panel-live.js` i rozszerza istniejący element.

Nowy moduł odpowiada za:
- `Pulpit`,
- `Aktywność`,
- `Powiadomienia`,
- badge w nawigacji,
- responsywny układ kart agregacyjnych.

`panel.py` rejestruje jako module URL najwyższy wrapper `school-panel-hub.js`.

## Dane i brak fikcji

Nie dodawać danych demo/fake do ścieżki produkcyjnej. Jeżeli pole nie jest dostępne LIVE, panel ma je pominąć lub pokazać neutralny brak danych.

`LuckyNumber` istnieje w modelu, ale nie jest obecnie zasilany przez builder. W 0.10.0 nie wolno pokazywać szczęśliwego numerka, dopóki rzeczywisty endpoint nie zostanie potwierdzony i zaimplementowany osobnym TDD.

## Bezpieczeństwo

Zachować i rozszerzyć obecną filtrację sekretów. Żadne powiadomienie, historia ani payload panelu nie może zawierać:
- hasła,
- cookies,
- tokenów,
- `session_key`, `mailbox_key`, `journal_key`,
- `globalKeySkrzynka`,
- `apiGlobalKey`,
- innych identyfikatorów routingu używanych do autoryzacji.

Identyfikatory publiczne wiadomości pozostają hashowane.

## Wydajność

- lokalny ticker panelu nie może generować nowych logowań,
- time-based notifications mają być oceniane przy update coordinatora oraz przez lekki lokalny timer tylko tam, gdzie jest to konieczne,
- nie tworzyć osobnego pollera portalu,
- deduplikacja alertów musi opierać się o stabilne signature/event_id i trwały Store.

## Testy i release

TDD RED→GREEN dla każdej grupy zachowań.

Przed merge wymagane:
- wszystkie testy Python GREEN,
- `node --check` dla `school-panel.js`, `school-panel-live.js`, `school-panel-hub.js`,
- Hassfest GREEN,
- HACS GREEN,
- spójność README/CHANGELOG/manifest.

Wersja docelowa: `0.10.0`.