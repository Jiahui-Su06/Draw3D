from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from i18n import tr


ExportFormat = Literal["png", "svg", "pdf"]
ExportQuality = Literal["standard", "high"]

EXPORT_FORMATS: tuple[ExportFormat, ...] = ("png", "svg", "pdf")
EXPORT_QUALITIES: tuple[ExportQuality, ...] = ("standard", "high")
EXPORT_QUALITY_SCALES: dict[ExportQuality, int] = {
    "standard": 2,
    "high": 4,
}


@dataclass(frozen=True)
class ExportOptions:
    file_format: ExportFormat
    image_scale: int


class ExportDialog(QDialog):
    def __init__(
        self,
        default_format: ExportFormat,
        default_quality: ExportQuality,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.export_as"))
        self.setModal(True)
        self.setMinimumSize(330, 230)

        self._format_combo = QComboBox()
        self._format_combo.setObjectName("formatCombo")
        for file_format in EXPORT_FORMATS:
            self._format_combo.addItem(_format_label(file_format), file_format)
        format_index = self._format_combo.findData(default_format)
        self._format_combo.setCurrentIndex(max(format_index, 0))
        self._format_combo.currentIndexChanged.connect(self._sync_quality_visibility)

        self._quality_label = _section_label(tr("export.quality"))
        self._quality_combo = QComboBox()
        self._quality_combo.setObjectName("qualityCombo")
        for quality in EXPORT_QUALITIES:
            self._quality_combo.addItem(tr(f"export.quality_{quality}"), quality)
        quality_index = self._quality_combo.findData(default_quality)
        self._quality_combo.setCurrentIndex(max(quality_index, 0))

        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.setObjectName("dialogButton")
        cancel_button.setObjectName("dialogButton")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        button_layout.addStretch(1)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch(1)

        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(20, 20, 20, 18)
        settings_layout.setSpacing(10)
        settings_layout.addWidget(_section_label(tr("export.format")))
        settings_layout.addWidget(self._format_combo)
        settings_layout.addSpacing(10)
        settings_layout.addWidget(self._quality_label)
        settings_layout.addWidget(self._quality_combo)
        settings_layout.addStretch(1)
        settings_layout.addLayout(button_layout)

        settings_frame = QFrame()
        settings_frame.setObjectName("exportSettings")
        settings_frame.setLayout(settings_layout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        layout.addWidget(settings_frame)

        self.setStyleSheet(
            """
            QDialog {
                background: #f6f7f9;
            }
            QFrame#exportSettings {
                min-width: 300px;
                background: #f6f7f9;
            }
            QLabel[role="section"] {
                color: #1f2328;
                font-weight: 600;
                background: transparent;
            }
            QComboBox#formatCombo,
            QComboBox#qualityCombo {
                min-height: 30px;
                padding: 3px 28px 3px 8px;
                border: 1px solid #b8c2cc;
                border-radius: 2px;
                background: #ffffff;
                color: #1f2328;
            }
            QComboBox#formatCombo:hover,
            QComboBox#qualityCombo:hover {
                border-color: #6d8fbd;
                background: #f9fbfd;
            }
            QComboBox#formatCombo::drop-down,
            QComboBox#qualityCombo::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #9aa8b8;
                background: #dce5ef;
            }
            QComboBox#formatCombo::drop-down:hover,
            QComboBox#qualityCombo::drop-down:hover {
                background: #9fbce3;
            }
            QComboBox#formatCombo::down-arrow,
            QComboBox#qualityCombo::down-arrow {
                image: url("$SPIN_DOWN_ICON");
                width: 8px;
                height: 8px;
            }
            QPushButton#dialogButton {
                min-width: 78px;
                min-height: 28px;
                padding: 3px 10px;
                border: 1px solid #b8c2cc;
                border-radius: 2px;
                background: #ffffff;
                color: #1f2328;
            }
            QPushButton#dialogButton:hover {
                background: #b9d0ee;
                border-color: #6d8fbd;
            }
            """
            .replace("$SPIN_DOWN_ICON", _icon_path("spin_down.svg"))
        )

    def options(self) -> ExportOptions:
        file_format = self._current_format()
        quality = self._quality_combo.currentData()
        if quality not in EXPORT_QUALITIES:
            quality = "standard"
        return ExportOptions(
            file_format=file_format,
            image_scale=EXPORT_QUALITY_SCALES[quality],
        )

    def _current_format(self) -> ExportFormat:
        value = self._format_combo.currentData()
        if value in EXPORT_FORMATS:
            return value
        return "png"

    def _sync_quality_visibility(self) -> None:
        file_format = self._current_format()
        has_quality = file_format in {"png", "pdf"}
        self._quality_label.setVisible(has_quality)
        self._quality_combo.setVisible(has_quality)


def _section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("role", "section")
    return label


def _format_label(file_format: ExportFormat) -> str:
    if file_format == "png":
        return "PNG"
    if file_format == "svg":
        return "SVG"
    return "PDF"


def _icon_path(name: str) -> str:
    return (Path(__file__).resolve().parent / "icons" / name).as_posix()
