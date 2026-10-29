# LogLens

LogLens to projekt narzędzia do analizy logów Serilog w formacie CLEF / compact
JSON. Docelowo pakiet Pythona będzie strumieniowo wczytywać logi, analizować
błędy i czasy odpowiedzi w DuckDB/pandas oraz tworzyć raporty Markdown, HTML
i CSV. Generator przykładowych logów powstanie w C# (.NET 8).

Obecnie dostępny jest szkielet pakietu `loglens` z numerem wersji.
Plan rozwoju: [ROADMAP.md](ROADMAP.md).
Mapa kodu: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Instalacja i uruchomienie

Wymagany jest Python 3.12 lub nowszy. Z katalogu repozytorium:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -c 'import loglens; print(loglens.__version__)'
```

Na Windows aktywuj środowisko poleceniem `.venv\Scripts\Activate.ps1`
w PowerShell. Instalacja zależności wymaga indeksu pakietów lub lokalnie
przygotowanych pakietów.

## Sprawdzenie projektu

```bash
ruff check . --fix
pytest -q
```

Testy korzystają z `src/` przez konfigurację pytest, więc po zainstalowaniu
narzędzi można je uruchamiać bez instalacji samego pakietu.
CLI i generator .NET zostaną dodane w kolejnych krokach; testy Pythona
będą działać niezależnie od środowiska .NET.
