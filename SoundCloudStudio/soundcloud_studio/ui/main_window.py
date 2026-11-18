from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget,
    QFrame, QMessageBox, QProgressBar, QComboBox, QFileDialog, QCheckBox,
    QAbstractItemView, QSplitter
)
from .theme import STYLE
from ..core.soundcloud import SoundCloudService
from ..downloader.worker import DownloadWorker
from ..services.settings import Settings
from ..database.store import Store

def duration(value):
    if not value:
        return "—"
    sec = int(value)
    return f"{sec // 60}:{sec % 60:02d}"

class SearchWorker(QThread):
    done = Signal(dict, list)
    error = Signal(str)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            profile, tracks = SoundCloudService().fetch(self.url)
            self.done.emit(profile, tracks)
        except Exception as exc:
            self.error.emit(str(exc))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SoundCloud Studio")
        self.resize(1320, 850)
        self.setMinimumSize(1050, 680)
        self.setStyleSheet(STYLE)
        self.settings = Settings()
        self.store = Store()
        self.tracks = []
        self.workers = {}
        self.queue_rows = {}
        self._build()
        self._restore_history()
        self._restore_pending_queue()

    def _build(self):
        base = QWidget()
        root = QHBoxLayout(base)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 25, 18, 18)
        side.setSpacing(8)
        brand = QLabel("◉  SoundCloud Studio")
        brand.setObjectName("Brand")
        side.addWidget(brand)
        sub = QLabel("YOUR MUSIC WORKSPACE")
        sub.setObjectName("Muted")
        side.addWidget(sub)
        side.addSpacing(25)
        self.nav_buttons = []
        for i, name in enumerate(["⌂   Обзор библиотеки", "⇩   Очередь загрузок", "◷   История", "⚙   Настройки"]):
            b = QPushButton(name)
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.clicked.connect(lambda checked=False, idx=i: self.show_page(idx))
            side.addWidget(b)
            self.nav_buttons.append(b)
        side.addStretch()
        version = QLabel("SOUNDCloud STUDIO  •  1.0.0")
        version.setObjectName("Muted")
        side.addWidget(version)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._library_page())
        self.pages.addWidget(self._queue_page())
        self.pages.addWidget(self._history_page())
        self.pages.addWidget(self._settings_page())
        root.addWidget(sidebar)
        root.addWidget(self.pages, 1)
        self.setCentralWidget(base)
        self.show_page(0)

    def _page_shell(self, title, subtitle):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 27, 30, 26)
        layout.setSpacing(18)
        heading = QLabel(title)
        heading.setObjectName("PageTitle")
        desc = QLabel(subtitle)
        desc.setObjectName("Muted")
        layout.addWidget(heading)
        layout.addWidget(desc)
        return page, layout

    def _library_page(self):
        page, layout = self._page_shell("Музыкальная библиотека", "Откройте публичный профиль или плейлист SoundCloud")
        bar = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Вставьте ссылку на профиль или плейлист SoundCloud…")
        self.url_input.returnPressed.connect(self.search_profile)
        self.search_btn = QPushButton("Найти библиотеку")
        self.search_btn.setObjectName("Primary")
        self.search_btn.clicked.connect(self.search_profile)
        bar.addWidget(self.url_input, 1)
        bar.addWidget(self.search_btn)
        layout.addLayout(bar)

        self.profile_label = QLabel("Пока ничего не загружено")
        self.profile_label.setObjectName("SectionTitle")
        layout.addWidget(self.profile_label)

        controls = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Поиск по названию или исполнителю…")
        self.filter_input.textChanged.connect(self.filter_tracks)
        self.sort_box = QComboBox()
        self.sort_box.addItems(["Без сортировки", "Название A–Я", "Название Я–А", "Длительность"])
        self.sort_box.currentIndexChanged.connect(self.render_tracks)
        self.select_all_btn = QPushButton("Выбрать все")
        self.select_all_btn.clicked.connect(self.select_all)
        self.download_btn = QPushButton("↓  Скачать выбранное")
        self.download_btn.setObjectName("Primary")
        self.download_btn.clicked.connect(self.download_selected)
        controls.addWidget(self.filter_input, 1)
        controls.addWidget(self.sort_box)
        controls.addWidget(self.select_all_btn)
        controls.addWidget(self.download_btn)
        layout.addLayout(controls)

        self.track_table = QTableWidget(0, 5)
        self.track_table.setHorizontalHeaderLabels(["", "КОМПОЗИЦИЯ", "ИСПОЛНИТЕЛЬ", "ДЛИТЕЛЬНОСТЬ", "ДОСТУПНОСТЬ"])
        self.track_table.verticalHeader().setVisible(False)
        self.track_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.track_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.track_table.setAlternatingRowColors(True)
        self.track_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.track_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.track_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.track_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.track_table.setColumnWidth(0, 42)
        layout.addWidget(self.track_table, 1)
        self.library_status = QLabel("Готово к поиску")
        self.library_status.setObjectName("Muted")
        layout.addWidget(self.library_status)
        return page

    def _queue_page(self):
        page, layout = self._page_shell("Очередь загрузок", "Состояние текущих и завершённых задач")
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)
        self.total_progress.setValue(0)
        layout.addWidget(QLabel("Общий прогресс"))
        layout.addWidget(self.total_progress)
        self.queue_table = QTableWidget(0, 4)
        self.queue_table.setHorizontalHeaderLabels(["КОМПОЗИЦИЯ", "ПРОГРЕСС", "СКОРОСТЬ", "СТАТУС"])
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.queue_table, 1)
        actions = QHBoxLayout()
        self.cancel_btn = QPushButton("Отменить активные")
        self.cancel_btn.clicked.connect(self.cancel_downloads)
        self.retry_btn = QPushButton("Повторить ошибки")
        self.retry_btn.clicked.connect(self.retry_failed)
        actions.addWidget(self.cancel_btn)
        actions.addWidget(self.retry_btn)
        actions.addStretch()
        layout.addLayout(actions)
        return page

    def _history_page(self):
        page, layout = self._page_shell("История загрузок", "Файлы, сохранённые на этом компьютере")
        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["КОМПОЗИЦИЯ", "ИСПОЛНИТЕЛЬ", "ДАТА", "ФАЙЛ"])
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.history_table, 1)
        open_btn = QPushButton("Открыть расположение выбранного файла")
        open_btn.clicked.connect(self.open_history_folder)
        layout.addWidget(open_btn)
        return page

    def _settings_page(self):
        page, layout = self._page_shell("Настройки", "Папка сохранения, аудиоформат и метаданные")
        layout.addWidget(QLabel("Папка сохранения"))
        row = QHBoxLayout()
        self.folder_input = QLineEdit(self.settings.get("download_dir"))
        browse = QPushButton("Обзор…")
        browse.clicked.connect(self.choose_folder)
        row.addWidget(self.folder_input, 1)
        row.addWidget(browse)
        layout.addLayout(row)
        layout.addWidget(QLabel("Формат аудио"))
        self.format_box = QComboBox()
        self.format_box.addItems(["mp3", "source"])
        self.format_box.setCurrentText(self.settings.get("audio_format"))
        layout.addWidget(self.format_box)
        layout.addWidget(QLabel("Качество MP3"))
        self.quality_box = QComboBox()
        self.quality_box.addItems(["0", "128", "192", "256", "320"])
        self.quality_box.setCurrentText(str(self.settings.get("mp3_quality")))
        layout.addWidget(self.quality_box)
        self.cover_check = QCheckBox("Сохранять обложки")
        self.cover_check.setChecked(self.settings.get("save_cover"))
        layout.addWidget(self.cover_check)
        self.meta_check = QCheckBox("Сохранять метаданные (JSON)")
        self.meta_check.setChecked(self.settings.get("save_metadata"))
        layout.addWidget(self.meta_check)
        self.skip_check = QCheckBox("Пропускать уже скачанные файлы")
        self.skip_check.setChecked(self.settings.get("skip_existing"))
        layout.addWidget(self.skip_check)
        save = QPushButton("Сохранить настройки")
        save.setObjectName("Primary")
        save.clicked.connect(self.save_settings)
        layout.addWidget(save)
        layout.addStretch()
        return page

    def show_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

    def search_profile(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.information(self, "SoundCloud Studio", "Сначала вставьте ссылку SoundCloud.")
            return
        self.search_btn.setEnabled(False)
        self.library_status.setText("Получаем библиотеку…")
        self.search_worker = SearchWorker(url)
        self.search_worker.done.connect(self.on_search_done)
        self.search_worker.error.connect(self.on_search_error)
        self.search_worker.finished.connect(lambda: self.search_btn.setEnabled(True))
        self.search_worker.start()

    def on_search_done(self, profile, tracks):
        self.tracks = tracks
        self.profile_label.setText(f"{profile['name']}     •     {len(tracks)} композиций")
        self.library_status.setText(f"Найдено композиций: {len(tracks)}")
        self.render_tracks()

    def on_search_error(self, message):
        self.library_status.setText("Не удалось получить библиотеку")
        QMessageBox.warning(self, "Ошибка поиска", message)

    def filter_tracks(self):
        query = self.filter_input.text().lower()
        for row in range(self.track_table.rowCount()):
            title = self.track_table.item(row, 1).text().lower()
            artist = self.track_table.item(row, 2).text().lower()
            self.track_table.setRowHidden(row, query not in title and query not in artist)

    def render_tracks(self):
        tracks = list(self.tracks)
        mode = self.sort_box.currentIndex()
        if mode == 1:
            tracks.sort(key=lambda t: t["title"].casefold())
        elif mode == 2:
            tracks.sort(key=lambda t: t["title"].casefold(), reverse=True)
        elif mode == 3:
            tracks.sort(key=lambda t: t.get("duration") or 0)
        self.track_table.setRowCount(0)
        for track in tracks:
            row = self.track_table.rowCount()
            self.track_table.insertRow(row)
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            check.setCheckState(Qt.Unchecked)
            check.setData(Qt.UserRole, track["id"])
            self.track_table.setItem(row, 0, check)
            self.track_table.setItem(row, 1, QTableWidgetItem(track["title"]))
            self.track_table.setItem(row, 2, QTableWidgetItem(track["artist"]))
            self.track_table.setItem(row, 3, QTableWidgetItem(duration(track.get("duration"))))
            self.track_table.setItem(row, 4, QTableWidgetItem("Проверяется при загрузке"))
            self.track_table.setRowHeight(row, 48)
        self.filter_tracks()

    def select_all(self):
        state = Qt.Unchecked if self.track_table.rowCount() and all(
            self.track_table.item(r, 0).checkState() == Qt.Checked for r in range(self.track_table.rowCount())
        ) else Qt.Checked
        for r in range(self.track_table.rowCount()):
            if not self.track_table.isRowHidden(r):
                self.track_table.item(r, 0).setCheckState(state)

    def download_selected(self):
        selected_ids = {
            self.track_table.item(r, 0).data(Qt.UserRole)
            for r in range(self.track_table.rowCount())
            if self.track_table.item(r, 0).checkState() == Qt.Checked
        }
        selected = [t for t in self.tracks if t["id"] in selected_ids]
        if not selected:
            QMessageBox.information(self, "Очередь", "Выберите хотя бы одну композицию.")
            return
        for track in selected:
            if track["id"] in self.workers:
                continue
            if self.settings.get("skip_existing"):
                # History IDs are checked first; the worker also avoids overwriting existing names.
                if any(str(h[0]) == str(track["id"]) and Path(h[3]).exists() for h in self.store.history()):
                    continue
            self.enqueue(track)
        self.show_page(1)

    def enqueue(self, track):
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)
        self.queue_table.setItem(row, 0, QTableWidgetItem(track["title"]))
        bar = QProgressBar()
        bar.setValue(0)
        self.queue_table.setCellWidget(row, 1, bar)
        self.queue_table.setItem(row, 2, QTableWidgetItem("—"))
        self.queue_table.setItem(row, 3, QTableWidgetItem("В очереди"))
        self.queue_rows[str(track["id"])] = row
        self.store.save_queue_item(track["id"], track, "queued")
        self.start_download(track)

    def start_download(self, track):
        settings = dict(self.settings.data)
        worker = DownloadWorker(track, settings)
        worker.progress.connect(self.on_download_progress)
        worker.completed.connect(self.on_download_complete)
        worker.failed.connect(self.on_download_failed)
        worker.finished.connect(lambda tid=str(track["id"]): self.workers.pop(tid, None))
        self.workers[str(track["id"])] = worker
        row = self.queue_rows[str(track["id"])]
        self.queue_table.setItem(row, 3, QTableWidgetItem("Загружается"))
        worker.start()

    def on_download_progress(self, track_id, percent, speed):
        row = self.queue_rows.get(track_id)
        if row is None:
            return
        bar = self.queue_table.cellWidget(row, 1)
        if bar:
            bar.setValue(int(percent))
        self.queue_table.setItem(row, 2, QTableWidgetItem(speed))
        self.update_total_progress()

    def update_total_progress(self):
        values = []
        for row in range(self.queue_table.rowCount()):
            bar = self.queue_table.cellWidget(row, 1)
            values.append(bar.value() if bar else 0)
        self.total_progress.setValue(int(sum(values) / len(values)) if values else 0)

    def on_download_complete(self, result):
        track, path = result["track"], result["path"]
        tid = str(track["id"])
        row = self.queue_rows.get(tid)
        if row is not None:
            self.queue_table.setItem(row, 3, QTableWidgetItem("Готово"))
            bar = self.queue_table.cellWidget(row, 1)
            if bar: bar.setValue(100)
        self.store.add_history(tid, track["title"], track["artist"], path)
        self.store.save_queue_item(tid, track, "completed")
        self._restore_history()
        self.update_total_progress()

    def on_download_failed(self, track_id, message):
        row = self.queue_rows.get(track_id)
        if row is not None:
            self.queue_table.setItem(row, 3, QTableWidgetItem("Ошибка"))
        self.store.save_queue_item(track_id, {"id": track_id}, "failed")
        QMessageBox.warning(self, "Ошибка загрузки", message[:1200])

    def retry_failed(self):
        failed_ids = []
        for row in range(self.queue_table.rowCount()):
            status = self.queue_table.item(row, 3)
            if status and status.text() == "Ошибка":
                for track_id, mapped_row in self.queue_rows.items():
                    if mapped_row == row:
                        failed_ids.append(track_id)
        for track_id in failed_ids:
            track = next((t for t in self.tracks if str(t["id"]) == track_id), None)
            if track and track_id not in self.workers:
                self.store.save_queue_item(track_id, track, "queued")
                self.start_download(track)

    def cancel_downloads(self):
        for worker in list(self.workers.values()):
            worker.cancel()
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Отмена…")
        # Re-enable after workers have had a chance to stop.
        for worker in list(self.workers.values()):
            worker.finished.connect(lambda: self.cancel_btn.setEnabled(True))
            worker.finished.connect(lambda: self.cancel_btn.setText("Отменить активные"))

    def _restore_pending_queue(self):
        # Requeue items left in the persistent queue by an interrupted session.
        for track in self.store.pending_queue():
            if str(track.get("id")) not in self.workers:
                self.enqueue(track)

    def _restore_history(self):
        rows = self.store.history()
        self.history_table.setRowCount(0)
        for track_id, title, artist, path, date in rows:
            r = self.history_table.rowCount()
            self.history_table.insertRow(r)
            for c, value in enumerate([title, artist, date.replace("T", " "), path]):
                self.history_table.setItem(r, c, QTableWidgetItem(str(value)))

    def open_history_folder(self):
        row = self.history_table.currentRow()
        if row < 0:
            return
        path = Path(self.history_table.item(row, 3).text())
        if path.exists():
            import os
            os.startfile(str(path.parent))
        else:
            QMessageBox.information(self, "Файл не найден", "Файл больше не существует по сохранённому пути.")

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Папка сохранения", self.folder_input.text())
        if folder:
            self.folder_input.setText(folder)

    def save_settings(self):
        folder = Path(self.folder_input.text()).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if not folder.is_dir():
                raise OSError("Указанный путь не является папкой.")
        except OSError as exc:
            QMessageBox.warning(self, "Папка недоступна", str(exc))
            return
        self.settings.set("download_dir", str(folder))
        self.settings.set("audio_format", self.format_box.currentText())
        self.settings.set("mp3_quality", self.quality_box.currentText())
        self.settings.set("save_cover", self.cover_check.isChecked())
        self.settings.set("save_metadata", self.meta_check.isChecked())
        self.settings.set("skip_existing", self.skip_check.isChecked())
        QMessageBox.information(self, "Настройки", "Настройки сохранены.")

    def closeEvent(self, event):
        active = list(self.workers.values())
        if active:
            answer = QMessageBox.question(self, "Загрузки выполняются",
                "Загрузки ещё выполняются. Отменить их и закрыть приложение?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            for worker in active:
                worker.cancel()
                worker.wait()
        self.store.close()
        event.accept()
