# Changelog

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
