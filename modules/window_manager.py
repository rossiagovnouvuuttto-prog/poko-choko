"""Управление окнами Windows и браузером по умолчанию"""
import webbrowser
from typing import List, Optional
import pygetwindow as gw


class WindowManager:
    """Операции над открытыми окнами по части заголовка."""

    @staticmethod
    def list_windows() -> List[str]:
        """Список всех видимых окон с непустым заголовком."""
        return [w.title for w in gw.getAllWindows() if w.title.strip()]

    @staticmethod
    def find(title_substring: str) -> Optional[gw.Win32Window]:
        """Найти первое окно, в заголовке которого есть подстрока."""
        for w in gw.getAllWindows():
            if title_substring.lower() in w.title.lower() and w.title.strip():
                return w
        return None

    @staticmethod
    def activate(title_substring: str) -> bool:
        """Развернуть окно и сделать активным."""
        win = WindowManager.find(title_substring)
        if not win:
            return False
        try:
            if win.isMinimized:
                win.restore()
            win.activate()
            return True
        except Exception as e:
            print(f"[WindowManager] activate error: {e}")
            return False

    @staticmethod
    def minimize(title_substring: str) -> bool:
        win = WindowManager.find(title_substring)
        if win:
            win.minimize()
            return True
        return False

    @staticmethod
    def close(title_substring: str) -> bool:
        win = WindowManager.find(title_substring)
        if win:
            win.close()
            return True
        return False


class BrowserControl:
    """Простое управление браузером по умолчанию."""

    @staticmethod
    def open_url(url: str) -> bool:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return webbrowser.open(url)

    @staticmethod
    def search_google(query: str) -> bool:
        q = query.replace(" ", "+")
        return BrowserControl.open_url(f"https://www.google.com/search?q={q}")

    @staticmethod
    def search_youtube(query: str) -> bool:
        q = query.replace(" ", "+")
        return BrowserControl.open_url(
            f"https://www.youtube.com/results?search_query={q}"
        )
