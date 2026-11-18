import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from soundcloud_studio.ui.main_window import MainWindow
from soundcloud_studio.services.paths import ensure_app_dirs

def main():
    ensure_app_dirs()
    app = QApplication(sys.argv)
    app.setApplicationName("SoundCloud Studio")
    app.setOrganizationName("SoundCloudStudio")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
