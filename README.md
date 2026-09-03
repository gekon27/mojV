# mojV

![mojV](icon.svg)

Nieoficjalna integracja Home Assistant skoncentrowana na planie lekcji, bieżącej/następnej lekcji, frekwencji, ocenach, uwagach i automatyzacjach szkolnych.

## Status

**HACS 0.4.0 — pierwszy build LIVE.**

Wersja 0.4.0 dodaje rzeczywiste logowanie do portalu szkolnego, automatyczne wykrywanie **1..N dzieci** oraz pobieranie prawdziwego planu lekcji i frekwencji. Tryb demonstracyjny nadal jest dostępny do diagnostyki UI.

Logowanie jest realizowane lekką sesją HTTP wewnątrz integracji. Jeżeli dane konto otrzyma obowiązkową weryfikację wymagającą pełnej przeglądarki, Config Flow zgłosi to jednoznacznie zamiast zapisywać niedziałającą konfigurację.

## Panel „Szkoła”

Po załadowaniu integracji mojV automatycznie rejestruje pozycję **Szkoła** w lewym menu Home Assistant.

Panel jest responsywny i dla każdego wykrytego dziecka pokazuje:

- pełny plan lekcji poniedziałek–piątek,
- wyróżnienie dzisiejszego dnia i aktualnej lekcji,
- aktualną i następną lekcję,
- numer lekcji, salę, nauczyciela i czas do końca,
- stan frekwencji przy lekcjach,
- alert o spóźnieniu,
- alert o nieobecności,
- alert o końcu lekcji w ciągu 5 minut,
- miejsce na oceny i uwagi.

Przy dwóch dzieciach plany są niezależne i układają się responsywnie na komputerze i telefonie.

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

## Instalacja / aktualizacja przez HACS

1. Dodaj `https://github.com/gekon27/mojV` jako **Integration** w Custom repositories, jeżeli repo nie jest jeszcze dodane.
2. W HACS wybierz `mojV` → **Redownload / Update**.
3. Uruchom ponownie Home Assistant.
4. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację → mojV**.
5. Wybierz **Konto szkolne**.
6. Podaj login/e-mail i hasło.
7. mojV sprawdzi logowanie i automatycznie wykryje wszystkie dzieci dostępne na koncie.

Po sukcesie wpis integracji będzie nazwany np. `mojV — 2 dzieci`, a panel **Szkoła** zacznie korzystać z rzeczywistych danych.

Tryb **Demo** można dodać osobno, jeśli potrzebny jest test bez połączenia z portalem.

## Pierwszy zakres LIVE

W 0.4.0 celowo uruchamiane są najpierw dwa najważniejsze moduły:

- plan lekcji,
- frekwencja.

Oceny, uwagi, terminarz, wiadomości i kolejne funkcje są rozwijane na tej samej modularnej warstwie danych i będą dokładane po zweryfikowaniu rzeczywistego logowania i struktury danych.

## Diagnostyka

Jeżeli logowanie albo integracja się nie załaduje:

1. Otwórz **Ustawienia → System → Dzienniki**.
2. Wyszukaj `mojv`.
3. Na stronie integracji wybierz **Pobierz diagnostykę**.

Nie publikuj hasła ani cookies. Diagnostyka mojV usuwa pola poufne przed eksportem.

## Instalacja ręczna

HACS instaluje katalog `custom_components/mojv` do katalogu konfiguracji Home Assistant. W używanym tutaj układzie będzie to:

`/homeassistant/custom_components/mojv`

## Branding

Od Home Assistant 2026.3 custom integrations mogą dostarczać branding lokalnie. mojV zawiera własny `custom_components/mojv/brand/icon.png`, więc ikona pojawia się bez osobnego repozytorium marek.

## Architektura

- `auth.py` — uwierzytelnienie i automatyczne wykrywanie dzieci,
- `school_api.py` — modułowe zapytania danych,
- `parsers/` — niezależne parsery odpowiedzi,
- `client.py` — scala dane w model mojV,
- `coordinator.py` — kontrolowane odświeżanie danych,
- `models.py` — wspólny model szkolny,
- `logic.py` — lokalna logika czasu lekcji,
- `panel.py` — backend panelu i WebSocket,
- `frontend/school-panel.js` — panel **Szkoła**,
- `notifications.py` — alerty i eventy,
- `sensor.py`, `binary_sensor.py`, `calendar.py` — standardowe encje HA,
- `config_flow.py` — konfiguracja GUI,
- `diagnostics.py` — diagnostyka.

## Multi-student

Integracja nie zakłada dwóch dzieci na sztywno. Konto jest traktowane jako kolekcja **1..N uczniów**, a każdy dostaje własne urządzenie, encje i plan.
