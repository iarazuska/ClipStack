import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import keyboard
from clipboard_watcher import ClipboardWatcher
from storage import load_history, save_history, add_item, toggle_pin, remove_item, clear_unpinned

BG = "#0d0d1a"
BG2 = "#12122a"
BG3 = "#1a1a3e"
BG4 = "#222244"
FG = "#e8e8ff"
FG2 = "#8888aa"
ACCENT = "#7c4dff"
ACCENT2 = "#651fff"
GREEN = "#00e676"
ERROR = "#ff5252"
WARNING = "#ffab40"
FONT_UI = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)
FONT_TITLE = ("Segoe UI", 15, "bold")

GLOBAL_HOTKEY = "ctrl+shift+v"


class ClipStackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClipStack")
        self.root.geometry("500x650")
        self.root.configure(bg=BG)
        self.root.minsize(400, 400)

        self.history = load_history()
        self.filtered = self.history.copy()

        self._build_header()
        self._build_search()
        self._build_list()
        self._build_statusbar()
        self._refresh_list()

        self.watcher = ClipboardWatcher(self._on_new_clip)
        self.watcher.start()

        self._setup_hotkey()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Unmap>", self._on_minimize)

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG3, pady=14)
        header.pack(fill=tk.X)

        tk.Label(header, text="📋 ClipStack", bg=BG3, fg=FG, font=FONT_TITLE).pack(side=tk.LEFT, padx=16)
        tk.Label(header, text="  —  Clipboard Manager", bg=BG3, fg=FG2, font=FONT_UI).pack(side=tk.LEFT)

        tk.Button(
            header, text="🗑 Limpiar",
            bg=BG4, fg=FG2, font=("Segoe UI", 9),
            relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
            activebackground=ERROR, activeforeground="white",
            command=self._clear_history
        ).pack(side=tk.RIGHT, padx=12)

    def _build_search(self):
        frame = tk.Frame(self.root, bg=BG, pady=10)
        frame.pack(fill=tk.X, padx=16)

        tk.Label(frame, text="🔍", bg=BG, fg=FG2, font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            frame, bg=BG3, fg=FG, font=FONT_UI,
            relief=tk.FLAT, insertbackground=FG,
            textvariable=self.search_var, bd=0
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self.search_var.trace_add("write", lambda *a: self._filter())

        hint = tk.Label(
            self.root, text=f"Atajo global: {GLOBAL_HOTKEY.upper()}",
            bg=BG, fg=FG2, font=("Segoe UI", 8)
        )
        hint.pack(anchor=tk.W, padx=16, pady=(0, 6))

    def _build_list(self):
        canvas_frame = tk.Frame(self.root, bg=BG2)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        self.canvas = tk.Canvas(canvas_frame, bg=BG2, highlightthickness=0)
        scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.list_frame = tk.Frame(self.canvas, bg=BG2)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        self.list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=BG3, pady=5)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(bar, text="Escuchando portapapeles...", bg=BG3, fg=GREEN, font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT, padx=12)
        tk.Label(bar, text="ClipStack v1.0", bg=BG3, fg=FG2, font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=12)

    def _on_new_clip(self, content):
        self.history = add_item(self.history, content)
        self.root.after(0, self._filter)
        self.root.after(0, lambda: self._set_status("✓ Copiado capturado", GREEN))

    def _set_status(self, text, color=None):
        self.status_label.config(text=text, fg=color or GREEN)
        self.root.after(2000, lambda: self.status_label.config(text="Escuchando portapapeles...", fg=GREEN))

    def _filter(self):
        query = self.search_var.get().lower().strip()
        if query:
            self.filtered = [h for h in self.history if query in h["content"].lower()]
        else:
            self.filtered = self.history.copy()
        self._refresh_list()

    def _refresh_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        if not self.filtered:
            tk.Label(
                self.list_frame, text="No hay elementos en el historial",
                bg=BG2, fg=FG2, font=FONT_UI
            ).pack(pady=40)
            return

        for item in self.filtered:
            self._build_item_card(item)

    def _build_item_card(self, item):
        content = item["content"]
        pinned = item["pinned"]

        card = tk.Frame(self.list_frame, bg=BG3 if not pinned else BG4, pady=8, padx=10)
        card.pack(fill=tk.X, padx=4, pady=3)

        top = tk.Frame(card, bg=card["bg"])
        top.pack(fill=tk.X)

        preview = content.replace("\n", " ⏎ ")
        if len(preview) > 80:
            preview = preview[:80] + "..."

        label = tk.Label(
            top, text=preview, bg=card["bg"], fg=FG,
            font=FONT_MONO, anchor="w", justify=tk.LEFT,
            wraplength=320, cursor="hand2"
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        label.bind("<Button-1>", lambda e, c=content: self._copy_to_clipboard(c))

        try:
            ts = datetime.fromisoformat(item["timestamp"])
            time_str = ts.strftime("%H:%M")
        except Exception:
            time_str = ""

        actions = tk.Frame(card, bg=card["bg"])
        actions.pack(fill=tk.X, pady=(4, 0))

        tk.Label(actions, text=time_str, bg=card["bg"], fg=FG2, font=("Segoe UI", 8)).pack(side=tk.LEFT)

        pin_text = "📌" if pinned else "📍"
        pin_btn = tk.Button(
            actions, text=pin_text, bg="transparent" if False else card["bg"],
            fg=ACCENT if pinned else FG2, font=("Segoe UI", 10),
            relief=tk.FLAT, padx=6, cursor="hand2",
            activebackground=card["bg"], activeforeground=ACCENT,
            command=lambda c=content: self._toggle_pin(c)
        )
        pin_btn.pack(side=tk.RIGHT, padx=2)

        del_btn = tk.Button(
            actions, text="✕", bg=card["bg"],
            fg=FG2, font=("Segoe UI", 10),
            relief=tk.FLAT, padx=6, cursor="hand2",
            activebackground=card["bg"], activeforeground=ERROR,
            command=lambda c=content: self._delete_item(c)
        )
        del_btn.pack(side=tk.RIGHT, padx=2)

        copy_btn = tk.Button(
            actions, text="Copiar", bg=card["bg"],
            fg=ACCENT, font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT, padx=8, cursor="hand2",
            activebackground=card["bg"], activeforeground=ACCENT2,
            command=lambda c=content: self._copy_to_clipboard(c)
        )
        copy_btn.pack(side=tk.RIGHT, padx=2)

    def _copy_to_clipboard(self, content):
        self.watcher.set_clipboard(content)
        self._set_status("✓ Copiado al portapapeles", GREEN)

    def _toggle_pin(self, content):
        self.history = toggle_pin(self.history, content)
        self._filter()

    def _delete_item(self, content):
        self.history = remove_item(self.history, content)
        self._filter()

    def _clear_history(self):
        confirm = messagebox.askyesno(
            "Limpiar historial",
            "¿Eliminar todos los elementos no fijados? Los fijados se mantendrán."
        )
        if confirm:
            self.history = clear_unpinned(self.history)
            self._filter()
            self._set_status("Historial limpiado", WARNING)

    def _setup_hotkey(self):
        def show_window():
            self.root.after(0, self._show_window)

        try:
            keyboard.add_hotkey(GLOBAL_HOTKEY, show_window)
        except Exception:
            pass

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.watcher.resume()

    def _on_minimize(self, event):
        if self.root.state() == "iconic":
            pass

    def _on_close(self):
        self.watcher.stop()
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self.root.destroy()