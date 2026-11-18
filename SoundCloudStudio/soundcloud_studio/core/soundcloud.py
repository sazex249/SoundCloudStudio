import re
import yt_dlp

SOUNDCLOUD_RE = re.compile(r"^https?://(www\\.)?soundcloud\\.com/", re.I)

class SoundCloudService:
    @staticmethod
    def validate_url(url):
        url = (url or "").strip()
        if not SOUNDCLOUD_RE.match(url):
            raise ValueError("Введите корректную публичную ссылку SoundCloud.")
        return url

    def fetch(self, url):
        url = self.validate_url(url)
        opts = {
            "quiet": True, "no_warnings": True, "extract_flat": "in_playlist",
            "skip_download": True, "ignoreerrors": True, "playlistend": 1000,
            "socket_timeout": 20, "retries": 2
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            raise RuntimeError("SoundCloud не вернул данные для этой ссылки.")
        entries = info.get("entries")
        if entries is None:
            entries = [info]
        tracks = []
        for item in entries:
            if not item:
                continue
            track_url = item.get("url") or item.get("webpage_url")
            if track_url and not str(track_url).startswith("http"):
                track_url = "https://soundcloud.com/" + str(track_url).lstrip("/")
            if not track_url:
                continue
            tracks.append({
                "id": str(item.get("id") or track_url),
                "title": item.get("title") or "Untitled",
                "artist": item.get("uploader") or item.get("artist") or info.get("uploader") or "Unknown artist",
                "duration": item.get("duration"),
                "thumbnail": item.get("thumbnail"),
                "url": track_url,
                "downloadable": item.get("availability") not in ("private", "subscriber_only"),
                "status": "Проверяется при загрузке"
            })
        profile = {
            "name": info.get("uploader") or info.get("title") or "SoundCloud",
            "avatar": info.get("thumbnails", [{}])[-1].get("url") if info.get("thumbnails") else info.get("thumbnail"),
            "count": len(tracks),
            "title": info.get("title") or ""
        }
        return profile, tracks
