from pathlib import Path
from platformdirs import user_data_dir, user_music_dir

APP_DIR = Path(user_data_dir("SoundCloudStudio", "SoundCloudStudio"))
DOWNLOAD_DIR = Path(user_music_dir()) / "SoundCloud Studio"
DB_PATH = APP_DIR / "studio.sqlite3"
SETTINGS_PATH = APP_DIR / "settings.json"

def ensure_app_dirs():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
