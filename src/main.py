from __future__ import annotations

import os
import sys
from pathlib import Path


os.environ.setdefault("QT_API", "pyside6")


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from main_window import MainWindow

    app = QApplication(sys.argv)
    _apply_style(app)

    window = MainWindow()
    window.show()

    return app.exec()


def _apply_style(app) -> None:
    qss_path = Path(__file__).resolve().parent / "industrial.qss"
    if qss_path.exists():
        icon_dir = (Path(__file__).resolve().parent / "icons").as_posix()
        qss = qss_path.read_text(encoding="utf-8").replace("$ICON_DIR", icon_dir)
        app.setStyleSheet(qss)


if __name__ == "__main__":
    raise SystemExit(main())
