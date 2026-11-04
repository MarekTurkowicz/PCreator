"""Find supported log files before reading their events."""

from pathlib import Path


def find_log_files(directory: str | Path) -> list[Path]:
    """Return immediate .clef/.json files sorted by case-sensitive filename.

    Extensions are matched case-insensitively. Subdirectories are excluded;
    missing or non-directory inputs propagate filesystem errors.
    """
    return sorted(
        (
            path
            for path in Path(directory).iterdir()
            if path.suffix.lower() in {".clef", ".json"} and path.is_file()
        ),
        key=lambda path: path.name,
    )
