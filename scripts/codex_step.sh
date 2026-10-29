#!/usr/bin/env bash
# Jeden krok aplikacji: Codex → lint/testy → (ew. jedna poprawka) → gotowe do commita.
# Nie dotyka gita zdalnego i nie widzi tokenów GitHuba.
set -euo pipefail

mkdir -p .codex/out
if [[ -f ROADMAP.md ]]; then PROMPT_FILE=.codex/prompts/step.md; else PROMPT_FILE=.codex/prompts/bootstrap.md; fi

codex_run() {
  local args=(exec --sandbox workspace-write --ephemeral
              -c "model_reasoning_effort=\"${CODEX_EFFORT:-medium}\""
              -o .codex/out/last.md)
  [[ -n "${CODEX_MODEL:-}" ]] && args+=(-m "$CODEX_MODEL")
  codex "${args[@]}" "$1"
}

install_deps() {
  if [[ -f pyproject.toml ]]; then
    pip install -q -e ".[dev]" || pip install -q -e .
  fi
}

check() {
  # łańcuch &&, bo w `if ! check` bash wyłącza set -e wewnątrz funkcji
  # kod 5 z pytest = brak testów (np. tuż po bootstrapie) — traktujemy jako OK
  install_deps && ruff check . && { pytest -q || [[ $? -eq 5 ]]; } && check_dotnet
}

check_dotnet() {
  [[ -f dotnet/LogLens.sln ]] || return 0
  dotnet test dotnet/LogLens.sln --nologo -v q
}

echo "::group::Codex ($PROMPT_FILE)"
codex_run "$(cat "$PROMPT_FILE")"
echo "::endgroup::"

if ! check > .codex/out/check.log 2>&1; then
  echo "Testy/lint nie przeszły — jedna próba poprawki."
  tail -n 40 .codex/out/check.log
  codex_run "Lint lub testy nie przechodzą po ostatniej zmianie. Użyj skilla fix-failing-checks. Napraw minimalnie, bez nowych funkcji. Końcówka logu:
$(tail -n 60 .codex/out/check.log)"
  check > .codex/out/check.log 2>&1 || { cat .codex/out/check.log; exit 1; }
fi
tail -n 5 .codex/out/check.log

if git diff --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
  echo "Codex nie wprowadził zmian." >&2
  exit 1
fi
