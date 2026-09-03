# mojV

![mojV](icon.svg)

Nieoficjalna integracja Home Assistant skoncentrowana na planie lekcji, bieżącej/następnej lekcji, frekwencji, ocenach, uwagach i automatyzacjach szkolnych.

## Status

**HACS 0.5.2 — LIVE + panel Szkoła + poprawiony pełny flow logowania.**

Wersja 0.5.2 rozwija rzeczywiste logowanie do portalu szkolnego, automatyczne wykrywanie **1..N dzieci** oraz pobieranie prawdziwego planu lekcji i frekwencji. Najważniejszą zmianą jest pełniejsze przejście procesu logowania: etap identyfikacji konta, przekazanie sesji do konkretnego dziennika, obsługa formularzy SSO oraz odpowiedzi API opakowanych w `data`.

W 0.5.2 diagnostyka wykrywania uczniów raportuje wyłącznie bezpieczne informacje techniczne: liczbę znalezionych linków, liczbę uruchomionych sesji dziennika, liczbę odpowiedzi kontekstu, liczbę rekordów oraz nazwy pól/kształt odpowiedzi. Login, hasło, cookies, klucze sesji i payloady SSO nie są logowane.

Logowanie jest realizowane lekką sesją HTTP wewnątrz integracji. Jeżeli dane konto otrzyma obowiązkową weryfikację wymagającą pełnej przeglądarki, Config Flow zgłosi to jednoznacznie zamiast zapisywać niedziałającą konfigurację.

## Panel „Szkoła”

Po załadowaniu integracji mojV automatycznie rejestruje pozycję **Szkoła** w lewym menu Home Assistant.

Panel 0.5.2 zawiera:

- zakładki do przełączania pomiędzy wykrytymi dziećmi,
- pełny plan lekcji poniedziałek–piątek,
- mocne wyróżnienie dzisiejszego dnia i aktualnej lekcji,
- aktualną i następną lekcję,
- numer lekcji, salę i nauczyciela,
- pierścień postępu lekcji oraz czas do końca,
- stan frekwencji przy każdej lekcji,
- alerty o nieobecności, spóźnieniu i zbliżającym się końcu lekcji,
- panel ostatnich ocen,
- panel ostatnich uwag,
- panel bieżących powiadomień,
- responsywny układ desktop / tablet / telefon,
- własny branding mojV.

Panel nie tworzy fikcyjnych modułów. Sekcje wymagające danych, których LIVE jeszcze nie pobiera, nie są udawane.

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
6. Podaj login/e-mail albo alias oraz hasło.
7. mojV sprawdzi logowanie i automatycznie wykryje wszystkie dzieci dostępne na koncie.

Po sukcesie wpis integracji będzie nazwany np. `mojV — 2 dzieci`, a panel **Szkoła** zacznie korzystać z rzeczywistych danych.

Tryb **Demo** można dodać osobno, jeśli potrzebny jest test bez połączenia z portalem.

## Aktualny zakres LIVE

W 0.5.2 podstawą pozostają dwa najważniejsze moduły:

- plan lekcji,
- frekwencja.

Oceny, uwagi, terminarz, wiadomości i kolejne funkcje są rozwijane na tej samej modularnej warstwie danych i będą dokładane po zweryfikowaniu rzeczywistego logowania i struktury danych na kontach użytkowników.

## Diagnostyka

Jeżeli logowanie albo integracja się nie załaduje:

1. Otwórz **Ustawienia → System → Dzienniki**.
2. Wyszukaj `mojv`.
3. Ponów próbę logowania.
4. Wróć do dziennika i skopiuj linie z `custom_components.mojv`.

Nie publikuj hasła ani cookies. Diagnostyka mojV nie zapisuje ich do logu.

## Instalacja ręczna

HACS instaluje katalog `custom_components/mojv` do katalogu konfiguracji Home Assistant. W używanym tutaj układzie będzie to:

`/homeassistant/custom_components/mojv`

## Branding

Od Home Assistant 2026.3 custom integrations mogą dostarczać branding lokalnie. mojV zawiera własny `custom_components/mojv/brand/icon.png`, więc ikona pojawia się bez osobnego repozytorium marek.

## Architektura

- `auth.py` — uwierzytelnienie, SSO i automatyczne wykrywanie dzieci,
- `school_api.py` — modułowe zapytania danych,
- `parsers/` — niezależne parsery odpowiedzi,
- `client.py` — scala dane w model mojV,
- `coordinator.py` — kontrolowane odświeżanie danych,
- `models.py` — wspólny model szkolny,
- `logic.py` — lokalna logika czasu lekcji i stanów panelu,
- `panel.py` — backend panelu i WebSocket,
- `frontend/school-panel.js` — panel **Szkoła**,
- `notifications.py` — alerty i eventy,
- `sensor.py`, `binary_sensor.py`, `calendar.py` — standardowe encje HA,
- `config_flow.py` — konfiguracja GUI,
- `diagnostics.py` — diagnostyka.

## Multi-student

Integracja nie zakłada dwóch dzieci na sztywno. Konto jest traktowane jako kolekcja **1..N uczniów**, a każde dziecko dostaje własne urządzenie, encje i plan.
