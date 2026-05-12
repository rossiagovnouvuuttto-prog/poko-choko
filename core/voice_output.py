"""
Синтез речи через pyttsx3.
Версия с очередью — все TTS-запросы исполняются в одном выделенном
потоке, что устраняет зависания SAPI5 при многопоточном использовании.
"""
import threading
import queue
import pyttsx3
from config import ASSISTANT_NAME, TTS_RATE, TTS_VOLUME


def _find_russian_voice(engine):
    """Вернуть id русского голоса, если есть в системе."""
    for voice in engine.getProperty("voices"):
        name = (voice.name or "").lower()
        if "russian" in name or "русск" in name \
                or "irina" in name or "pavel" in name:
            return voice.id
    return None


class VoiceOutput:
    """
    Озвучивание через выделенный TTS-поток.

    Внешне выглядит как раньше: voice.speak("текст") блокирует вызов
    до конца озвучки. Внутри — текст уходит в очередь, отдельный
    поток инициализирует свежий движок pyttsx3, произносит фразу и
    сигналит событием, что готово.

    Это решает две проблемы:
    1. pyttsx3.runAndWait() капризен при вызове из разных потоков;
    2. Свежий engine для каждой фразы предотвращает редкие
       зависания после нескольких озвучек подряд.
    """

    def __init__(self):
        self._queue: "queue.Queue[tuple[str, threading.Event]]" = queue.Queue()
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._worker.start()

    def speak(self, text: str) -> None:
        """Произнести фразу. Блокирует до конца озвучки."""
        if not text:
            return
        print(f"[{ASSISTANT_NAME}] {text}")
        done = threading.Event()
        self._queue.put((text, done))
        # Ждём, пока TTS-поток закончит. Таймаут как страховка
        # от подвисаний — лучше тихо отпустить, чем заморозить весь GUI.
        done.wait(timeout=30)

    def _loop(self):
        """Основной цикл TTS-потока."""
        while not self._stop.is_set():
            try:
                text, done = self._queue.get()
            except Exception:
                continue

            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", TTS_RATE)
                engine.setProperty("volume", TTS_VOLUME)
                voice_id = _find_russian_voice(engine)
                if voice_id:
                    engine.setProperty("voice", voice_id)
                engine.say(text)
                engine.runAndWait()
                try:
                    engine.stop()
                except Exception:
                    pass
                del engine
            except Exception as e:
                print(f"[VoiceOutput] {e}")
            finally:
                done.set()
