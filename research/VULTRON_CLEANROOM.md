# Vultron → mojV: clean-room research

Ten branch służy do analizy rozwiązań projektu `htomasz/vultron` bez kopiowania jego implementacji do kodu MIT mojV.

## Zasada licencyjna

Projekt źródłowy jest GPL-3.0, podczas gdy mojV jest MIT. Do `main` przenosimy wyłącznie własną implementację zachowań i protokołów zaobserwowanych w działającym projekcie. Nie kopiujemy kodu, kart JS ani automatyzacji linia-po-linii.

## Architektura, którą warto zachować

1. Jedno logowanie rodzica → automatyczne wykrycie 1..N uczniów.
2. Etap uwierzytelnienia oddzielony od późniejszych zapytań HTTP.
3. Dane każdego ucznia pobierane niezależnie.
4. Niezależne moduły danych pobierane współbieżnie.
5. Pamięć poprzednio widzianych wpisów, aby nowe oceny/uwagi/wiadomości generowały alert tylko raz.
6. Plan pobierany dla szerszego okna niż bieżący dzień — poprzedni, bieżący i następny tydzień.
7. Ograniczone odpytywanie zewnętrznego portalu; lokalna logika czasu lekcji działa bez dodatkowych requestów.

## Zaobserwowane moduły danych

### Priorytet P0

- Plan zajęć — endpoint `PlanZajec`, zakres dat.
- Frekwencja — endpoint `Frekwencja`, dodatkowo `Przedmioty` i `FrekwencjaStatystyki`.
- Okresy klasyfikacyjne — `OkresyKlasyfikacyjne`.
- Oceny — `Oceny` dla identyfikatora okresu klasyfikacyjnego.
- Uwagi — `Uwagi`.

### Priorytet P1

- Sprawdziany i zadania — `SprawdzianyZadaniaDomowe`.
- Wiadomości — osobna część sesji/serwisu; do zbadania po stabilizacji P0.
- Oceny proponowane i końcowe.

### Priorytet P2

- Frekwencja per przedmiot i statystyki.
- Osiągnięcia — `Osiagniecia`.
- Zebrania.
- Szczęśliwy numerek.

## Docelowe mapowanie do mojV

- `SchoolAccount` — konto rodzica i kontekst sesji.
- `Student` — stabilny identyfikator ucznia, nazwa, klasa.
- `Lesson` — czas, przedmiot, sala, nauczyciel, zmiana/odwołanie, status obecności.
- `Grade` — ocena cząstkowa + opis + data + okres.
- `FinalGrade` — proponowana/końcowa.
- `Remark` — uwaga/pochwała/informacja.
- `SchoolWork` — sprawdzian, kartkówka, zadanie domowe i termin.
- `Message` — nadawca, temat, data, status odczytania, treść.
- `AttendanceSummary` — statystyki ogólne i per przedmiot.
- `Achievement`, `Meeting`, `LuckyNumber` — późniejsze moduły.

## Różnice względem Vultron

mojV nie będzie publikował dużych JSON-ów jako atrybutów pojedynczych sensorów. Dane pozostają w coordinatorze/backendzie panelu, a sensory HA pokazują tylko najważniejsze stany. Panel „Szkoła” korzysta z własnego WebSocket API.

mojV nie będzie monolitem. Transport, parsowanie i modele danych będą oddzielone:

```text
transport/
  session.py
  portal.py
parsers/
  timetable.py
  attendance.py
  grades.py
  remarks.py
  schoolwork.py
models.py
coordinator.py
panel.py
notifications.py
```

## Alerty

- spóźnienie,
- nieobecność,
- nowa ocena,
- zmiana oceny,
- nowa uwaga,
- nowy sprawdzian/zadanie,
- wiadomość,
- 5 minut do końca lekcji,
- zmiana/odwołanie lekcji.

Każdy alert ma stabilną sygnaturę i deduplikację w storage Home Assistant.
