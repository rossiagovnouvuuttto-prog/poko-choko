"""
Чат-GUI для Поко Чоко.
Окно с историей сообщений, поле ввода, кнопка микрофона,
индикатор статуса.

Все обновления интерфейса проходят через self.after() — это
обязательно для tkinter, иначе обработка из фоновых потоков
ломает виджеты и вешает кнопки в промежуточных состояниях.

Запуск:  python -m gui.chat_window
"""
import threading
from datetime import datetime
import customtkinter as ctk
from core.voice_output import VoiceOutput
from core.voice_input import VoiceInput
from core.command_processor import CommandProcessor
from config import ASSISTANT_NAME, USER_NAME

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# === Цветовая палитра в стиле HUD ===
BG_DARK = "#0a0e27"
BG_PANEL = "#0f1535"
BG_INPUT = "#1a2148"
ACCENT = "#00d4ff"
ACCENT_HOVER = "#00a3cc"
TEXT_MAIN = "#e0f7ff"
TEXT_MUTED = "#7a8db5"
USER_BUBBLE = "#1e3a5f"
BOT_BUBBLE = "#0a2540"


class GuiVoiceOutput:
    """
    Обёртка над VoiceOutput: помимо озвучки, добавляет реплику в чат.
    GUI-обновление обязательно через .after() — иначе ломает tkinter.
    """

    def __init__(self, real_voice: VoiceOutput, gui_window):
        self.real = real_voice
        self.gui = gui_window

    def speak(self, text: str) -> None:
        # Запрос на добавление сообщения — на главный поток
        self.gui.after(0, lambda t=text: self.gui._add_bot_message(t))
        # Сама озвучка блокирующая, но потокобезопасная
        self.real.speak(text)


