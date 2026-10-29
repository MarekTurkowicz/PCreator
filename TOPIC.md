# Temat aplikacji

**Nazwa robocza:** LogLens: analiza logów Serilog (.NET) w Pythonie

**Co robi (2–4 zdania):**
Mała aplikacja w C# (.NET 8) generuje realistyczne, ustrukturyzowane logi Serilog
w formacie JSON (CLEF / compact JSON): żądania HTTP, czasy odpowiedzi, błędy z wyjątkami,
poziomy logowania, właściwości kontekstu. Pakiet Pythona `loglens` wczytuje te logi
(również duże pliki, strumieniowo), normalizuje je do DuckDB/pandas i daje CLI do analizy:
statystyki błędów, percentyle czasów odpowiedzi, grupowanie podobnych wyjątków,
wykrywanie anomalii w czasie oraz raporty (Markdown/HTML/CSV).

**Dla kogo / scenariusz użycia:**
Developer albo osoba z on-call w zespole .NET, która dostaje katalog plików `.clef`/`.json`
z produkcji i chce w minutę odpowiedzieć na pytania: co się zepsuło, od kiedy, jak często,
które endpointy zwalniają. Użycie: `loglens report logs/ --since 2h --out raport.md`.

**Stos:**
- Python 3.12: Typer (CLI), pandas, DuckDB (SQL na logach), pytest, ruff.
- C# / .NET 8: Serilog + Serilog.Formatting.Compact (generator logów), xUnit (testy).

**Inne języki współpracujące z Pythonem:**
- C# w katalogu `dotnet/` z plikiem `dotnet/LogLens.sln`. Część .NET tworzy przykładowe
  logi (CLI `generate --count N --error-rate 0.05 --seed 42`) i ma własne testy xUnit.
- SQL (DuckDB) do agregacji. Zapytania w plikach `.sql` w pakiecie Pythona.
- Kontrakt między językami: format CLEF. Przykładowe pliki w `samples/` (małe, < 200 KB)
  są wspólnym zbiorem testowym dla Pythona i C#.

**Czego NIE robić:**
- Bez frontendu webowego i bez zewnętrznych API wymagających kluczy.
- Testy Pythona nie mogą wymagać uruchomienia .NET. Korzystają z plików w `samples/`.
- Bez dużych plików w repo (wygenerowane logi > 200 KB nie trafiają do gita).
