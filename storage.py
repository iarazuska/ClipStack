import json
import os
from datetime import datetime

STORAGE_DIR = os.path.join(os.path.expanduser("~"), ".clipstack")
STORAGE_FILE = os.path.join(STORAGE_DIR, "history.json")

MAX_ITEMS = 100


def ensure_dir():
    os.makedirs(STORAGE_DIR, exist_ok=True)


def load_history():
    ensure_dir()
    if not os.path.exists(STORAGE_FILE):
        return []
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history):
    ensure_dir()
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def add_item(history, content):
    if not content or not content.strip():
        return history

    history = [h for h in history if h["content"] != content]

    item = {
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "pinned": False
    }
    history.insert(0, item)

    pinned = [h for h in history if h["pinned"]]
    unpinned = [h for h in history if not h["pinned"]]
    unpinned = unpinned[:MAX_ITEMS]
    history = pinned + unpinned

    save_history(history)
    return history


def toggle_pin(history, content):
    for item in history:
        if item["content"] == content:
            item["pinned"] = not item["pinned"]
            break
    pinned = [h for h in history if h["pinned"]]
    unpinned = [h for h in history if not h["pinned"]]
    history = pinned + unpinned
    save_history(history)
    return history


def remove_item(history, content):
    history = [h for h in history if h["content"] != content]
    save_history(history)
    return history


def clear_unpinned(history):
    history = [h for h in history if h["pinned"]]
    save_history(history)
    return history