# Поко Чоко — голосовой ассистент для Windows 11

Персональный ИИ-помощник на Python с интеграцией **Mistral AI** через бесплатный
API La Plateforme. Слушает голос или принимает текстовые команды, управляет
системой через PowerShell. Если штатный обработчик не понимает запрос —
передаёт его LLM-мозгу.

## Что внутри

- 🎤 Голосовой ввод (`SpeechRecognition` + Google Speech)
- 🔊 Голосовой вывод (`pyttsx3`, локальный Windows SAPI5 — работает оффлайн)
- 🪟 Управление системой через PowerShell (приложения, папки, питание, сон)
- 🧠 LLM-fallback на **Mistral Small** через прямой HTTP к La Plateforme
- 🖼️ Управление окнами, браузером, меню Пуск
- ⚡ Запуск Python-скриптов «на лету»
- 💎 Опциональный футуристичный GUI на CustomTkinter
- 💬 **Текстовый режим** `chat.py` — для тех, у кого не работает микрофон

## Установка

### 1. Python 3.10+

При установке поставь галочку «Add Python to PATH».

### 2. Распакуй проект и зайди в папку

```powershell
cd C:\путь\к\jarvis
```

### 3. Виртуальное окружение и зависимости

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Если на `pyaudio` будет ошибка компиляции:

```powershell
pip install pyaudio --only-binary :all:
```

> Если PowerShell ругается «выполнение скриптов отключено» при активации venv:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### 4. Mistral API ключ

1. Заходи на **https://console.mistral.ai/**, регистрируйся (нужно подтвердить телефон)
2. Слева в меню → **API Keys** → **Create new key**
3. Скопируй файл `.env.example` → `.env`:
   ```powershell
   copy .env.example .env
   ```
4. Открой `.env` в Блокноте и подставь ключ:
   ```
   MISTRAL_API_KEY=твой_ключ_сюда
   ```

Бесплатный тариф Mistral: **1 запрос в секунду, 1 млрд токенов в месяц**. Для
личного ассистента — с гигантским запасом.

> Если LLM не нужен — поставь в `config.py` параметр `LLM_MODE = "off"`,
> и ассистент будет работать только на жёстких командах (без интернета).

## Запуск

**Текстовый режим (рекомендуется для проверки):**

```powershell
python chat.py
```

**Голосовой режим:**

```powershell
python main.py
```

Скажи «Поко Чоко» → услышишь «Слушаю» → произнеси команду.

**С графическим интерфейсом:**

```powershell
python -m gui.main_window
```

## Примеры команд

**Жёсткие команды (быстро, без обращения к LLM):**

| Команда | Что делает |
|---|---|
| открой блокнот | `Start-Process notepad` |
| открой пуск | имитирует нажатие клавиши Win |
| создай папку C:\Users\дима\тест | `New-Item -ItemType Directory` |
| заблокируй | блокировка Windows |
| выключи компьютер | `shutdown /s /t 60` |
| отмени выключение | `shutdown /a` |
| таймер сна на 45 минут | спящий режим через 45 мин |
| какой заряд батареи | через `Get-CimInstance Win32_Battery` |
| загрузка процессора | через `Get-CimInstance Win32_Processor` |
| найди в гугле новости AI | Google поиск |
| ютуб смешные коты | YouTube поиск |
| открой сайт habr.com | в браузере по умолчанию |
| переключись на хром | активирует окно Chrome |
| сверни блокнот | сворачивает окно |
| закрой окно блокнот | закрывает окно |

**Размытые запросы (уходят в Mistral):**

```
сколько будет 47 умножить на 13
открой что-нибудь, чтобы записать заметку
найди где можно купить телефон мощный за 10к
переведи "спасибо" на японский
расскажи короткий анекдот
```

Mistral возвращает JSON с указанием функции и её аргументов, а Поко Чоко
исполняет это решение как обычную команду.

## Структура проекта

```
jarvis/
├── main.py                      # Голосовой режим
├── chat.py                      # Текстовый режим
├── config.py                    # Все настройки
├── requirements.txt
├── .env.example                 # Шаблон для MISTRAL_API_KEY
├── core/
│   ├── voice_input.py           # Распознавание речи
│   ├── voice_output.py          # Синтез речи через pyttsx3
│   ├── ai_brain.py              # Mistral AI через HTTP
│   └── command_processor.py     # Маршрутизация + LLM-fallback
├── modules/
│   ├── system_control.py        # PowerShell-обёртка
│   ├── window_manager.py        # Окна + браузер
│   └── script_runner.py         # Скрипты на лету
├── gui/
│   └── main_window.py           # Футуристичный GUI
└── generated_scripts/           # Сюда падают авто-сгенерированные скрипты
```

## Частые ошибки и решения

| Ошибка | Решение |
|---|---|
| `No module named 'distutils'` | `pip install setuptools` (уже в requirements) |
| `No module named 'pyaudio'` | `pip install pyaudio --only-binary :all:` |
| `[Brain] MISTRAL_API_KEY не задан` | проверь `.env` в корне проекта, без `.txt` |
| `HTTP 401` от Mistral | неверный или просроченный ключ, выпусти новый |
| `HTTP 429` от Mistral | превышен лимит 1 запрос/сек, подожди секунду |
| pyttsx3 говорит по-английски | Параметры → Время и язык → Речь → добавь «русский» |
| Микрофон молчит в голосовом режиме | Параметры → Конфиденциальность → Микрофон |

## Расширение

Добавить новую жёсткую команду — пиши обработчик в `core/command_processor.py`,
добавляй триггер в `self.commands`.

Чтобы Mistral знал про новую функцию — упомяни её в `SYSTEM_PROMPT` внутри
`core/ai_brain.py` и добавь в `self.llm_functions` соответствующее
сопоставление.

## Лицензия

Делай с кодом что угодно. Используешь Mistral — соблюдай их Terms of Service.
