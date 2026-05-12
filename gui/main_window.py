"""Минималистичный GUI в стиле HUD"""
import threading
from datetime import datetime
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class JarvisGUI(ctk.CTk):
    BG = "#0a0e27"
    ACCENT = "#00d4ff"
    TEXT = "#e0f7ff"

    def __init__(self):
        super().__init__()
        self.title("Поко Чоко")
        self.geometry("720x520")
        self.configure(fg_color=self.BG)

        ctk.CTkLabel(
            self, text="ПОКО ЧОКО",
            font=("Consolas", 36, "bold"),
            text_color=self.ACCENT,
        ).pack(pady=(20, 0))

        ctk.CTkLabel(
            self, text="Personal AI Assistant",
            font=("Consolas", 11), text_color=self.TEXT,
        ).pack()

        self.status = ctk.CTkLabel(
            self, text="● ОЖИДАНИЕ",
            font=("Consolas", 14, "bold"), text_color="#666666",
        )
        self.status.pack(pady=10)

        self.clock = ctk.CTkLabel(
            self, text="", font=("Consolas", 12), text_color=self.ACCENT,
        )
        self.clock.pack()

        self.log_box = ctk.CTkTextbox(
            self, width=660, height=300,
            font=("Consolas", 11),
            fg_color="#050818", text_color=self.TEXT,
            border_color=self.ACCENT, border_width=1, corner_radius=8,
        )
        self.log_box.pack(pady=15, padx=20)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=5)

        ctk.CTkButton(
            btns, text="ЗАПУСТИТЬ", width=140,
            fg_color=self.ACCENT, text_color="#000000",
            hover_color="#00a3cc", command=self._start,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btns, text="ВЫХОД", width=140,
            fg_color="transparent", text_color=self.ACCENT,
            border_color=self.ACCENT, border_width=1,
            hover_color="#1a2a4a", command=self.destroy,
        ).pack(side="left", padx=5)

        self._tick_clock()

    def _tick_clock(self):
        self.clock.configure(text=datetime.now().strftime("%d.%m.%Y  %H:%M:%S"))
        self.after(1000, self._tick_clock)

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.see("end")

    def _start(self):
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import start_assistant_loop

        self.status.configure(text="● АКТИВЕН", text_color=self.ACCENT)
        self.log("Система активирована.")
        threading.Thread(
            target=start_assistant_loop,
            args=(self.log,),
            daemon=True,
        ).start()


if __name__ == "__main__":
    JarvisGUI().mainloop()
