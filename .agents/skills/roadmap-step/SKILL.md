---
name: roadmap-step
description: Wykonanie jednego kroku z ROADMAP.md metodą test-first, z minimalnym zużyciem kontekstu. Użyj przy każdym zwykłym kroku.
---

# Jeden krok z ROADMAP.md

1. Znajdź pierwszy `- [ ]`: `rg -n -m1 '^- \[ \]' ROADMAP.md`. Nie czytaj całego pliku.
2. Przeczytaj `docs/ARCHITECTURE.md` i ustal 1–3 pliki do zmiany. Nic więcej nie otwieraj.
3. Napisz test w `tests/test_<moduł>.py` (lub w `dotnet/*.Tests/` dla C#), który opisuje
   nowe zachowanie. Dane testowe: małe pliki w `samples/` albo fixture w kodzie.
4. Zaimplementuj minimum, które przechodzi test. Bez refaktorów obok.
5. Uruchamiaj tylko testy, których dotyczy zmiana: `pytest -q tests/test_<moduł>.py -x`.
   Pełne `pytest -q` dopiero raz, na końcu.
6. Zaznacz krok `- [x]`, dopisz jedną linię w `docs/ARCHITECTURE.md`,
   zapisz commit message do `.commit_msg.txt`.

## Oszczędzanie kontekstu
- Szukaj `rg -n 'wzorzec' src/`, czytaj fragmenty `sed -n '40,90p' plik`.
- Nie wypisuj plików > 200 linii w całości. Nie uruchamiaj `ls -R`, `tree`, `cat` na katalogach.
- Długie wyjścia ucinaj: `pytest -q 2>&1 | tail -n 30`.
