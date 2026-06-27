from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTreeWidget,
    QTreeWidgetItem,
)

from objects import SceneObject


OBJECT_ID_ROLE = Qt.ItemDataRole.UserRole
VISIBLE_ROLE = Qt.ItemDataRole.UserRole + 1

ICON_DIR = Path(__file__).resolve().parent / "icons"
EYE_ICON = QIcon(str(ICON_DIR / "eye.svg"))
EYE_OFF_ICON = QIcon(str(ICON_DIR / "eye_off.svg"))


class ComponentTree(QTreeWidget):
    object_selected = Signal(object)
    visibility_changed = Signal(str, bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setUniformRowHeights(True)
        self.setRootIsDecorated(True)
        self.setIconSize(QSize(18, 18))
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 24)

        self._root = QTreeWidgetItem(["Scene", ""])
        self._root.setData(0, OBJECT_ID_ROLE, None)
        self.addTopLevelItem(self._root)
        self._root.setExpanded(True)

        self.currentItemChanged.connect(self._emit_current_object)
        self.itemClicked.connect(self._handle_item_clicked)

    def add_object(self, obj: SceneObject) -> None:
        item = QTreeWidgetItem([self._label_for(obj), ""])
        item.setData(0, OBJECT_ID_ROLE, obj.id)
        item.setData(1, VISIBLE_ROLE, obj.visible)
        item.setIcon(1, EYE_ICON if obj.visible else EYE_OFF_ICON)
        item.setToolTip(0, self._label_for(obj))
        item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
        self._root.addChild(item)
        self._root.setExpanded(True)
        self.setCurrentItem(item)

    def remove_object(self, object_id: str) -> None:
        item = self._find_item(object_id)
        if item is None:
            return
        parent = item.parent()
        if parent is not None:
            parent.removeChild(item)
        self.setCurrentItem(self._root)

    def refresh_object(self, obj: SceneObject) -> None:
        item = self._find_item(obj.id)
        if item is not None:
            label = self._label_for(obj)
            item.setText(0, label)
            item.setToolTip(0, label)
            item.setData(1, VISIBLE_ROLE, obj.visible)
            item.setIcon(1, EYE_ICON if obj.visible else EYE_OFF_ICON)

    def current_object_id(self) -> str | None:
        item = self.currentItem()
        if item is None:
            return None
        value = item.data(0, OBJECT_ID_ROLE)
        return value if isinstance(value, str) else None

    def select_object(self, object_id: str | None) -> None:
        if object_id is None:
            self.setCurrentItem(self._root)
            return
        item = self._find_item(object_id)
        if item is not None:
            self.setCurrentItem(item)

    def _emit_current_object(self, current: QTreeWidgetItem | None, _previous) -> None:
        if current is None:
            self.object_selected.emit(None)
            return
        value = current.data(0, OBJECT_ID_ROLE)
        self.object_selected.emit(value if isinstance(value, str) else None)

    def _handle_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 1:
            return
        object_id = item.data(0, OBJECT_ID_ROLE)
        if not isinstance(object_id, str):
            return
        current = bool(item.data(1, VISIBLE_ROLE))
        self.visibility_changed.emit(object_id, not current)

    def _find_item(self, object_id: str) -> QTreeWidgetItem | None:
        for index in range(self._root.childCount()):
            item = self._root.child(index)
            if item.data(0, OBJECT_ID_ROLE) == object_id:
                return item
        return None

    def _label_for(self, obj: SceneObject) -> str:
        if obj.kind == "gds_layer":
            return f"{obj.name}  L{obj.layer}/{obj.datatype}"
        return obj.name
