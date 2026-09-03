# mojV Auth Helper

Ten komponent jest małym lokalnym pomocnikiem logowania dla integracji **mojV**.

Jego jedyne zadania to:

- uruchomić lokalny Chromium, gdy portal szkolny wymaga pełnej przeglądarki,
- utrzymać sesję przeglądarkową wewnątrz kontenera,
- zwrócić integracji mojV wyłącznie publiczne dane uczniów, plan i frekwencję.

Helper **nie zapisuje hasła**, nie eksportuje cookies ani kluczy sesji i nie wystawia portu do sieci LAN. Komunikacja odbywa się wyłącznie w wewnętrznej sieci Home Assistant.

## Instalacja

1. Dodaj `https://github.com/gekon27/mojV` jako repozytorium aplikacji Home Assistant.
2. Zainstaluj **mojV Auth Helper**.
3. Uruchom aplikację i pozostaw `Uruchamiaj przy starcie` włączone.
4. W HACS zainstaluj lub zaktualizuj integrację mojV.
5. Dodaj konto szkolne w integracji mojV.

Nie ma żadnych opcji do konfiguracji w samym helperze.
