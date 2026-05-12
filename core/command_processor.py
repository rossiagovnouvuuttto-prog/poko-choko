"""
Обработчик голосовых/текстовых команд.

Гибридная логика с фолбэками:
1. Сначала жёсткие триггеры (быстро, офлайн).
2. Если жёсткая команда не справилась с конкретным аргументом — Mistral.
3. Если триггеров не нашлось вообще — тоже Mistral.
4. Если LLM выключен — извинение.
"""
import re
import threading
import pyautogui
from modules.system_control import (
    open_application, create_folder, lock_workstation,
    shutdown, cancel_shutdown, sleep_after,
    get_battery_percent, get_cpu_load,
)
from modules.window_manager import WindowManager, BrowserControl
from modules.script_runner import ScriptRunner
from core.ai_brain import GemmaBrain


# Псевдонимы для частых приложений
APP_ALIASES = {
    "блокнот": "notepad",
    "калькулятор": "calc",
    "браузер": "msedge",
    "хром": "chrome",
    "проводник": "explorer",
    "терминал": "wt",
    "настройки": "ms-settings:",
    "диспетчер задач": "taskmgr",
    "командная строка": "cmd",
    "пейнт": "mspaint",
    "paint": "mspaint",
    "ворд": "winword",
    "эксель": "excel",
}


