# Changelog

## [0.1.5] - 2026-09-03

- helper zapisuje przy starcie `mojV Auth Helper version=<wersja>`,
- numer wersji pochodzi z `MOJV_HELPER_VERSION`, czyli z dokładnie uruchomionego obrazu,
- log startowy nie zawiera loginu, hasła, cookies ani tokenów.

## [0.1.4] - 2026-09-03

- poprawiono przejście z dashboardu do dziennika: helper akceptuje poprawne przekierowanie na host ucznia bez wymagania ścieżki `/App/...`,
- tenant/miasto jest wykrywane z pierwszego segmentu ścieżki po przekierowaniu SSO,
- wolne ładowanie strony nadal jest izolowane per link, a diagnostyka błędu zawiera bezpieczną lokalizację bez query string i sekretów,
- zachowano obsługę 1..N dzieci i filtrowanie duplikatów.

## [0.1.3] - 2026-09-03

- timeout renderera podczas otwierania pojedynczego linku dziennika nie przerywa już całego logowania,
- helper próbuje zatrzymać niedokończone ładowanie przez `window.stop()` i sprawdza, czy aplikacja ucznia jest już dostępna,
- poprawnie zachowuje wcześniej wykryte konteksty i uczniów, nawet gdy kolejny link jest wolny lub uszkodzony,
- błędy Selenium są zamieniane na kontrolowany błąd helpera zamiast surowej odpowiedzi HTTP 500,
- diagnostyka loguje wyłącznie indeks linku, typ błędu i bezpieczną lokalizację bez sekretów.

## [0.1.2] - 2026-09-03

- uruchamianie Chromium z Xvfb i klasycznym `--headless`,
- dodane etapy diagnostyczne logowania bez zapisywania loginu, hasła, cookies ani query string,
- dodany lokalny screenshot błędu z wyczyszczonymi wartościami pól formularza,
- `/health` raportuje faktyczną wersję obrazu przez `MOJV_HELPER_VERSION`,
- CI sprawdza Xvfb, Chromium i zgodność wersji helpera.

## [0.1.1] - 2026-09-03

- helper jest publikowany jako gotowy wieloarchitekturowy obraz GHCR,
- Home Assistant pobiera obraz zamiast budować go lokalnie,
- obsługa `amd64` i `aarch64`,
- zweryfikowane anonimowe pobieranie obrazu bez tokenu GitHub.

## [0.1.0] - 2026-09-03

- pierwsza wersja lokalnego helpera Chromium dla mojV,
- wykrywanie 1..N dzieci w uwierzytelnionej sesji,
- pobieranie planu lekcji i frekwencji bez eksportowania cookies lub kluczy sesji,
- prywatne API dostępne wyłącznie w wewnętrznej sieci Home Assistant,
- cache sesji powiązany z fingerprintem loginu i hasła,
- brak zapisu hasła na dysku.
