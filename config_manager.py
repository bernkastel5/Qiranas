# config_manager.py
import threading
import time
from config import read_config

class ConfigManager:
    def __init__(self, path='config.txt', poll_interval=2):
        self.path = path
        self.poll_interval = poll_interval
        self.config = read_config(self.path)
        self.last_content = self._get_file_content()
        self.callbacks = []
        self.running = True
        threading.Thread(target=self._watch, daemon=True).start()

    def _get_file_content(self):
        try:
            with open(self.path, encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

    def _watch(self):
        while self.running:
            time.sleep(self.poll_interval)
            content = self._get_file_content()
            if content != self.last_content:
                self.last_content = content
                self.config = read_config(self.path)
                for cb in self.callbacks:
                    cb(self.config)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def on_change(self, callback):
        self.callbacks.append(callback)

    def stop(self):
        self.running = False

config_manager = ConfigManager('config.txt')