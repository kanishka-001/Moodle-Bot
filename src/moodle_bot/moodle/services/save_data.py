from pathlib import Path
import json
from datetime import datetime, timezone
from moodle_bot.config import CACHE_DIR


def save_contents(name: int, payload: list[dict]) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = CACHE_DIR / f"{name}.json"

    with path.open("w", encoding="utf-8") as file:
        file.write(json.dumps(payload, indent=4, ensure_ascii=False))
    return path
