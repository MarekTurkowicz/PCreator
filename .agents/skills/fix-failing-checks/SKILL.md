---
name: fix-failing-checks
description: Minimalna naprawa nieprzechodzącego lintu (ruff), pytest lub dotnet test. Użyj, gdy prompt zawiera log błędu.
---

# Naprawa checków

1. Z logu wyciągnij plik i linię pierwszego błędu. Napraw tylko przyczynę, bez nowych funkcji.
2. Ruff: najpierw `ruff check . --fix`, potem ręcznie to, czego `--fix` nie ruszył.
   Nie wyłączaj reguł w `pyproject.toml` i nie dodawaj `# noqa` bez konkretnego powodu.
3. Pytest: uruchom tylko padający test `pytest -q <plik>::<test> -x`. Popraw kod,
   a test zmieniaj tylko wtedy, gdy jest ewidentnie błędny.
4. dotnet: czytaj tylko linie `error CS....`. Zwykłe przyczyny: brak `using`,
   zła nazwa namespace, brak `<PackageReference>` w `.csproj`.
5. Na końcu jedno pełne `ruff check . && pytest -q`. Nie zmieniaj plików w `.github/` i `scripts/`.
