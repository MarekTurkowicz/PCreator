# Mapa kodu

- `src/loglens/cli.py::inspect` → strumieniowo liczy poprawne i błędne zdarzenia w plikach katalogu; testy w `tests/test_cli.py` obejmują mieszane dane, pusty katalog oraz błędy ścieżki i kodowania.
- `src/loglens/cli.py` → aplikacja Typer z poleceniem `loglens version` i punktem wejścia w `pyproject.toml`; wyjście i kod zakończenia sprawdza `tests/test_cli.py`.
- `src/loglens/clef.py::read_files` → leniwie odczytuje kolejne pliki w kolejności wejścia, zachowując źródła i numery linii oraz tryb obsługi błędów; testy dwóch próbek i przypadków brzegowych w `tests/test_reader.py`.
- `src/loglens/discovery.py::find_log_files` → zwraca posortowane według nazw pliki `.clef` i `.json` bez podkatalogów, ignorując wielkość liter rozszerzeń; testy w `tests/test_discovery.py` obejmują też puste katalogi i błędne ścieżki.
- `src/loglens/__init__.py` → publiczny pakiet `loglens` i jego wersja.
- `src/loglens/models.py` → model `LogEvent` z wartościami domyślnymi, kontekstem i lokalizacją źródłową, sprawdzany w `tests/test_models.py`.
- `src/loglens/clef.py` → odczyt pól `@t`, `@l`, `@mt` i `@m` z pojedynczej linii JSON do `LogEvent`, testowany w `tests/test_clef.py` na próbce `samples/basic.clef`.
- `src/loglens/clef.py::parse_line` → normalizuje czas do UTC (także daty bez strefy), zachowuje brak czasu i odrzuca błędne daty; testy obejmują offsety i zmianę dnia.
- `src/loglens/clef.py::_normalize_level` → normalizuje sześć poziomów Serilog bez rozróżniania wielkości liter, domyślnie używa `Information` przy braku `@l` i odrzuca nieznane wartości; testy w `tests/test_clef.py`.
- `src/loglens/clef.py::parse_line` → zachowuje wyjątek `@x` i zagnieżdżony kontekst, pomija metadane CLEF i odkodowuje nazwy `@@`; testy w `tests/test_clef.py`.
- `src/loglens/clef.py::read_file` → czyta plik UTF-8 leniwie, przypisując zdarzeniom ścieżkę źródła i numer linii od 1; testy w `tests/test_reader.py`.
- `src/loglens/clef.py::read_file(strict=False)` → pomija błędne linie z ostrzeżeniem zawierającym ścieżkę, numer linii i przyczynę; domyślny tryb ścisły i błędy plików nadal zgłaszają wyjątki, co sprawdza `tests/test_reader.py`.
- `pyproject.toml` → metadane pakietu w `src/`, extra `dev` oraz konfiguracja pytest i ruff.
- `tests/test_smoke.py` → test importu pakietu i zgodności wersji z metadanymi.
- `README.md` → opis projektu oraz instrukcje instalacji, uruchomienia i sprawdzeń.
- `ROADMAP.md` → uporządkowany plan 60 małych zmian wraz z testami.
- `TOPIC.md` → zakres docelowych analiz CLEF, generatora .NET i raportów.
