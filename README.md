# mojV

Nieoficjalna integracja Home Assistant skoncentrowana na planie lekcji, bieżącej/następnej lekcji, frekwencji, ocenach, uwagach i automatyzacjach szkolnych.

## Status

**Wersja testowa HACS 0.3.0.**

Aktualny build służy do sprawdzenia instalacji przez HACS i całej architektury Home Assistant. Zawiera deterministyczny tryb demo obsługujący **1..N dzieci** (domyślnie 2). Warstwa danych rzeczywistych zostanie dołączona do istniejącego klienta bez przebudowy encji, panelu ani multi-student.

## Panel „Szkoła”

Po załadowaniu integracji mojV automatycznie rejestruje pozycję **Szkoła** w lewym menu Home Assistant.

Panel jest responsywny i dla każdego dziecka pokazuje:

- pełny plan lekcji na dziś,
- aktualną i następną lekcję,
- numer lekcji, salę, nauczyciela i czas do końca,
- obecność przy każdej lekcji,
- alert o spóźnieniu,
- alert o nieobecności,
- alert o końcu lekcji w ciągu 5 minut,
- ostatnie oceny,
- ostatnie uwagi.

Przy dwóch dzieciach plany są pokazane jako dwa niezależne panele na szerokim ekranie i jeden pod drugim na telefonie.

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

mojV tworzy Persistent Notification w Home Assistant i publikuje zdarzenia event bus:

- `mojv_lesson_late` — spóźnienie,
- `mojv_lesson_absent` — nieobecność,
- `mojv_new_grade` — nowa ocena,
- `mojv_new_remark` — nowa uwaga.

Zdarzenia można później podpiąć bezpośrednio do automatyzacji `notify.mobile_app_*`, komunikatora, głośnika albo innego kanału powiadomień.

Integracja zapamiętuje już obsłużone oceny i uwagi w storage HA. W trybie rzeczywistym pierwszy start nie ma generować lawiny powiadomień o starych wpisach.

## Instalacja przez HACS

1. W HACS otwórz menu z trzema kropkami.
2. Wybierz **Custom repositories / Niestandardowe repozytoria**.
3. Dodaj `https://github.com/gekon27/mojV`.
4. Typ repozytorium: **Integration**.
5. Zainstaluj lub zaktualizuj `mojV`.
6. Uruchom ponownie Home Assistant.
7. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację**.
8. Wyszukaj `mojV`.
9. W teście pozostaw `Liczba dzieci = 2`.

## Oczekiwany wynik testu dla 2 dzieci

Powstaną dwa urządzenia:

- `Dziecko 1`,
- `Dziecko 2`.

W danych demo:

- Dziecko 1 ma bieżącą nieobecność,
- Dziecko 2 ma bieżące spóźnienie,
- każde ma przykładową ocenę,
- każde ma przykładową uwagę,
- bieżąca lekcja kończy się w ciągu kilku minut,
- po lewej stronie pojawia się panel **Szkoła**.

Pozwala to przetestować UI, encje i mechanizm alertów bez danych rzeczywistych.

## Diagnostyka

Jeżeli integracja się nie załaduje:

1. Otwórz **Ustawienia → System → Dzienniki**.
2. Wyszukaj `mojv`.
3. Na stronie integracji wybierz **Pobierz diagnostykę** i zachowaj plik.

Diagnostyka mojV usuwa pola poufne przed eksportem.

## Instalacja ręczna

HACS instaluje katalog `custom_components/mojv` do katalogu konfiguracji Home Assistant. Przy układzie używanym w tym projekcie będzie to:

`/homeassistant/custom_components/mojv`

## Architektura

- `client.py` — źródło danych,
- `coordinator.py` — `DataUpdateCoordinator`,
- `models.py` — uczniowie, lekcje, oceny i uwagi,
- `logic.py` — logika czasu lekcji,
- `panel.py` — backend panelu i WebSocket,
- `frontend/school-panel.js` — panel „Szkoła”,
- `notifications.py` — alerty i eventy,
- `sensor.py`, `binary_sensor.py`, `calendar.py` — standardowe encje HA,
- `config_flow.py` — konfiguracja GUI,
- `diagnostics.py` — diagnostyka.

## Multi-student

Integracja nie zakłada dwóch dzieci na sztywno. Dane są przetwarzane jako kolekcja uczniów i mogą obsłużyć 1..N rekordów.
