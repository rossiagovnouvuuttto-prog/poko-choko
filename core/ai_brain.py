"""
LLM-мозг ассистента на Mistral AI (через La Plateforme).
Прямой HTTP-запрос вместо SDK — меньше зависимостей и проблем с импортами.

Бесплатный тариф: 1 запрос/сек, 500K токенов/мин, 1 млрд токенов/мес.
Получить ключ: https://console.mistral.ai/
"""
import json
import re
import httpx
from typing import Optional, Dict, Any
from config import LLM_MODE, MISTRAL_MODEL, MISTRAL_API_KEY, ASSISTANT_NAME


SYSTEM_PROMPT = f"""Ты — {ASSISTANT_NAME}, голосовой ассистент пользователя на Windows 11.
Твоя задача — понять запрос и решить, какую системную функцию вызвать.

Доступные функции:
- open_app(name)              — открыть приложение (notepad, chrome, calc, mspaint и т.д.)
- create_folder(path)         — создать папку
- lock()                      — заблокировать ПК
- shutdown(seconds)           — выключить через N секунд
- cancel_shutdown()           — отменить выключение
- sleep_timer(minutes)        — таймер сна на N минут
- battery()                   — узнать заряд батареи
- cpu_load()                  — загрузка процессора
- google(query)               — поиск в Google
- youtube(query)              — поиск на YouTube
- open_url(url)               — открыть сайт
- minimize_window(title)      — свернуть окно
- activate_window(title)      — переключиться на окно
- close_window(title)         — закрыть окно
- speak(text)                 — просто ответить голосом, без действий
- random_anime()              — случайное аниме через Jikan API
- recommend_anime(genre)      — подобрать аниме по жанру (романтика, экшен, ужасы, фэнтези и т.п.)
- anime_edit(title)           — открыть первый обычный YouTube-ролик с эдитом/AMV по аниме

Отвечай СТРОГО одним JSON-объектом без пояснений и без markdown:
{{"function": "имя", "args": {{"ключ": "значение"}}, "reply": "что произнести"}}

Примеры:
"открой блокнот" → {{"function":"open_app","args":{{"name":"notepad"}},"reply":"Открываю блокнот."}}
"сколько будет 2+2" → {{"function":"speak","args":{{"text":"Четыре."}},"reply":"Четыре."}}
"найди где купить телефон за 10к" → {{"function":"google","args":{{"query":"купить смартфон до 10000 рублей"}},"reply":"Ищу смартфоны до 10 тысяч."}}
"открой что-нибудь для заметок" → {{"function":"open_app","args":{{"name":"notepad"}},"reply":"Открываю блокнот."}}
"таймер сна на 45 минут" → {{"function":"sleep_timer","args":{{"minutes":45}},"reply":"Таймер на 45 минут установлен."}}
"расскажи анекдот" → {{"function":"speak","args":{{"text":"Программист в магазине..."}},"reply":"Программист в магазине..."}}
"случайное аниме" → {{"function":"random_anime","args":{{}},"reply":"Подбираю случайное аниме."}}
"посоветуй аниме романтика" → {{"function":"recommend_anime","args":{{"genre":"романтика"}},"reply":"Подбираю романтическое аниме."}}
"посоветуй аниме экшен" → {{"function":"recommend_anime","args":{{"genre":"экшен"}},"reply":"Подбираю аниме в жанре экшен."}}
"эдит наруто" → {{"function":"anime_edit","args":{{"title":"Naruto"}},"reply":"Открываю эдит Naruto."}}
"найди эдит" → {{"function":"anime_edit","args":{{"title":""}},"reply":"Открываю эдит случайного аниме."}}
"""


API_URL = "https://api.mistral.ai/v1/chat/completions"


class GemmaBrain:  # Имя сохранено для совместимости с command_processor
    """Прямая обёртка над REST API Mistral."""

    def __init__(self):
        self.mode = LLM_MODE

        if self.mode == "off":
            print("[Brain] LLM-режим выключен в config.py")
            return

        if not MISTRAL_API_KEY:
            print("[Brain] MISTRAL_API_KEY не задан в .env — LLM выключен.")
            self.mode = "off"
            return

        print(f"[Brain] Подключён к {MISTRAL_MODEL} через Mistral AI (HTTP)")

    def think(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Получить решение модели для запроса."""
        if self.mode == "off":
            return None

        try:
            response = httpx.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MISTRAL_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
            return self._parse_json(text)
        except httpx.HTTPStatusError as e:
            print(f"[Brain] HTTP {e.response.status_code}: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"[Brain] Ошибка генерации: {e}")
            return None

    @staticmethod
    def _parse_json(text: str) -> Optional[Dict[str, Any]]:
        """Достать JSON из ответа модели."""
        if not text:
            return None
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
