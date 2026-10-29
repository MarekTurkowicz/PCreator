# Zasady dla Codexa (czytaj w całości, jest krótki)

Projekt opisany w `TOPIC.md`. Plan pracy: `ROADMAP.md`. Mapa kodu: `docs/ARCHITECTURE.md`.

## Oszczędzaj kontekst
- Najpierw czytaj tylko `ROADMAP.md` i `docs/ARCHITECTURE.md`.
- Otwieraj wyłącznie pliki potrzebne do bieżącego kroku. Nie przeglądaj całego repo.
- Nie wypisuj długich podsumowań — końcowa odpowiedź max 8 linii.
- Szukaj przez `rg`, czytaj fragmenty (`sed -n 'a,bp'`), ucinaj długie wyjścia (`| tail -n 30`).
- Skille w `.agents/skills/`: `roadmap-step` (każdy krok), `fix-failing-checks`,
  `dotnet-serilog`, `duckdb-logs`. Używaj ich, gdy pasują.

## Jeden krok = jedna mała, działająca zmiana
- Realizuj DOKŁADNIE jeden krok z ROADMAP.md. Nic ponad to, bez refaktorów „przy okazji”.
- Typowy rozmiar: 40–250 linii nowego kodu + testy.
- Każdy krok dodaje nową funkcjonalność i co najmniej jeden test w `tests/`.
- Po kroku: zaznacz go w ROADMAP.md (`- [x]`) i zaktualizuj `docs/ARCHITECTURE.md`
  (max 40 linii: moduł → jedno zdanie).

## Środowisko
- Python 3.12, pakiet w `src/`, testy `pytest`, lint `ruff`.
- Brak internetu w sandboxie. Nowe zależności dopisz do `pyproject.toml`
  (CI je zainstaluje), ale nie zakładaj, że są już dostępne w tym przebiegu —
  testy nowego kodu z nową zależnością oznacz `pytest.importorskip`.
- C# / .NET 8: kod w `dotnet/`, rozwiązanie `dotnet/LogLens.sln`, testy xUnit.
  Pakiety NuGet (Serilog, xUnit) dopisuj do `.csproj` — restore i `dotnet test`
  uruchomi skrypt poza sandboxem. Jeśli `dotnet build` u Ciebie nie przejdzie
  z braku sieci, nie obchodź tego; pilnuj poprawności kodu. Nie commituj `bin/`, `obj/`.
- SQL wykonuj przez Pythona (DuckDB).
- Nie zmieniaj `.github/`, `scripts/`, `AGENTS.md`, `.codex/prompts/`, `.agents/`.

## Zakończenie
- Uruchom `ruff check . --fix` i `pytest -q`; jeśli istnieje `dotnet/LogLens.sln`,
  także `dotnet test dotnet/LogLens.sln`. Napraw błędy.
- Zapisz jednolinijkowy komunikat commita (Conventional Commits, po angielsku,
  max 72 znaki) do `.codex/out/commit_msg.txt`.
