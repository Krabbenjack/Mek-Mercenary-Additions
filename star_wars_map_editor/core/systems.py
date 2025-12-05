"""
Systems module for Star Wars Map Editor.

Contains data structures and graphics items for star systems.
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid

from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen


@dataclass
class SystemData:
    """Data structure representing a star system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    color: str = "#FFD700"  # Gold/yellow default
    size: float = 20.0
    
    def position(self) -> QPointF:
        """Get the system's position as a QPointF."""
        return QPointF(self.x, self.y)
    
    def set_position(self, pos: QPointF) -> None:
        """Set the system's position from a QPointF."""
        self.x = pos.x()
        self.y = pos.y()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "size": self.size,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SystemData":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            color=data.get("color", "#FFD700"),
            size=data.get("size", 20.0),
        )


class SystemItem(QGraphicsEllipseItem):
    """
    Graphics item representing a star system on the map.
    
    Displays as a colored ellipse with an optional label.
    """
    
    def __init__(self, data: SystemData, parent: Optional[QGraphicsItem] = None):
        """
        Initialize a SystemItem.
        
        Args:
            data: The SystemData instance this item represents.
            parent: Optional parent graphics item.
        """
        self._data = data
        half_size = data.size / 2
        super().__init__(-half_size, -half_size, data.size, data.size, parent)
        
        # Set position
        self.setPos(data.x, data.y)
        
        # Set appearance
        color = QColor(data.color)
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(130), 2))
        
        # Enable selection and movement
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Create label
        self._label = QGraphicsTextItem(data.name, self)
        self._label.setDefaultTextColor(QColor("#FFFFFF"))
        self._update_label_position()
        
        # Z-value for layering (systems on top of routes)
        self.setZValue(10)
    
    @property
    def data(self) -> SystemData:
        """Get the underlying SystemData."""
        return self._data
    
    @property
    def system_id(self) -> str:
        """Get the system's unique ID."""
        return self._data.id
    
    def set_name(self, name: str) -> None:
        """Set the system name and update the label."""
        self._data.name = name
        self._label.setPlainText(name)
        self._update_label_position()
    
    def set_color(self, color: str) -> None:
        """Set the system color."""
        self._data.color = color
        qcolor = QColor(color)
        self.setBrush(QBrush(qcolor))
        self.setPen(QPen(qcolor.darker(130), 2))
    
    def _update_label_position(self) -> None:
        """Position the label centered below the system."""
        label_rect = self._label.boundingRect()
        self._label.setPos(
            -label_rect.width() / 2,
            self._data.size / 2 + 5
        )
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position updates."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            pos = value
            self._data.x = pos.x()
            self._data.y = pos.y()
            # Notify scene about position change (for route updates)
            scene = self.scene()
            if scene is not None and hasattr(scene, 'on_system_moved'):
                scene.on_system_moved(self.system_id)
        return super().itemChange(change, value)
    
    def sync_from_data(self) -> None:
        """Sync the item's visual state from its data."""
        self.setPos(self._data.x, self._data.y)
        half_size = self._data.size / 2
        self.setRect(-half_size, -half_size, self._data.size, self._data.size)
        self.set_color(self._data.color)
        self._label.setPlainText(self._data.name)
        self._update_label_position()
