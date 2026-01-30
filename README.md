# finalproject_Evseenkova_Marina_M25-555
Итоговый проект. Платформа для отслеживания и симуляции торговли валютами.

В модуле valutatrade_hub/infra/settings.py подключается библиотека import toml. toml — это сторонняя библиотека для чтения .toml файлов (например, settings.toml). Python не включает её по умолчанию. 
Ее можно установить с помощью команды poetry add toml Это установит пакет toml и добавит его в pyproject.toml как зависимость.
Альтернатива - использовать встроенный модуль tomllib (Python 3.11+). tomllib - это аналог json, но для TOML.
Нужно заменить в valutatrade_hub/infra/settings.py:
Было: import toml
Стало: import tomllib  # Встроен в Python 3.11+
И при чтении файла.
Было:
with open(config_path, "r", encoding="utf-8") as f:
    config = toml.load(f)
Стало:
with open(config_path, "rb") as f:  # Важно: режим 'rb' для tomllib
    config = tomllib.load(f)