"""
Routes module for Star Wars Map Editor.

Contains data structures and graphics items for routes (splines between systems).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
import uuid

from PyQt5.QtWidgets import (
    QGraphicsPathItem, QGraphicsEllipseItem, QGraphicsItem
)
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainterPath, QPen, QColor, QBrush


@dataclass
class RouteData:
    """
    Data structure representing a route between two systems.
    
    Attributes:
        id: Unique route identifier.
        name: Optional route name (can be empty or auto-generated).
        start_system_id: ID of the starting system.
        end_system_id: ID of the ending system.
        control_points: List of control points in scene coordinates used to bend the spline.
        color: Route color in hex format.
        width: Route line width.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    start_system_id: str = ""
    end_system_id: str = ""
    control_points: List[QPointF] = field(default_factory=list)
    color: str = "#4CAF50"  # Green default
    width: float = 3.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "start_system_id": self.start_system_id,
            "end_system_id": self.end_system_id,
            "control_points": [[p.x(), p.y()] for p in self.control_points],
            "color": self.color,
            "width": self.width,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RouteData":
        """Create from dictionary."""
        control_points = [
            QPointF(p[0], p[1]) for p in data.get("control_points", [])
        ]
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            start_system_id=data.get("start_system_id", ""),
            end_system_id=data.get("end_system_id", ""),
            control_points=control_points,
            color=data.get("color", "#4CAF50"),
            width=data.get("width", 3.0),
        )


