# valutatrade_hub/parser_service/storage.py

import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List

# ✅ Импортируем и config, и пути
from .config import HISTORY_FILE_PATH, RATES_FILE_PATH

# --- Устаревшие пути (можно удалить) ---
# Больше не используем os.path.join("..", "..", "data", ...)
# Заменяем на config-пути
# ----------------------------------------


# === Операции для exchange_rates.json (история) ===

def load_exchange_rates() -> List[Dict[str, Any]]:
    """Загрузить историю обновлений"""
    if not HISTORY_FILE_PATH.exists():
        return []
    try:
        with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ [Storage] Ошибка чтения {HISTORY_FILE_PATH.name}: {e}")
        return []


def save_exchange_rates(records: List[Dict[str, Any]]) -> bool:
    """Сохранить историю атомарно: temp file → rename"""
    try:
        temp_fd, temp_path = tempfile.mkstemp(suffix=".json", dir=tempfile.gettempdir(), text=True) # noqa: E501
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as tmp_file:
                json.dump(records, tmp_file, ensure_ascii=False, indent=4, default=str)
            # Атомарная замена
            os.replace(temp_path, HISTORY_FILE_PATH)
            print(f"💾 История курсов сохранена: {len(records)} записей")
            return True
        except Exception as e:
            os.close(temp_fd)
            os.unlink(temp_path)
            raise e
    except Exception as e:
        print(f"❌ [Storage] Ошибка записи {HISTORY_FILE_PATH.name}: {e}")
        return False


# === Операции для rates.json (актуальные курсы) ===

def save_rates_cache(rates: Dict[str, float]) -> None:
    """Сохранить плоский кэш для Core Service: 
    { "BTC": 59337.21, "last_updated": "..." }"""
    data = {
        code: rate for code, rate in rates.items()
    }
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    try:
        temp_fd, temp_path = tempfile.mkstemp(suffix=".json", dir=tempfile.gettempdir(), text=True) # noqa: E501
        with os.fdopen(temp_fd, "w", encoding="utf-8") as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False, indent=4, default=str)
        os.replace(temp_path, RATES_FILE_PATH)
        print(f"💾 Актуальные курсы сохранены в {RATES_FILE_PATH}")
    except Exception as e:
        print(f"❌ [Storage] Ошибка записи {RATES_FILE_PATH.name}: {e}")


def load_rates_snapshot() -> Dict[str, Any]:
    """Загрузить текущий снимок курсов"""
    if not RATES_FILE_PATH.exists():
        return {"pairs": {}, "last_refresh": None}
    try:
        with open(RATES_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"pairs": {}, "last_refresh": None}
            pairs = data.get("pairs", {})
            if not isinstance(pairs, dict):
                pairs = {}
            return {
                "pairs": pairs,
                "last_refresh": data.get("last_refresh")
            }
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ [Storage] Ошибка чтения {RATES_FILE_PATH.name}: {e}")
        return {"pairs": {}, "last_refresh": None}


def save_rates_snapshot(pairs: Dict[str, Dict], timestamp: str) -> bool:
    """Сохранить снимок курсов атомарно через временный файл"""
    try:
        # Создаём папку, если её нет
        RATES_FILE_PATH.parent.mkdir(exist_ok=True)

        # Временный файл
        temp_path = RATES_FILE_PATH.with_suffix(".json.tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump({
                "pairs": pairs,
                "last_updated": timestamp
            }, f, ensure_ascii=False, indent=2)

        # Атомарная замена — ключевой момент
        temp_path.replace(RATES_FILE_PATH)

        print(f"💾 [Storage] Успешно сохранено {len(pairs)} пар в {RATES_FILE_PATH.name}") # noqa: E501
        return True

    except Exception as e:
        print(f"❌ [Storage] Ошибка записи {RATES_FILE_PATH.name}: {e}")
        return False
