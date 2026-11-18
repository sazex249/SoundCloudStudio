import sqlite3
from datetime import datetime
from ..services.paths import DB_PATH

class Store:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(DB_PATH)
        self.db.execute('''CREATE TABLE IF NOT EXISTS history (
            id TEXT PRIMARY KEY, title TEXT, artist TEXT, path TEXT, downloaded_at TEXT)''')
        self.db.execute('''CREATE TABLE IF NOT EXISTS queue (
            id TEXT PRIMARY KEY, payload TEXT, status TEXT, updated_at TEXT)''')
        self.db.commit()

    def add_history(self, track_id, title, artist, path):
        self.db.execute("INSERT OR REPLACE INTO history VALUES (?,?,?,?,?)",
                        (str(track_id), title, artist, str(path), datetime.now().isoformat(timespec="seconds")))
        self.db.commit()

    def history(self):
        return self.db.execute("SELECT id,title,artist,path,downloaded_at FROM history ORDER BY downloaded_at DESC").fetchall()

    def save_queue_item(self, track_id, payload, status):
        import json
        self.db.execute("INSERT OR REPLACE INTO queue VALUES (?,?,?,?)",
                        (str(track_id), json.dumps(payload, ensure_ascii=False), status,
                         datetime.now().isoformat(timespec="seconds")))
        self.db.commit()

    def pending_queue(self):
        import json
        rows = self.db.execute("SELECT payload,status FROM queue WHERE status IN ('queued','failed')").fetchall()
        result = []
        for payload, status in rows:
            try:
                item = json.loads(payload)
                if item.get("url"):
                    result.append(item)
            except (ValueError, TypeError):
                continue
        return result

    def close(self):
        self.db.close()
