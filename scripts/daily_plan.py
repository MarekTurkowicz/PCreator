#!/usr/bin/env python3
"""
Decyduje, czy bieżące uruchomienie workflowu ma zrobić krok aplikacji.

Workflow ma 3 sloty dziennie (pn–sb). Dla każdej daty deterministycznie
(ziarno = data + PLAN_SALT) losujemy N ∈ {1,2,3} i które N z 3 slotów
pracują. Bez stanu, bez bazy — każdy slot sam liczy ten sam plan.

Użycie:
  python scripts/daily_plan.py                # w Actions: pisze do GITHUB_OUTPUT
  python scripts/daily_plan.py --preview 31   # podgląd planu na 31 dni
"""

from __future__ import annotations

import os
import random
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Warsaw")

# Muszą się zgadzać z `on.schedule` w .github/workflows/codex-daily.yml
SLOTS = {
    "17 8 * * 1-6": 0,   # ~09:17 / 10:17 Warszawa
    "43 12 * * 1-6": 1,  # ~13:43 / 14:43
    "29 17 * * 1-6": 2,  # ~18:29 / 19:29
}
SLOT_LABELS = ["rano", "po południu", "wieczorem"]


def plan_for(d: date, salt: str) -> list[int]:
    """Zwraca listę slotów (0–2), w których tego dnia powstaje commit."""
    if d.weekday() == 6:  # niedziela
        return []
    rnd = random.Random(f"{salt}:{d.isoformat()}")
    n = rnd.randint(1, 3)
    return sorted(rnd.sample(range(3), n))


def write_output(**kv: str) -> None:
    path = os.getenv("GITHUB_OUTPUT")
    lines = [f"{k}={v}" for k, v in kv.items()]
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    print(" ".join(lines))


def main() -> int:
    salt = os.getenv("PLAN_SALT", "codex-daily")
    today = datetime.now(TZ).date()

    if "--preview" in sys.argv:
        days = int(sys.argv[sys.argv.index("--preview") + 1])
        total = 0
        for i in range(days):
            d = today + timedelta(days=i)
            slots = plan_for(d, salt)
            total += len(slots)
            desc = ", ".join(SLOT_LABELS[s] for s in slots) or "—"
            print(f"{d:%Y-%m-%d %a}  {len(slots)}  {desc}")
        print(f"Razem: {total} kroków w {days} dni")
        return 0

    event = os.getenv("EVENT_NAME", "")
    end = os.getenv("END_DATE", "").strip()
    if end and today > date.fromisoformat(end):
        write_output(run="false", reason="po-END_DATE")
        return 0

    if event != "schedule":  # workflow_dispatch → zawsze
        write_output(run="true", reason="manual")
        return 0

    slot = SLOTS.get(os.getenv("SCHEDULE", ""))
    if slot is None:
        write_output(run="false", reason="nieznany-slot")
        return 0

    slots = plan_for(today, salt)
    write_output(
        run="true" if slot in slots else "false",
        reason=f"dzis={len(slots)} slot={slot}",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
