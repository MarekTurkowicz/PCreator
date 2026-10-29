# Mapa kodu

- `src/loglens/__init__.py` → publiczny pakiet `loglens` i jego wersja.
- `src/loglens/models.py` → model `LogEvent` z wartościami domyślnymi, kontekstem i lokalizacją źródłową, sprawdzany w `tests/test_models.py`.
- `src/loglens/clef.py` → odczyt pól `@t`, `@l`, `@mt` i `@m` z pojedynczej linii JSON do `LogEvent`, testowany w `tests/test_clef.py` na próbce `samples/basic.clef`.
- `src/loglens/clef.py::parse_line` → normalizuje czas do UTC (także daty bez strefy), zachowuje brak czasu i odrzuca błędne daty; testy obejmują offsety i zmianę dnia.
- `pyproject.toml` → metadane pakietu w `src/`, extra `dev` oraz konfiguracja pytest i ruff.
- `tests/test_smoke.py` → test importu pakietu i zgodności wersji z metadanymi.
- `README.md` → opis projektu oraz instrukcje instalacji, uruchomienia i sprawdzeń.
- `ROADMAP.md` → uporządkowany plan 60 małych zmian wraz z testami.
- `TOPIC.md` → zakres docelowych analiz CLEF, generatora .NET i raportów.