class RouteHandleItem(QGraphicsEllipseItem):
    """
    A draggable handle for editing route control points.
    
    When dragged, updates the corresponding control point in the parent RouteItem.
    """
    
    HANDLE_SIZE = 12
    
    def __init__(
        self,
        position: QPointF,
        index: int,
        route_item: "RouteItem",
        parent: Optional[QGraphicsItem] = None
    ):
        """
        Initialize a control point handle.
        
        Args:
            position: The initial position of the handle.
            index: The index of this control point in the route's control_points list.
            route_item: The parent RouteItem this handle belongs to.
            parent: Optional parent graphics item.
        """
        half = self.HANDLE_SIZE / 2
        super().__init__(-half, -half, self.HANDLE_SIZE, self.HANDLE_SIZE, parent)
        
        self._index = index
        self._route_item = route_item
        
        self.setPos(position)
        self.setBrush(QBrush(QColor("#2196F3")))  # Blue handle
        self.setPen(QPen(QColor("#1565C0"), 2))
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        self.setZValue(20)  # Above routes and systems
        self.setCursor(Qt.CrossCursor)
    
    @property
    def index(self) -> int:
        """Get the index of this control point."""
        return self._index
    
    def itemChange(self, change, value):
        """Handle position changes and update the route."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            self._route_item.update_control_point(self._index, value)
        return super().itemChange(change, value)


class RouteItem(QGraphicsPathItem):
    """
    Graphics item representing a route (spline) between two systems.
    
    Draws a smooth curve using cubic Bezier segments through control points.
    When selected, shows draggable handles for editing control points.
    """
    
    def __init__(
        self,
        data: RouteData,
        get_system_position: Callable[[str], Optional[QPointF]],
        parent: Optional[QGraphicsItem] = None
    ):
        """
        Initialize a RouteItem.
        
        Args:
            data: The RouteData instance this item represents.
            get_system_position: Callable that takes a system ID and returns
                its position, or None if not found.
            parent: Optional parent graphics item.
        """
        super().__init__(parent)
        
        self._data = data
        self._get_system_position = get_system_position
        self._handles: List[RouteHandleItem] = []
        self._show_handles = False
        
        # Set appearance
        pen = QPen(QColor(data.color))
        pen.setWidthF(data.width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        self.setPen(pen)
        
        # Enable selection
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Z-value for layering (routes below systems)
        self.setZValue(5)
        
        # Build the initial path
        self.rebuild_path()
    
    @property
    def data(self) -> RouteData:
        """Get the underlying RouteData."""
        return self._data
    
    @property
    def route_id(self) -> str:
        """Get the route's unique ID."""
        return self._data.id
    
    def set_name(self, name: str) -> None:
        """Set the route name."""
        self._data.name = name
    
    def set_color(self, color: str) -> None:
        """Set the route color."""
        self._data.color = color
        pen = self.pen()
        pen.setColor(QColor(color))
        self.setPen(pen)
    
    def set_width(self, width: float) -> None:
        """Set the route line width."""
        self._data.width = width
        pen = self.pen()
        pen.setWidthF(width)
        self.setPen(pen)
    
    def get_start_position(self) -> Optional[QPointF]:
        """Get the current position of the start system."""
        return self._get_system_position(self._data.start_system_id)
    
    def get_end_position(self) -> Optional[QPointF]:
        """Get the current position of the end system."""
        return self._get_system_position(self._data.end_system_id)
    
    def rebuild_path(self) -> None:
        """
        Rebuild the spline path based on current system positions and control points.
        
        Uses cubic Bezier curves for smooth interpolation.
        """
        start_pos = self.get_start_position()
        end_pos = self.get_end_position()
        
        if start_pos is None or end_pos is None:
            # Can't draw if either endpoint is missing
            self.setPath(QPainterPath())
            return
        
        path = QPainterPath()
        path.moveTo(start_pos)
        
        control_points = self._data.control_points
        
        if not control_points:
            # No control points - draw straight line
            path.lineTo(end_pos)
        elif len(control_points) == 1:
            # One control point - quadratic Bezier
            path.quadTo(control_points[0], end_pos)
        else:
            # Multiple control points - chain of cubic Bezier curves
            points = [start_pos] + control_points + [end_pos]
            self._build_smooth_curve(path, points)
        
        self.setPath(path)
    
    def _build_smooth_curve(self, path: QPainterPath, points: List[QPointF]) -> None:
        """
        Build a smooth curve through the given points using cubic Bezier segments.
        
        Uses Catmull-Rom to cubic Bezier conversion for smooth interpolation.
        """
        n = len(points)
        if n < 2:
            return
        
        if n == 2:
            path.lineTo(points[1])
            return
        
        # For each segment, calculate cubic Bezier control points
        for i in range(n - 1):
            p0 = points[max(0, i - 1)]
            p1 = points[i]
            p2 = points[i + 1]
            p3 = points[min(n - 1, i + 2)]
            
            # Catmull-Rom to cubic Bezier conversion
            cp1 = QPointF(
                p1.x() + (p2.x() - p0.x()) / 6,
                p1.y() + (p2.y() - p0.y()) / 6
            )
            cp2 = QPointF(
                p2.x() - (p3.x() - p1.x()) / 6,
                p2.y() - (p3.y() - p1.y()) / 6
            )
            
            path.cubicTo(cp1, cp2, p2)
    
    def update_control_point(self, index: int, position: QPointF) -> None:
        """
        Update a control point position and rebuild the path.
        
        Args:
            index: The index of the control point to update.
            position: The new position.
        """
        if 0 <= index < len(self._data.control_points):
            self._data.control_points[index] = position
            self.rebuild_path()
    
    def add_control_point(self, position: QPointF, index: Optional[int] = None) -> None:
        """
        Add a new control point to the route.
        
        Args:
            position: The position for the new control point.
            index: Optional index to insert at. If None, appends to end.
        """
        if index is None:
            self._data.control_points.append(position)
        else:
            self._data.control_points.insert(index, position)
        
        self.rebuild_path()
        
        if self._show_handles:
            self._rebuild_handles()
    
    def remove_control_point(self, index: int) -> None:
        """
        Remove a control point from the route.
        
        Args:
            index: The index of the control point to remove.
        """
        if 0 <= index < len(self._data.control_points):
            del self._data.control_points[index]
            self.rebuild_path()
            
            if self._show_handles:
                self._rebuild_handles()
    
    def show_handles(self, show: bool = True) -> None:
        """
        Show or hide the control point handles.
        
        Args:
            show: Whether to show handles.
        """
        self._show_handles = show
        
        if show:
            self._rebuild_handles()
        else:
            self._clear_handles()
    
    def _rebuild_handles(self) -> None:
        """Create handle items for all control points."""
        self._clear_handles()
        
        scene = self.scene()
        if scene is None:
            return
        
        for i, point in enumerate(self._data.control_points):
            handle = RouteHandleItem(point, i, self)
            scene.addItem(handle)
            self._handles.append(handle)
    
    def _clear_handles(self) -> None:
        """Remove all handle items from the scene."""
        scene = self.scene()
        for handle in self._handles:
            if scene is not None:
                scene.removeItem(handle)
        self._handles.clear()
    
    def sync_handles_from_data(self) -> None:
        """Sync handle positions from data (after data modification)."""
        for i, handle in enumerate(self._handles):
            if i < len(self._data.control_points):
                handle.setPos(self._data.control_points[i])
    
    def on_system_moved(self, system_id: str) -> None:
        """
        Handle notification that a connected system has moved.
        
        Args:
            system_id: The ID of the system that moved.
        """
        if system_id in (self._data.start_system_id, self._data.end_system_id):
            self.rebuild_path()
    
    def itemChange(self, change, value):
        """Handle selection changes to show/hide handles."""
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.show_handles(value)
        return super().itemChange(change, value)
    
    def cleanup(self) -> None:
        """Clean up resources before removal."""
        self._clear_handles()
