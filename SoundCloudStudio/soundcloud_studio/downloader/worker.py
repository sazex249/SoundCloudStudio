from pathlib import Path
from PySide6.QtCore import QThread, Signal
import yt_dlp

class DownloadWorker(QThread):
    progress = Signal(str, float, str)
    completed = Signal(dict)
    failed = Signal(str, str)

    def __init__(self, track, settings):
        super().__init__()
        self.track = track
        self.settings = dict(settings)
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        track = self.track
        outdir = Path(self.settings["download_dir"])
        outdir.mkdir(parents=True, exist_ok=True)
        fmt = self.settings.get("audio_format", "mp3")
        quality = self.settings.get("mp3_quality", "0")
        safe_id = "".join(c for c in str(track["id"]) if c.isalnum() or c in "-_")[:80]
        if not safe_id:
            safe_id = "track"
        template = str(outdir / f"%(title).180B [{safe_id}].%(ext)s")

        def hook(data):
            if self._cancelled:
                raise yt_dlp.utils.DownloadError("Загрузка отменена пользователем")
            if data.get("status") == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                done = data.get("downloaded_bytes") or 0
                pct = (done / total * 100) if total else 0
                speed = data.get("speed") or 0
                speed_text = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "—"
                self.progress.emit(str(track["id"]), pct, speed_text)
            elif data.get("status") == "finished":
                self.progress.emit(str(track["id"]), 100, "Обработка…")

        opts = {
            "outtmpl": template, "quiet": True, "no_warnings": True,
            "noplaylist": True, "continuedl": True, "overwrites": False,
            "progress_hooks": [hook], "retries": 3, "fragment_retries": 3,
            "writethumbnail": bool(self.settings.get("save_cover", True)),
            "writeinfojson": bool(self.settings.get("save_metadata", True)),
        }
        # imageio-ffmpeg ships a platform-specific FFmpeg binary.
        try:
            import imageio_ffmpeg
            opts["ffmpeg_location"] = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            if fmt == "mp3":
                self.failed.emit(str(track["id"]),
                    "Для конвертации в MP3 не найден FFmpeg. Выберите исходный формат.")
                return

        if fmt == "mp3":
            opts.update({"format": "bestaudio/best", "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                 "preferredquality": str(quality)},
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"}
            ]})
        else:
            opts["format"] = "bestaudio/best"
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(track["url"], download=True)
                filepath = ydl.prepare_filename(info)
                if fmt == "mp3":
                    filepath = str(Path(filepath).with_suffix(".mp3"))
                path = Path(filepath)
                if not path.exists():
                    candidates = sorted(outdir.glob(f"*[{safe_id}].*"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if candidates:
                        path = candidates[0]
                if not path.exists():
                    raise RuntimeError("Загрузка завершилась, но итоговый файл не найден.")
                self.completed.emit({"track": track, "path": str(path)})
        except Exception as exc:
            self.failed.emit(str(track["id"]), str(exc))
