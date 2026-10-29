#!/usr/bin/env bash
# Commit (jako Ty) → push gałęzi → PR → czekanie na CI → merge (rebase, żeby autor commita został Twój).
# Wymaga: GH_TOKEN (fine-grained PAT), GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, GITHUB_REPOSITORY.
set -euo pipefail

MSG="$(head -n1 .codex/out/commit_msg.txt 2>/dev/null | cut -c1-72 || true)"
[[ -n "$MSG" ]] || MSG="feat: next roadmap step"
BR="codex/$(date -u +%Y%m%d-%H%M%S)"

git config user.name  "$GIT_AUTHOR_NAME"
git config user.email "$GIT_AUTHOR_EMAIL"
git remote set-url origin "https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"

git switch -c "$BR"
git add -A
git commit -q -m "$MSG"
git push -q -u origin "$BR"

BODY="$(sed -n '1,40p' .codex/out/last.md 2>/dev/null || true)"
gh pr create --base main --head "$BR" --title "$MSG" --body "${BODY:-Automatyczny krok z ROADMAP.md}"

# Czekamy na run ci.yml dla tej gałęzi przez API Actions
# (`gh pr checks` wymaga uprawnienia Commit statuses, którego PAT nie ma).
SHA="$(git rev-parse HEAD)"
RUN_ID=""
for _ in $(seq 1 30); do
  RUN_ID="$(gh run list --workflow ci.yml --branch "$BR" --event pull_request \
            --json databaseId,headSha --jq ".[] | select(.headSha==\"$SHA\") | .databaseId" | head -n1)"
  [[ -n "$RUN_ID" ]] && break
  sleep 10
done
if [[ -z "$RUN_ID" ]] || ! gh run watch "$RUN_ID" --exit-status --interval 20 > /dev/null; then
  gh pr comment "$BR" --body "CI nie przeszło — PR zostaje otwarty do ręcznej poprawki."
  exit 1
fi

gh pr merge "$BR" --rebase --delete-branch
echo "Zmergowano: $MSG"
