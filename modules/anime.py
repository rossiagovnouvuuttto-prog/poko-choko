"""
Аниме-раздел: работа с Jikan API (https://docs.api.jikan.moe/).

Содержит чистые функции без побочных эффектов на GUI/голос:
- get_random_anime() — случайное аниме через /random/anime
- get_anime_by_genre(genre_name) — лучшее аниме по жанру (топ-10 по оценке)
- get_random_popular_anime_title() — название случайного аниме для эдитов
- build_anime_reply(anime) — собирает текст ответа на русском
"""
import random
from typing import Optional, Dict, Any

import httpx


JIKAN_BASE = "https://api.jikan.moe/v4"
HTTP_TIMEOUT = 15.0


# Жанры Jikan: русские варианты → ID жанра на MAL.
GENRE_MAP: Dict[str, int] = {
    "экшен": 1,
    "экшн": 1,
    "action": 1,
    "приключения": 2,
    "приключение": 2,
    "комедия": 4,
    "юмор": 4,
    "драма": 8,
    "фэнтези": 10,
    "фентези": 10,
    "fantasy": 10,
    "ужасы": 14,
    "ужас": 14,
    "horror": 14,
    "романтика": 22,
    "ромком": 22,
    "romance": 22,
    "фантастика": 24,
    "sci-fi": 24,
    "sci fi": 24,
    "научная фантастика": 24,
    "спорт": 30,
    "повседневность": 36,
    "slice of life": 36,
}


def _resolve_genre_id(genre_name: str) -> Optional[int]:
    """Найти ID жанра по русскому/английскому ключевому слову."""
    if not genre_name:
        return None
    key = genre_name.lower().strip()
    if key in GENRE_MAP:
        return GENRE_MAP[key]
    # Допускаем частичное совпадение: "посоветуй романтическое" → "романт"
    for alias, gid in GENRE_MAP.items():
        if alias in key or key in alias:
            return gid
    return None


def _http_get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Безопасный GET с возвратом JSON или None при любой ошибке."""
    try:
        response = httpx.get(url, params=params, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[Anime] HTTP error: {e}")
        return None


def get_random_anime() -> Optional[Dict[str, Any]]:
    """Случайное аниме через Jikan: GET /random/anime."""
    data = _http_get_json(f"{JIKAN_BASE}/random/anime")
    if not data:
        return None
    return data.get("data")


def get_anime_by_genre(genre_name: str) -> Optional[Dict[str, Any]]:
    """
    Получить топ-10 аниме по жанру (по оценке) и выбрать одно случайно,
    чтобы рекомендации не повторялись.
    """
    genre_id = _resolve_genre_id(genre_name)
    if genre_id is None:
        return None

    params = {
        "genres": genre_id,
        "order_by": "score",
        "sort": "desc",
        "limit": 10,
    }
    data = _http_get_json(f"{JIKAN_BASE}/anime", params=params)
    if not data:
        return None
    items = data.get("data") or []
    if not items:
        return None
    return random.choice(items)


def get_random_popular_anime_title() -> str:
    """
    Вернуть название случайного аниме для команды 'найди эдит' без названия.
    Берёт title_english, если есть, иначе title. Пустая строка — если API недоступен.
    """
    anime = get_random_anime()
    if not anime:
        return ""
    return (anime.get("title_english") or anime.get("title") or "").strip()


def build_anime_reply(anime: Optional[Dict[str, Any]]) -> str:
    """
    Собрать текст ответа ассистента на русском:
    - название аниме
    - оценка MAL (если есть)
    - краткое описание (если есть, обрезано)
    - ссылка на страницу MyAnimeList (если есть)
    """
    if not anime:
        return "Не удалось получить аниме. Попробуйте ещё раз."

    title = (
        anime.get("title_english")
        or anime.get("title")
        or anime.get("title_japanese")
        or "Без названия"
    )

    parts = [f"Аниме: {title}."]

    score = anime.get("score")
    if score:
        parts.append(f"Оценка MAL: {score}.")

    synopsis = anime.get("synopsis")
    if synopsis:
        # Краткое описание — первые ~300 символов, чтобы голосовой ответ
        # не превратился в монолог на пять минут.
        short = synopsis.strip().replace("\n", " ")
        if len(short) > 300:
            short = short[:300].rsplit(" ", 1)[0] + "..."
        parts.append(f"Описание: {short}")

    url = anime.get("url")
    if url:
        parts.append(f"Ссылка: {url}")

    return " ".join(parts)
