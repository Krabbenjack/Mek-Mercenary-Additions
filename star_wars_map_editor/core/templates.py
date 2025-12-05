"""
Templates module for Star Wars Map Editor.

Contains data structures and graphics items for background map templates.
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid

from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPixmap


@dataclass
class TemplateData:
    """
    Data structure representing a background template image.
    
    Attributes:
        id: Unique template identifier.
        name: Template name.
        file_path: Path to the image file.
        x: X position in scene coordinates.
        y: Y position in scene coordinates.
        scale: Scale factor (1.0 = original size).
        opacity: Opacity value (0.0 to 1.0).
        locked: Whether the template is locked from editing.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    file_path: str = ""
    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0
    opacity: float = 0.7
    locked: bool = False
    
    def position(self) -> QPointF:
        """Get the template's position as a QPointF."""
        return QPointF(self.x, self.y)
    
    def set_position(self, pos: QPointF) -> None:
        """Set the template's position from a QPointF."""
        self.x = pos.x()
        self.y = pos.y()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "x": self.x,
            "y": self.y,
            "scale": self.scale,
            "opacity": self.opacity,
            "locked": self.locked,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TemplateData":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            file_path=data.get("file_path", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            scale=data.get("scale", 1.0),
            opacity=data.get("opacity", 0.7),
            locked=data.get("locked", False),
        )


class TemplateItem(QGraphicsPixmapItem):
    """
    Graphics item representing a background template image.
    
    Templates are used for aligning/tracing background maps.
    """
    
    def __init__(self, data: TemplateData, parent: Optional[QGraphicsItem] = None):
        """
        Initialize a TemplateItem.
        
        Args:
            data: The TemplateData instance this item represents.
            parent: Optional parent graphics item.
        """
        super().__init__(parent)
        
        self._data = data
        self._original_pixmap: Optional[QPixmap] = None
        
        # Load the image if path is provided
        if data.file_path:
            self.load_image(data.file_path)
        
        # Set position
        self.setPos(data.x, data.y)
        
        # Apply scale and opacity
        self.setScale(data.scale)
        self.setOpacity(data.opacity)
        
        # Enable selection and movement (unless locked)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not data.locked)
        self.setFlag(QGraphicsItem.ItemIsMovable, not data.locked)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Z-value for layering (templates at bottom)
        self.setZValue(0)
    
    @property
    def data(self) -> TemplateData:
        """Get the underlying TemplateData."""
        return self._data
    
    @property
    def template_id(self) -> str:
        """Get the template's unique ID."""
        return self._data.id
    
    def load_image(self, file_path: str) -> bool:
        """
        Load an image from file.
        
        Args:
            file_path: Path to the image file.
            
        Returns:
            True if loading succeeded, False otherwise.
        """
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return False
        
        self._original_pixmap = pixmap
        self._data.file_path = file_path
        self.setPixmap(pixmap)
        return True
    
    def set_template_scale(self, scale: float) -> None:
        """Set the template scale."""
        self._data.scale = scale
        self.setScale(scale)
    
    def set_template_opacity(self, opacity: float) -> None:
        """Set the template opacity (0.0 to 1.0)."""
        self._data.opacity = max(0.0, min(1.0, opacity))
        self.setOpacity(self._data.opacity)
    
    def set_locked(self, locked: bool) -> None:
        """Set whether the template is locked from editing."""
        self._data.locked = locked
        self.setFlag(QGraphicsItem.ItemIsSelectable, not locked)
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
    
    def reset_transform(self) -> None:
        """Reset scale and position to defaults."""
        self._data.scale = 1.0
        self._data.x = 0.0
        self._data.y = 0.0
        self.setScale(1.0)
        self.setPos(0.0, 0.0)
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position updates."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            pos = value
            self._data.x = pos.x()
            self._data.y = pos.y()
        return super().itemChange(change, value)
    
    def sync_from_data(self) -> None:
        """Sync the item's visual state from its data."""
        self.setPos(self._data.x, self._data.y)
        self.setScale(self._data.scale)
        self.setOpacity(self._data.opacity)
        self.set_locked(self._data.locked)
        
        if self._data.file_path and self._original_pixmap is None:
            self.load_image(self._data.file_path)
