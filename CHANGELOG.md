# Changelog

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
