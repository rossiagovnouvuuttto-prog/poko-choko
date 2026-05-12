"""Глобальная конфигурация ассистента"""
import os
from dotenv import load_dotenv

load_dotenv()  # Подгружает переменные из .env

# === Активация ===
# Список вариантов, как Google может расслышать кодовое слово.
# Срабатывание происходит при совпадении ЛЮБОГО варианта.
WAKE_WORDS = ["поко чоко", "пока чоко", "поко чока", "пока чока", "пуко чоко"]
WAKE_WORD = WAKE_WORDS[0]
ASSISTANT_NAME = "Поко Чоко"
USER_NAME = "Сэр"

# === TTS (pyttsx3, локальный Windows SAPI5) ===
# Если стоят русские голоса (Irina, Pavel), они выберутся автоматически.
TTS_RATE = 180          # скорость речи
TTS_VOLUME = 1.0        # громкость 0.0..1.0

# === Распознавание речи ===
LANGUAGE = "ru-RU"
ENERGY_THRESHOLD = 300
PAUSE_THRESHOLD = 0.8
USE_WHISPER = False
WHISPER_MODEL = "base"  # tiny | base | small | medium | large

# === LLM (Mistral AI через La Plateforme) ===
# 'api' — Mistral AI (бесплатно, рекомендуется)
# 'off' — отключить, использовать только жёсткие команды
LLM_MODE = "api"

# Доступные модели на free tier:
#   mistral-small-latest   — быстрый, для маршрутизации команд (рекомендуется)
#   mistral-medium-latest  — умнее, но медленнее
#   mistral-large-latest   — самый умный, тратит больше токенов
MISTRAL_MODEL = "mistral-small-latest"
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

# === Пути ===
SCRIPTS_DIR = "generated_scripts"
LOG_FILE = "jarvis.log"
