# mojV Auth Helper

Ten komponent jest małym lokalnym pomocnikiem logowania dla integracji **mojV**.

Jego zadania to:

- uruchomić lokalny Chromium, gdy portal szkolny wymaga pełnej przeglądarki,
- utrzymać sesję przeglądarkową wewnątrz kontenera,
- zwrócić integracji mojV wyłącznie publiczne dane uczniów: plan, frekwencję, oceny i terminarz/prace szkolne.

Helper nie jest wymagany dla każdego konta. mojV zawsze najpierw próbuje lekkiego logowania HTTP. Jeżeli konto wymaga pełnej przeglądarki, integracja automatycznie przełącza się na helper; użytkownik nie wybiera backendu ręcznie.

Od wersji **0.1.6** każdy moduł danych jest pobierany niezależnie. Problem z ocenami lub terminarzem nie powinien blokować planu i frekwencji. Identyfikatory routingu, klucze sesji, cookies i tokeny pozostają wewnątrz helpera.

Chromium działa z lokalnym wirtualnym ekranem Xvfb i klasycznym trybem headless. Helper zapisuje do logu wyłącznie bezpieczne etapy logowania i lokalizację strony bez parametrów zapytania.

Przy nieudanym logowaniu może powstać lokalny plik `/data/mojv_auth_error.png`. Przed wykonaniem zrzutu helper czyści wartości wszystkich pól formularza.

Helper **nie zapisuje hasła**, nie eksportuje cookies ani kluczy sesji i nie wystawia portu do sieci LAN. Komunikacja odbywa się wyłącznie w wewnętrznej sieci Home Assistant.

## Instalacja

1. Dodaj `https://github.com/gekon27/mojV` jako repozytorium aplikacji Home Assistant.
2. Zainstaluj lub zaktualizuj **mojV Auth Helper** do wersji **0.1.6** lub nowszej, jeżeli integracja zgłosi potrzebę pełnej przeglądarki.
3. Uruchom aplikację i pozostaw `Uruchamiaj przy starcie` włączone.
4. W HACS zainstaluj lub zaktualizuj integrację mojV.
5. Dodaj konto szkolne w integracji mojV.

Nie ma żadnych opcji do konfiguracji w samym helperze.
