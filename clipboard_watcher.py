import threading
import time
import pyperclip


class ClipboardWatcher:
    def __init__(self, on_new_content, interval=0.5):
        self.on_new_content = on_new_content
        self.interval = interval
        self.running = False
        self.last_content = ""
        self.thread = None
        self.paused = False

    def start(self):
        if self.running:
            return
        self.running = True
        try:
            self.last_content = pyperclip.paste()
        except Exception:
            self.last_content = ""
        self.thread = threading.Thread(target=self._watch, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        try:
            self.last_content = pyperclip.paste()
        except Exception:
            pass
        self.paused = False

    def _watch(self):
        while self.running:
            if not self.paused:
                try:
                    current = pyperclip.paste()
                    if current != self.last_content and current.strip():
                        self.last_content = current
                        self.on_new_content(current)
                except Exception:
                    pass
            time.sleep(self.interval)

    def set_clipboard(self, content):
        self.last_content = content
        pyperclip.copy(content)