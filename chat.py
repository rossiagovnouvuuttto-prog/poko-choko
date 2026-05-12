"""
Поко Чоко — текстовый режим.
Вместо голоса — пишешь команды с клавиатуры. Ответ произносится вслух.

Запуск:  python chat.py
Выход:   'выход' / 'quit' / Ctrl+C
"""
from core.voice_output import VoiceOutput
from core.command_processor import CommandProcessor
from config import ASSISTANT_NAME, USER_NAME


def main():
    print(f"=== {ASSISTANT_NAME} (текстовый режим) ===")

    voice_out = VoiceOutput()
    processor = CommandProcessor(voice_out)

    voice_out.speak(f"Система готова к работе, {USER_NAME}.")
    print("\nПиши команды. Для выхода — 'выход', 'quit' или Ctrl+C.\n")

    while True:
        try:
            command = input("Ты> ").strip()
            if not command:
                continue
            if command.lower() in ("выход", "exit", "quit"):
                voice_out.speak(f"До встречи, {USER_NAME}.")
                break
            processor.process(command)
        except (KeyboardInterrupt, EOFError):
            print()
            voice_out.speak(f"До встречи, {USER_NAME}.")
            break
        except Exception as e:
            print(f"[Ошибка] {e}")


if __name__ == "__main__":
    main()
