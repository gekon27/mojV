# mojV 0.9.0 — LIVE modules

## Scope

Add real portal data for remarks, messages, achievements, parent meetings and extended attendance statistics while preserving HTTP-first authentication, automatic browser-helper fallback and 1..N students.

## Contracts derived from public API behaviour

- student API: `/api/Uwagi`
- student API: `/api/Osiagniecia`
- student API: `/api/Zebrania`
- attendance: `/api/Przedmioty` + `/api/FrekwencjaStatystyki?idPrzedmiot=...`
- messages: separate message tenant with `/api/OdebraneSkrzynka` and `/api/WiadomoscSzczegoly`
- mailbox routing key comes from student context and remains internal

Reference code is GPL-3.0 and is not copied. mojV uses independently written transports, parsers, models and UI.

## Order

1. RED parser/API/auth/message contracts.
2. GREEN pure parsers and model extensions.
3. GREEN concurrent direct HTTP fetch with per-module failure isolation.
4. Extend snapshot builder, client and panel serialization.
5. Extend standalone browser helper to the same snapshot contract and publish 0.1.8 multi-arch.
6. Add dynamic panel views only for data actually returned.
7. Release helper first, then HACS 0.9.0 after full CI.

## Security

No passwords, cookies, session keys, mailbox keys, routing identifiers or request query strings are exposed in public snapshots or logs. No fake LIVE records are generated when a module is empty or unavailable.
