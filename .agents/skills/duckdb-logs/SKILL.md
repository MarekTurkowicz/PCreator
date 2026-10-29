---
name: duckdb-logs
description: Wczytywanie logów CLEF do DuckDB/pandas i analizy SQL w pakiecie loglens. Użyj przy krokach z parsowaniem, agregacjami, raportami.
---

# Analiza logów w Pythonie

- Czytanie: strumieniowo, linia po linii (`json.loads`), z licznikiem błędnych linii zamiast wyjątku.
  Duże katalogi: DuckDB `read_json_auto('logs/*.clef', format='newline_delimited')`.
- Normalizacja kolumn: `@t`→`timestamp` (UTC), `@l`→`level` (domyślnie `Information`),
  `@mt`→`template`, `@x`→`exception`. Reszta właściwości zostaje jako kolumny.
- SQL trzymaj w `src/loglens/sql/*.sql`, ładuj przez `importlib.resources`. Parametry przez `?`,
  nigdy przez f-stringi.
- Grupowanie wyjątków: odcisk = typ wyjątku + pierwsza ramka stosu bez numerów linii.
- Testy: małe pliki w `samples/` (< 200 KB), asercje na konkretnych liczbach.
- CLI w Typer: komendy cienkie, logika w funkcjach testowanych bez CLI.
