"""Управление окнами Windows и браузером по умолчанию"""
import re
import webbrowser
from typing import List, Optional
from urllib.parse import quote_plus

import httpx
import pygetwindow as gw


# Регулярка для обычных видео в результатах поиска YouTube.
# videoRenderer соответствует именно обычным роликам — Shorts
# выдаются как reelShelfRenderer/shortsLockupViewModel и сюда не попадают.
_YOUTUBE_VIDEO_ID_RE = re.compile(
    r'"videoRenderer"\s*:\s*\{\s*"videoId"\s*:\s*"([A-Za-z0-9_-]{11})"'
)

_YOUTUBE_SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def find_first_youtube_video_id(query: str) -> Optional[str]:
    """
    Найти videoId первого обычного видео в выдаче YouTube по запросу.

    Возвращает 11-символьный videoId или None, если не удалось.
    Shorts не считаются (они идут другим рендерером).
    """
    if not query or not query.strip():
        return None

    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    try:
        response = httpx.get(
            url,
            headers=_YOUTUBE_SEARCH_HEADERS,
            timeout=15.0,
            follow_redirects=True,
        )
        response.raise_for_status()
    except Exception as e:
        print(f"[YouTube] search error: {e}")
        return None

    match = _YOUTUBE_VIDEO_ID_RE.search(response.text)
    if not match:
        return None
    return match.group(1)


def open_first_youtube_video(query: str) -> bool:
    """
    Открыть первое обычное видео YouTube по запросу.

    Если найден videoId — открывается https://www.youtube.com/watch?v=...
    Если ничего не нашли — фолбэк на страницу поиска.
    Возвращает True, если открылась страница видео; False — если фолбэк
    или браузер не запустился.
    """
    if not query or not query.strip():
        return False

    video_id = find_first_youtube_video_id(query)
    if video_id:
        BrowserControl.open_url(f"https://www.youtube.com/watch?v={video_id}")
        return True

    # Видео не нашлось — отдаём страницу поиска, чтобы пользователь
    # хоть что-то увидел.
    BrowserControl.search_youtube(query)
    return False


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
