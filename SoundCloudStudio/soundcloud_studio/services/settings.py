import json
from .paths import SETTINGS_PATH, DOWNLOAD_DIR

DEFAULTS = {
    "download_dir": str(DOWNLOAD_DIR),
    "audio_format": "mp3",
    "mp3_quality": "0",
    "save_cover": True,
    "save_metadata": True,
    "skip_existing": True,
    "theme": "dark"
}

class Settings:
    def __init__(self):
        self.data = dict(DEFAULTS)
        self.load()

    def load(self):
        try:
            if SETTINGS_PATH.exists():
                loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.data.update({k: v for k, v in loaded.items() if k in DEFAULTS})
        except (OSError, ValueError):
            pass

    def save(self):
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = SETTINGS_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(SETTINGS_PATH)

    def get(self, key):
        return self.data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        if key in DEFAULTS:
            self.data[key] = value
            self.save()
