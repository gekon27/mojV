# mojV

Nieoficjalna integracja Home Assistant dla mojV. Projekt koncentruje się na planie lekcji, bieżącej/następnej lekcji, frekwencji oraz automatyzacjach związanych z końcem zajęć.

## Status

**Wersja testowa HACS 0.2.0.**

Aktualny build służy do sprawdzenia instalacji przez HACS i całej architektury Home Assistant. Zawiera deterministyczny tryb demo obsługujący **1..N dzieci** (domyślnie 2). Logowanie live do mojV zostanie dołączone jako osobna warstwa klienta; nie trzeba będzie przebudowywać encji ani dashboardu.

## Funkcje dostępne w teście

Dla każdego dziecka integracja tworzy osobne urządzenie Home Assistant oraz:

- `sensor` — aktualna lekcja,
- `sensor` — następna lekcja,
- `sensor` — numer lekcji,
- `sensor` — minuty do końca,
- `sensor` — obecność,
- `sensor` — plan dnia,
- `sensor` — ostatnia synchronizacja,
- `binary_sensor` — czy trwa lekcja,
- `calendar` — plan lekcji.

Dodatkowo powstaje wspólny sensor liczby wykrytych uczniów.

## Instalacja testowa przez HACS

1. W HACS otwórz menu z trzema kropkami.
2. Wybierz **Custom repositories / Niestandardowe repozytoria**.
3. Dodaj:

   `https://github.com/gekon27/mojV`

4. Typ repozytorium: **Integration**.
5. Zainstaluj `mojV`.
6. Uruchom ponownie Home Assistant.
7. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację**.
8. Wyszukaj `mojV`.
9. Pozostaw `Liczba dzieci = 2` i zakończ konfigurację.

## Oczekiwany wynik dla 2 dzieci

W Home Assistant powinny powstać dwa urządzenia:

- `Dziecko 1`,
- `Dziecko 2`.

Każde powinno mieć własny zestaw encji. Bezpośrednio po dodaniu integracji pierwsza lekcja jest ustawiana jako trwająca, a licznik minut do końca zmniejsza się wraz z czasem. Drugie dziecko ma lekko przesunięty plan, co pozwala sprawdzić niezależność danych.

## Diagnostyka

Jeżeli integracja się nie załaduje:

1. Otwórz **Ustawienia → System → Dzienniki**.
2. Wyszukaj `mojv`.
3. Na stronie integracji wybierz **Pobierz diagnostykę** i zachowaj plik.

Diagnostyka mojV jest przygotowana tak, aby przed udostępnieniem usuwać przyszłe pola poufne, takie jak hasło, token, cookies czy klucz sesji.

## Instalacja ręczna

HACS instaluje katalog:

`custom_components/mojv`

Do katalogu konfiguracji Home Assistant. Przy układzie używanym przez autora projektu będzie to:

`/homeassistant/custom_components/mojv`

## Architektura

- `client.py` — źródło danych (obecnie demo; później eduVULCAN),
- `coordinator.py` — jeden `DataUpdateCoordinator` dla całego konta rodzica,
- `models.py` — model konta, ucznia i lekcji,
- `logic.py` — czysta logika aktualnej/następnej lekcji,
- `sensor.py` — sensory,
- `binary_sensor.py` — stan „trwa lekcja”,
- `calendar.py` — kalendarze dzieci,
- `config_flow.py` — konfiguracja przez GUI,
- `diagnostics.py` — bezpieczna diagnostyka.

## Multi-student

Integracja nie zakłada dwóch dzieci na sztywno. Dane są przetwarzane jako kolekcja uczniów i mogą obsłużyć 1..N rekordów. W trybie testowym formularz pozwala ustawić od 1 do 8 symulowanych dzieci.

## Ważne

To projekt nieoficjalny i nie jest powiązany z firmą VULCAN. Obecny test nie wykonuje żadnych zapytań do mojV.
