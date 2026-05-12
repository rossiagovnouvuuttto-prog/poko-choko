"""Модуль распознавания речи"""
import speech_recognition as sr
from config import (
    LANGUAGE, ENERGY_THRESHOLD, PAUSE_THRESHOLD,
    USE_WHISPER, WHISPER_MODEL,
)


class VoiceInput:
    """Слушает микрофон и возвращает распознанный текст."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = ENERGY_THRESHOLD
        self.recognizer.pause_threshold = PAUSE_THRESHOLD
        self.microphone = sr.Microphone()

        # Калибровка под фоновый шум при старте
        with self.microphone as source:
            print("[VoiceInput] Калибровка микрофона...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        # Опциональная загрузка локального Whisper
        self.whisper_model = None
        if USE_WHISPER:
            import whisper
            print(f"[VoiceInput] Загружаю модель Whisper '{WHISPER_MODEL}'...")
            self.whisper_model = whisper.load_model(WHISPER_MODEL)

    def listen(self, timeout=None, phrase_time_limit=10):
        """
        Слушает одну фразу.
        :param timeout: сколько ждать начала речи (None — бесконечно)
        :param phrase_time_limit: максимальная длина фразы
        :return: строка в нижнем регистре или None
        """
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            # Маршрут 1: локальный Whisper
            if self.whisper_model:
                import tempfile, os
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio.get_wav_data())
                    tmp = f.name
                result = self.whisper_model.transcribe(tmp, language="ru")
                os.unlink(tmp)
                return result["text"].strip().lower()

            # Маршрут 2: Google Speech (бесплатный, требует интернет)
            return self.recognizer.recognize_google(audio, language=LANGUAGE).lower()

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[VoiceInput] Ошибка сервиса распознавания: {e}")
            return None
