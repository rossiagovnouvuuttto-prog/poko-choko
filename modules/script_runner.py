"""Генерация и запуск Python-скриптов в рантайме"""
import os
import subprocess
import sys
from datetime import datetime
from typing import Optional, Tuple
from config import SCRIPTS_DIR


class ScriptRunner:
    """Создаёт временный .py-файл и запускает его как отдельный процесс."""

    def __init__(self):
        os.makedirs(SCRIPTS_DIR, exist_ok=True)

    def save(self, code: str, name: Optional[str] = None) -> str:
        if not name:
            name = f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        path = os.path.join(SCRIPTS_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        return path

    def run(self, path: str, timeout: int = 60) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                [sys.executable, path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
            )
            if result.returncode == 0:
                return True, result.stdout
            return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Скрипт превысил таймаут"
        except Exception as e:
            return False, str(e)

    def execute_inline(self, code: str) -> Tuple[bool, str]:
        """Сохранить код и сразу его запустить."""
        return self.run(self.save(code))
