# Changelog

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
