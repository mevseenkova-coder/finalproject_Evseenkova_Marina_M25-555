# valutatrade_hub/infra/settings.py

import json
from pathlib import Path
from typing import Any, Dict

import toml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: str = "data"
    users_file: str = "data/users.json"
    portfolios_file: str = "data/portfolios.json"
    rates_file: str = "data/rates.json"

    class Config:
        env_file = ".env"

# Singleton SettingsLoader (конфигурация)

class SettingsLoader:
    """
    Singleton: единая точка доступа к конфигурации приложения.
    Поддерживает загрузку из:
      1. config.json (приоритет)
      2. pyproject.toml ([tool.valutatrade])
      3. значения по умолчанию
    """
    _instance = None

    def __new__(cls):
        # Паттерн Singleton через __new__
        # Просто, читаемо, безопасно при импортах
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if not self._loaded:
            self._settings: Dict[str, Any] = {}
            self._load_settings()
            self._loaded = True

    def _load_settings(self):
        """Загружает настройки из доступных источников."""
        # Определяем корень проекта — две папки вверх от __file__
        project_root = Path(__file__).parent.parent.parent  
        # valutatrade_hub → finalproject_...

        # Приоритет 1: config.json в корне
        config_path = project_root / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._settings = json.load(f)
            return

        # Приоритет 2: pyproject.toml
        toml_path = project_root / "pyproject.toml"
        if toml_path.exists():
            with open(toml_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
            tool_config = data.get("tool", {}).get("valutatrade", {})
            if tool_config:
                self._settings = tool_config
                return

        # Приоритет 3: значения по умолчанию
        self._settings = {
            "data_dir": str(project_root / "data"),
            "rates_ttl_seconds": 300,
            "base_currency": "USD",
            "log_level": "INFO",
            "log_file": str(project_root / "logs" / "app.log")
        }

    '''
    def _load_settings(self):
        """Загружает настройки из доступных источников."""
        # Приоритет 1: config.json
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                self._settings = json.load(f)
            return

        # Приоритет 2: pyproject.toml
        if os.path.exists("pyproject.toml"):
            with open("pyproject.toml", "r", encoding="utf-8") as f:
                data = toml.load(f)
            tool_config = data.get("tool", {}).get("valutatrade", {})
            if tool_config:
                self._settings = tool_config
                return

        # Приоритет 3: значения по умолчанию
        self._settings = {
            "data_dir": "data",
            "rates_ttl_seconds": 300,
            "base_currency": "USD",
            "log_level": "INFO",
            "log_file": "logs/app.log"
        }
    '''

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение по ключу.
        :param key: имя параметра (например, 'data_dir')
        :param default: значение по умолчанию
        :return: значение из конфига или default
        """
        return self._settings.get(key, default)

    def reload(self) -> None:
        """
        Перезагрузить конфигурацию.
        Полезно при динамическом обновлении настроек (например, в CLI-команде).
        """
        self._loaded = False
        self.__init__()  # перезапустит _load_settings

    def all(self) -> Dict[str, Any]:
        """Вернуть все настройки (для отладки)."""
        return self._settings.copy()

    def __repr__(self) -> str:
        return f"<SettingsLoader loaded={self._loaded}>"
