# mojV Auth Helper

Ten komponent jest małym lokalnym pomocnikiem logowania dla integracji **mojV**.

Jego jedyne zadania to:

- uruchomić lokalny Chromium, gdy portal szkolny wymaga pełnej przeglądarki,
- utrzymać sesję przeglądarkową wewnątrz kontenera,
- zwrócić integracji mojV wyłącznie publiczne dane uczniów, plan i frekwencję.

Od wersji **0.1.2** Chromium działa z lokalnym wirtualnym ekranem Xvfb i klasycznym trybem headless. Helper zapisuje do logu wyłącznie bezpieczne etapy logowania i lokalizację strony bez parametrów zapytania.

Przy nieudanym logowaniu może powstać lokalny plik `/data/mojv_auth_error.png`. Przed wykonaniem zrzutu helper czyści wartości wszystkich pól formularza.

Helper **nie zapisuje hasła**, nie eksportuje cookies ani kluczy sesji i nie wystawia portu do sieci LAN. Komunikacja odbywa się wyłącznie w wewnętrznej sieci Home Assistant.

## Instalacja

1. Dodaj `https://github.com/gekon27/mojV` jako repozytorium aplikacji Home Assistant.
2. Zainstaluj lub zaktualizuj **mojV Auth Helper** do wersji 0.1.2 lub nowszej.
3. Uruchom aplikację i pozostaw `Uruchamiaj przy starcie` włączone.
4. W HACS zainstaluj lub zaktualizuj integrację mojV.
5. Dodaj konto szkolne w integracji mojV.

Nie ma żadnych opcji do konfiguracji w samym helperze.