class CommandProcessor:
    """Главный диспетчер команд."""

    def __init__(self, voice_output):
        self.voice = voice_output
        self.scripts = ScriptRunner()
        self.brain = GemmaBrain()
        self._last_command = ""

        # Жёсткие команды (более специфичные триггеры — выше)
        self.commands = [
            (["отмени выключение"], self._cancel_shutdown),
            (["выключи компьютер"], self._shutdown),
            (["таймер сна", "режим сна"], self._sleep_timer),
            (["заблокируй", "блокировка"], self._lock),
            (["создай папку"], self._create_folder),
            (["найди в гугле", "поиск гугл"], self._google),
            (["ютуб", "видео"], self._youtube),
            (["открой сайт"], self._open_url),
            (["открой пуск", "меню пуск"], self._open_start_menu),
            (["открой", "запусти"], self._open_app),
            (["сверни"], self._minimize),
            (["переключись на", "активируй окно"], self._activate),
            (["закрой окно"], self._close_window),
            (["батарея", "заряд"], self._battery),
            (["загрузка процессора", "загрузка цп"], self._cpu),
        ]

        # Карта функций для исполнения решений LLM
        self.llm_functions = {
            "open_app":         lambda args: self._open_app_direct(args.get("name", "")),
            "create_folder":    lambda args: self._create_folder(args.get("path", "")),
            "lock":             lambda args: self._lock(""),
            "shutdown":         lambda args: shutdown(args.get("seconds", 60)),
            "cancel_shutdown":  lambda args: self._cancel_shutdown(""),
            "sleep_timer":      lambda args: self._sleep_timer(str(args.get("minutes", 30))),
            "battery":          lambda args: self._battery(""),
            "cpu_load":         lambda args: self._cpu(""),
            "google":           lambda args: self._google(args.get("query", "")),
            "youtube":          lambda args: self._youtube(args.get("query", "")),
            "open_url":         lambda args: self._open_url(args.get("url", "")),
            "minimize_window":  lambda args: self._minimize(args.get("title", "")),
            "activate_window":  lambda args: self._activate(args.get("title", "")),
            "close_window":     lambda args: self._close_window(args.get("title", "")),
            "speak":            lambda args: self.voice.speak(args.get("text", "")),
        }

    # === Главная точка входа ===

    def process(self, command: str) -> None:
        if not command:
            return
        cmd = command.lower().strip()
        self._last_command = cmd
        print(f"[Команда] {cmd}")

        # Шаг 1: жёсткие триггеры
        for triggers, handler in self.commands:
            for trigger in triggers:
                if trigger in cmd:
                    arg = cmd.replace(trigger, "").strip()
                    handler(arg)
                    return

        # Шаг 2: триггеров не нашлось — спросим Mistral
        if not self._llm_fallback():
            self.voice.speak("Команда не распознана.")

    def _llm_fallback(self) -> bool:
        """Спросить Mistral. Возвращает True, если она что-то решила."""
        if self.brain.mode == "off":
            return False
        decision = self.brain.think(self._last_command)
        if decision:
            self._execute_llm_decision(decision)
            return True
        return False

    def _execute_llm_decision(self, decision: dict) -> None:
        """Исполнить решение, которое вернула модель."""
        func_name = decision.get("function", "speak")
        args = decision.get("args", {}) or {}
        reply = decision.get("reply", "")

        handler = self.llm_functions.get(func_name)
        if not handler:
            self.voice.speak(reply or "Не знаю такой функции.")
            return

        try:
            handler(args)
            if reply and func_name != "speak":
                self.voice.speak(reply)
        except Exception as e:
            print(f"[CommandProcessor] Ошибка LLM-функции: {e}")
            self.voice.speak("Не удалось выполнить.")

    # === Обработчики жёстких команд ===

    def _open_start_menu(self, _arg: str):
        """Открыть меню Пуск через нажатие клавиши Win."""
        try:
            pyautogui.press("win")
            self.voice.speak("Открываю меню Пуск.")
        except Exception as e:
            print(f"[OpenStart] {e}")
            self.voice.speak("Не удалось открыть Пуск.")

    def _open_app(self, arg: str):
        """Открыть по триггеру. При неудаче — спросим Mistral."""
        if not arg:
            self.voice.speak("Что именно открыть?")
            return
        target = APP_ALIASES.get(arg, arg)
        ok, _ = open_application(target)
        if ok:
            self.voice.speak(f"Открываю {arg}.")
        else:
            # Жёсткая команда не справилась — может, это размытое описание
            if not self._llm_fallback():
                self.voice.speak(f"Не удалось открыть {arg}.")

    def _open_app_direct(self, name: str):
        """Прямой вызов из LLM — без рекурсии в фолбэк."""
        if not name:
            self.voice.speak("LLM не указал, что открыть.")
            return
        target = APP_ALIASES.get(name.lower(), name)
        ok, _ = open_application(target)
        if not ok:
            self.voice.speak(f"Не удалось открыть {name}.")

    def _open_url(self, arg: str):
        if not arg:
            self.voice.speak("Какой сайт открыть?")
            return
        BrowserControl.open_url(arg.replace(" ", ""))
        self.voice.speak(f"Открываю {arg}.")

    def _create_folder(self, arg: str):
        if not arg:
            self.voice.speak("Укажите имя папки.")
            return
        ok, _ = create_folder(arg)
        self.voice.speak("Папка создана." if ok else "Не удалось создать папку.")

    def _lock(self, _arg: str):
        self.voice.speak("Блокирую систему.")
        lock_workstation()

    def _shutdown(self, _arg: str):
        self.voice.speak(
            "Компьютер выключится через минуту. "
            "Скажите 'отмени выключение' для отмены."
        )
        shutdown(60)

    def _cancel_shutdown(self, _arg: str):
        ok, _ = cancel_shutdown()
        self.voice.speak(
            "Выключение отменено." if ok else "Активного таймера выключения нет."
        )

    def _sleep_timer(self, arg: str):
        m = re.search(r"(\d+)", arg)
        minutes = int(m.group(1)) if m else 30
        self.voice.speak(f"Таймер сна установлен на {minutes} минут.")
        threading.Thread(target=sleep_after, args=(minutes,), daemon=True).start()

    def _battery(self, _arg: str):
        ok, out = get_battery_percent()
        if ok and out:
            self.voice.speak(f"Уровень заряда: {out} процентов.")
        else:
            self.voice.speak("Не удалось получить заряд батареи.")

    def _cpu(self, _arg: str):
        ok, out = get_cpu_load()
        if ok and out:
            self.voice.speak(f"Загрузка процессора: {out} процентов.")
        else:
            self.voice.speak("Не удалось получить загрузку процессора.")

    def _google(self, arg: str):
        if not arg:
            self.voice.speak("Что найти?")
            return
        BrowserControl.search_google(arg)
        self.voice.speak(f"Ищу: {arg}")

    def _youtube(self, arg: str):
        if not arg:
            self.voice.speak("Что найти на ютубе?")
            return
        BrowserControl.search_youtube(arg)
        self.voice.speak(f"Ищу на YouTube: {arg}")

    def _minimize(self, arg: str):
        if WindowManager.minimize(arg):
            self.voice.speak("Сворачиваю.")
        else:
            if not self._llm_fallback():
                self.voice.speak("Окно не найдено.")

    def _activate(self, arg: str):
        if WindowManager.activate(arg):
            self.voice.speak(f"Переключаюсь на {arg}.")
        else:
            if not self._llm_fallback():
                self.voice.speak("Окно не найдено.")

    def _close_window(self, arg: str):
        if WindowManager.close(arg):
            self.voice.speak(f"Закрыл {arg}.")
        else:
            if not self._llm_fallback():
                self.voice.speak("Окно не найдено.")
