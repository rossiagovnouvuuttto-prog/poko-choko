"""
Поко Чоко — точка входа (голосовой режим).
Цикл: ждём кодовое слово -> слушаем команду -> выполняем.
"""
import sys
from core.voice_input import VoiceInput
from core.voice_output import VoiceOutput
from core.command_processor import CommandProcessor
from config import WAKE_WORDS, ASSISTANT_NAME, USER_NAME


def start_assistant_loop(log_callback=None):
    """Главный цикл. Можно вызывать из терминала и из GUI."""

    def log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    log(f"=== {ASSISTANT_NAME} запускается ===")
    voice_in = VoiceInput()
    voice_out = VoiceOutput()
    processor = CommandProcessor(voice_out)

    voice_out.speak(f"Система готова к работе, {USER_NAME}.")

    while True:
        try:
            log(f"[Ожидание] Скажите '{WAKE_WORDS[0]}'...")
            phrase = voice_in.listen(timeout=None, phrase_time_limit=4)

            if phrase and any(w in phrase for w in WAKE_WORDS):
                log(f"[Активация] Услышал: {phrase}")
                voice_out.speak("Слушаю.")

                command = voice_in.listen(timeout=5, phrase_time_limit=10)
                if command:
                    log(f"[Команда] {command}")
                    processor.process(command)
                else:
                    voice_out.speak("Команды не услышал.")

        except KeyboardInterrupt:
            voice_out.speak(f"До встречи, {USER_NAME}.")
            sys.exit(0)
        except Exception as e:
            log(f"[Ошибка] {e}")


if __name__ == "__main__":
    start_assistant_loop()
