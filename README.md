# codex-daily — aplikacja budowana krok po kroku przez Codexa

Od poniedziałku do soboty GitHub Actions losuje **1–3 kroki dziennie**.
Każdy krok przebiega tak:

```
ROADMAP.md (następny [ ] krok)
  → codex exec (subskrypcja ChatGPT Pro)
  → ruff + pytest (przy błędzie: jedna próba poprawki przez Codexa)
  → commit jako Ty → gałąź codex/… → Pull Request
  → ci.yml (lint + testy) → merge (rebase) → main
```

Niedziele są wolne. Po `END_DATE` automat sam przestaje działać.
Podgląd planu na miesiąc: `python scripts/daily_plan.py --preview 31`.

## Pliki

| Plik | Rola |
|---|---|
| `TOPIC.md` | **Ty uzupełniasz** — temat aplikacji |
| `ROADMAP.md` | Generuje Codex przy pierwszym przebiegu (60 kroków) |
| `AGENTS.md` | Zasady dla Codexa: jeden krok, testy, oszczędzanie kontekstu |
| `.codex/prompts/*.md` | Krótkie prompty (bootstrap i kolejny krok) |
| `scripts/daily_plan.py` | Losowanie 1–3 slotów dziennie, deterministycznie po dacie |
| `scripts/codex_step.sh` | Codex → lint/testy → ewentualna poprawka |
| `scripts/publish.sh` | Commit → PR → czekanie na CI → merge |
| `.github/workflows/codex-daily.yml` | Harmonogram (3 sloty, pn–sb) |
| `.github/workflows/ci.yml` | Testy na PR i na main |

## Konfiguracja (jednorazowo, ok. 15 min)

1. **Nowe prywatne repo** z gałęzią `main` → wrzuć te pliki, uzupełnij `TOPIC.md`.

2. **Auth Codexa z subskrypcji Pro.** Zaloguj się w osobnym katalogu, żeby CI miało
   własną sesję, niezależną od Twojego lokalnego Codexa:
   ```bash
   export CODEX_HOME=$(mktemp -d)
   codex login                       # logowanie kontem ChatGPT
   gh secret set CODEX_AUTH_JSON --repo TWÓJ_LOGIN/REPO < "$CODEX_HOME/auth.json"
   rm -rf "$CODEX_HOME"; unset CODEX_HOME
   ```
   Plik działa jak hasło. Trzymaj go tylko w prywatnym repo.

3. **Fine-grained PAT** (GitHub → Settings → Developer settings → Fine-grained tokens):
   ograniczony do tego jednego repo, z uprawnieniami *Contents: RW*, *Pull requests: RW*,
   *Secrets: RW*, *Actions: Read*. Zapisz go jako sekret `GH_PAT`.
   Do czego służy PAT:
   - PR-y zakłada Twoje konto, więc liczą się do Twojej aktywności,
   - PR utworzony PAT-em uruchamia `ci.yml` (PR od `GITHUB_TOKEN` tego nie robi),
   - workflow może zapisać odświeżony `auth.json` z powrotem do sekretu.
   Ustaw ważność tokenu na ≥ 35 dni.

4. **Variables** (Settings → Secrets and variables → Actions → Variables):
   - `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL` — e-mail przypięty do konta GitHub
     (np. `ID+login@users.noreply.github.com`),
   - `END_DATE` — np. `2026-11-30`,
   - opcjonalnie: `CODEX_EFFORT` (`low` / `medium`), `CODEX_MODEL`, `PLAN_SALT`.

5. **Profil → Contribution settings → Include private contributions on my profile.**

6. **Pierwszy przebieg ręcznie:** Actions → `codex-daily` → *Run workflow*.
   Codex utworzy ROADMAP i szkielet projektu. Przejrzyj ten PR — od niego zależy cała reszta.

## Oszczędzanie tokenów

- Prompt dzienny ma 2 zdania. Kontekst daje `AGENTS.md` (≈30 linii) i to, co potrzebne do kroku.
- ROADMAP jest zaplanowany z góry, więc Codex nie planuje od nowa przy każdym przebiegu.
- `docs/ARCHITECTURE.md` (max 40 linii) zastępuje przeglądanie całego repo.
- `--ephemeral` — bez wczytywania historii sesji.
- `model_reasoning_effort=medium` domyślnie. `low` jest tańsze, ale przy dłuższych krokach słabsze.
- Poprawka po nieudanych testach dostaje tylko ostatnie 60 linii logu, a próba jest jedna.
- Wynik: 1–3 małe zadania dziennie. To niewielki ułamek limitu Pro.

## Gdy coś pójdzie nie tak

- **`refresh_token_reused` / błąd logowania** — sekret ma nieaktualny `auth.json`.
  Powtórz krok 2 konfiguracji. Nie kopiuj do CI swojego codziennego `~/.codex/auth.json`:
  rotacja tokenów rozjedzie się między komputerem a CI.
- **CI czerwone na PR** — PR zostaje otwarty z komentarzem, a kolejny slot i tak spróbuje następnego kroku.
  Zajrzyj, popraw ręcznie albo zamknij PR i odznacz krok w ROADMAP.
- **Brak przebiegów** — `schedule` w Actions potrafi spóźnić się o kilkanaście minut.
  Po 60 dniach bez aktywności GitHub wyłącza harmonogram, ale tutaj każdy merge jest aktywnością.
- **Inne języki** (Rust/PyO3, Go, JS z buildem) wymagają dopisania toolchainu do obu workflowów.
  Bez tego trzymaj się Pythona + SQL (DuckDB/SQLite).