class ChatGUI(ctk.CTk):
    """Главное окно чата."""

    def __init__(self):
        super().__init__()
        self.title(f"{ASSISTANT_NAME} — Чат")
        self.geometry("780x680")
        self.minsize(600, 500)
        self.configure(fg_color=BG_DARK)

        self._build_header()
        self._build_chat_area()
        self._build_input_area()
        self._build_status_bar()

        self.voice_in = None
        self.processor = None
        self._is_busy = False

        self._set_status("Инициализация...", "#ffaa00")
        threading.Thread(target=self._init_backend, daemon=True).start()

        self._tick_clock()

    # ========== Построение интерфейса ==========

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG_PANEL, height=60, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"  ◉  {ASSISTANT_NAME.upper()}",
            font=("Consolas", 20, "bold"),
            text_color=ACCENT,
        ).pack(side="left", padx=15)

        self.clock_label = ctk.CTkLabel(
            header, text="",
            font=("Consolas", 12), text_color=TEXT_MUTED,
        )
        self.clock_label.pack(side="right", padx=15)

    def _build_chat_area(self):
        self.chat_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=BG_DARK,
            scrollbar_button_color=ACCENT,
            scrollbar_button_hover_color=ACCENT_HOVER,
        )
        self.chat_frame.pack(fill="both", expand=True, padx=15, pady=(10, 5))

        self._add_bot_message(
            f"Готов помочь, {USER_NAME}. "
            f"Напишите команду или нажмите 🎤 для голоса."
        )

    def _build_input_area(self):
        input_frame = ctk.CTkFrame(self, fg_color=BG_PANEL, height=70, corner_radius=0)
        input_frame.pack(fill="x", side="bottom")
        input_frame.pack_propagate(False)

        self.entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Напишите команду или вопрос...",
            font=("Segoe UI", 13),
            fg_color=BG_INPUT,
            border_color=ACCENT, border_width=1,
            text_color=TEXT_MAIN, height=42,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(15, 8), pady=14)
        self.entry.bind("<Return>", lambda e: self._on_send())

        self.mic_button = ctk.CTkButton(
            input_frame, text="🎤",
            font=("Segoe UI", 18), width=50, height=42,
            fg_color=BG_INPUT, text_color=ACCENT,
            hover_color="#1a2a4a",
            border_color=ACCENT, border_width=1,
            command=self._on_mic_click,
        )
        self.mic_button.pack(side="left", padx=(0, 8), pady=14)

        self.send_button = ctk.CTkButton(
            input_frame, text="➤",
            font=("Segoe UI", 18, "bold"), width=50, height=42,
            fg_color=ACCENT, text_color="#000000",
            hover_color=ACCENT_HOVER,
            command=self._on_send,
        )
        self.send_button.pack(side="left", padx=(0, 15), pady=14)

    def _build_status_bar(self):
        status_frame = ctk.CTkFrame(self, fg_color=BG_DARK, height=22, corner_radius=0)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)

        self.status_dot = ctk.CTkLabel(
            status_frame, text="●",
            font=("Segoe UI", 14), text_color="#666666",
        )
        self.status_dot.pack(side="left", padx=(15, 5))

        self.status_label = ctk.CTkLabel(
            status_frame, text="ОЖИДАНИЕ",
            font=("Consolas", 10), text_color=TEXT_MUTED,
        )
        self.status_label.pack(side="left")

    # ========== Сообщения ==========

    def _add_message_bubble(self, text: str, is_user: bool):
        timestamp = datetime.now().strftime("%H:%M")
        anchor = "e" if is_user else "w"
        bubble_color = USER_BUBBLE if is_user else BOT_BUBBLE
        author = USER_NAME if is_user else ASSISTANT_NAME

        row = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        row.pack(fill="x", anchor=anchor, pady=4, padx=5)

        bubble = ctk.CTkFrame(
            row,
            fg_color=bubble_color,
            corner_radius=14,
            border_color=ACCENT if not is_user else "#3d5a8a",
            border_width=1,
        )
        bubble.pack(anchor=anchor, padx=4)

        ctk.CTkLabel(
            bubble, text=f"{author}  ·  {timestamp}",
            font=("Consolas", 9),
            text_color=ACCENT if not is_user else "#8aaedf",
        ).pack(anchor="w", padx=14, pady=(8, 0))

        ctk.CTkLabel(
            bubble, text=text,
            font=("Segoe UI", 13),
            text_color=TEXT_MAIN, justify="left", wraplength=540,
        ).pack(anchor="w", padx=14, pady=(2, 10))

        self.after(50, self._scroll_to_bottom)

    def _add_user_message(self, text: str):
        self._add_message_bubble(text, is_user=True)

    def _add_bot_message(self, text: str):
        self._add_message_bubble(text, is_user=False)

    def _safe_bot_message(self, text: str):
        """Безопасный вызов из фоновых потоков."""
        self.after(0, lambda t=text: self._add_bot_message(t))

    def _safe_user_message(self, text: str):
        self.after(0, lambda t=text: self._add_user_message(t))

    def _scroll_to_bottom(self):
        try:
            self.chat_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    # ========== Статус ==========

    def _set_status(self, text: str, color: str = TEXT_MUTED):
        """Безопасно обновить статус-бар (из любого потока)."""
        def _apply():
            self.status_dot.configure(text_color=color)
            self.status_label.configure(text=text.upper(), text_color=color)
        self.after(0, _apply)

    def _tick_clock(self):
        now = datetime.now().strftime("%d.%m.%Y  %H:%M:%S")
        self.clock_label.configure(text=now)
        self.after(1000, self._tick_clock)

    # ========== Бэкенд ==========

    def _init_backend(self):
        """Инициализация ассистента (тяжёлое — в потоке)."""
        try:
            real_voice = VoiceOutput()
            gui_voice = GuiVoiceOutput(real_voice, self)
            self.processor = CommandProcessor(gui_voice)

            try:
                self.voice_in = VoiceInput()
            except Exception as e:
                print(f"[GUI] Микрофон недоступен: {e}")
                self.voice_in = None
                self.after(0, lambda: self.mic_button.configure(
                    state="disabled", text="🚫"
                ))

            self._set_status("ГОТОВ", ACCENT)
        except Exception as e:
            print(f"[GUI] Ошибка инициализации: {e}")
            self._set_status("ОШИБКА", "#ff5555")

    def _set_busy(self, busy: bool):
        """Переключить флаг занятости и блокировку UI."""
        self._is_busy = busy
        # Кнопки тоже подсветим — наглядно показать, что идёт обработка
        state = "disabled" if busy else "normal"
        self.after(0, lambda: self.send_button.configure(state=state))

    # ========== Обработчики кнопок ==========

    def _on_send(self):
        """Кнопка отправить / Enter в поле ввода."""
        if self._is_busy or self.processor is None:
            return

        text = self.entry.get().strip()
        if not text:
            return

        self.entry.delete(0, "end")
        self._add_user_message(text)

        threading.Thread(
            target=self._process_command, args=(text,), daemon=True
        ).start()

    def _process_command(self, text: str):
        self._set_busy(True)
        self._set_status("ОБРАБОТКА...", "#ffaa00")
        try:
            self.processor.process(text)
        except Exception as e:
            self._safe_bot_message(f"[Ошибка] {e}")
        finally:
            self._set_status("ГОТОВ", ACCENT)
            self._set_busy(False)

    def _on_mic_click(self):
        """Кнопка микрофона — слушать одну фразу."""
        if self._is_busy or self.voice_in is None or self.processor is None:
            return
        threading.Thread(target=self._listen_once, daemon=True).start()

    def _listen_once(self):
        """Разовое прослушивание без wake-word."""
        self._set_busy(True)
        self._set_status("СЛУШАЮ...", "#ff5577")
        self.after(0, lambda: self.mic_button.configure(
            fg_color=ACCENT, text_color="#000000", text="●"
        ))

        try:
            phrase = self.voice_in.listen(timeout=5, phrase_time_limit=8)
            if phrase:
                self._safe_user_message(phrase)
                self._set_status("ОБРАБОТКА...", "#ffaa00")
                self.processor.process(phrase)
            else:
                self._safe_bot_message("Ничего не услышал.")
        except Exception as e:
            self._safe_bot_message(f"[Микрофон] {e}")
        finally:
            self.after(0, lambda: self.mic_button.configure(
                fg_color=BG_INPUT, text_color=ACCENT, text="🎤"
            ))
            self._set_status("ГОТОВ", ACCENT)
            self._set_busy(False)


if __name__ == "__main__":
    app = ChatGUI()
    app.mainloop()
