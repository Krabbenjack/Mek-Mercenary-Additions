"""
Star Wars Map Editor - Main GUI Application.

A PyQt5-based map editor for creating Star Wars galaxy maps with:
- Systems (star systems as nodes)
- Routes (spline connections between systems)
- Templates (background map images)

Provides three editing modes:
- Template Mode: For aligning background maps
- Systems Mode: For placing and editing systems
- Routes Mode: For creating and editing routes between systems
"""

import sys
import os
from typing import Optional, Dict, List
from enum import Enum, auto

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QToolBar, QAction, QActionGroup,
    QStatusBar, QFileDialog, QMessageBox, QInputDialog, QLabel,
    QSlider, QPushButton, QFrame, QGroupBox, QDoubleSpinBox,
    QSpinBox, QDockWidget, QMenu, QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt5.QtGui import (
    QColor, QPen, QBrush, QPainter, QKeySequence, QWheelEvent,
    QMouseEvent, QKeyEvent, QTransform
)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project_model import MapProject
from core.project_io import save_project, load_project, get_project_file_filter
from core.systems import SystemData, SystemItem
from core.routes import RouteData, RouteItem
from core.templates import TemplateData, TemplateItem


class EditorMode(Enum):
    """Enumeration of editor modes."""
    TEMPLATE = auto()
    SYSTEMS = auto()
    ROUTES = auto()


class MapScene(QGraphicsScene):
    """
    Custom graphics scene for the map editor.
    
    Manages systems, routes, and templates as graphics items.
    Provides grid drawing and system movement notifications.
    """
    
    def __init__(self, project: MapProject, parent=None):
        super().__init__(parent)
        self._project = project
        
        # Graphics items indexed by ID
        self._system_items: Dict[str, SystemItem] = {}
        self._route_items: Dict[str, RouteItem] = {}
        self._template_items: Dict[str, TemplateItem] = {}
        
        # Grid settings
        self._show_grid = True
        self._grid_size = 50
        self._grid_color = QColor(60, 60, 60)
        
        # Set scene rect
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.setBackgroundBrush(QBrush(QColor(20, 20, 30)))
    
    @property
    def project(self) -> MapProject:
        """Get the project."""
        return self._project
    
    def set_project(self, project: MapProject) -> None:
        """Set a new project and rebuild all items."""
        self._project = project
        self.rebuild_all()
    
    def rebuild_all(self) -> None:
        """Rebuild all graphics items from project data."""
        self.clear_items()
        
        # Rebuild templates (bottom layer)
        for template_data in self._project.templates.values():
            self._create_template_item(template_data)
        
        # Rebuild routes (middle layer)
        for route_data in self._project.routes.values():
            self._create_route_item(route_data)
        
        # Rebuild systems (top layer)
        for system_data in self._project.systems.values():
            self._create_system_item(system_data)
    
    def clear_items(self) -> None:
        """Remove all managed items from the scene."""
        for item in self._system_items.values():
            self.removeItem(item)
        for item in self._route_items.values():
            item.cleanup()
            self.removeItem(item)
        for item in self._template_items.values():
            self.removeItem(item)
        
        self._system_items.clear()
        self._route_items.clear()
        self._template_items.clear()
    
    # ---------- System operations ----------
    
    def _create_system_item(self, data: SystemData) -> SystemItem:
        """Create and add a system item."""
        item = SystemItem(data)
        self.addItem(item)
        self._system_items[data.id] = item
        return item
    
    def add_system(self, data: SystemData) -> SystemItem:
        """Add a new system to the scene."""
        self._project.add_system(data)
        return self._create_system_item(data)
    
    def remove_system(self, system_id: str) -> None:
        """Remove a system from the scene."""
        item = self._system_items.pop(system_id, None)
        if item:
            self.removeItem(item)
        
        # Remove from project (also removes connected routes)
        removed_system = self._project.remove_system(system_id)
        
        if removed_system:
            # Remove route items that were connected
            routes_to_remove = [
                rid for rid, route in list(self._route_items.items())
                if route.data.start_system_id == system_id or route.data.end_system_id == system_id
            ]
            for rid in routes_to_remove:
                self._remove_route_item(rid)
    
    def get_system_item(self, system_id: str) -> Optional[SystemItem]:
        """Get a system item by ID."""
        return self._system_items.get(system_id)
    
    def on_system_moved(self, system_id: str) -> None:
        """Handle notification that a system has moved."""
        # Update all routes connected to this system
        for route_item in self._route_items.values():
            route_item.on_system_moved(system_id)
    
    # ---------- Route operations ----------
    
    def _create_route_item(self, data: RouteData) -> RouteItem:
        """Create and add a route item."""
        item = RouteItem(
            data,
            get_system_position=self._project.get_system_position
        )
        self.addItem(item)
        self._route_items[data.id] = item
        return item
    
    def _remove_route_item(self, route_id: str) -> None:
        """Remove a route item from the scene."""
        item = self._route_items.pop(route_id, None)
        if item:
            item.cleanup()
            self.removeItem(item)
    
    def add_route(self, data: RouteData) -> Optional[RouteItem]:
        """Add a new route to the scene."""
        route = self._project.add_route(data)
        if route:
            return self._create_route_item(data)
        return None
    
    def remove_route(self, route_id: str) -> None:
        """Remove a route from the scene."""
        self._remove_route_item(route_id)
        self._project.remove_route(route_id)
    
    def get_route_item(self, route_id: str) -> Optional[RouteItem]:
        """Get a route item by ID."""
        return self._route_items.get(route_id)
    
    # ---------- Template operations ----------
    
    def _create_template_item(self, data: TemplateData) -> TemplateItem:
        """Create and add a template item."""
        item = TemplateItem(data)
        self.addItem(item)
        self._template_items[data.id] = item
        return item
    
    def add_template(self, data: TemplateData) -> TemplateItem:
        """Add a new template to the scene."""
        self._project.add_template(data)
        return self._create_template_item(data)
    
    def remove_template(self, template_id: str) -> None:
        """Remove a template from the scene."""
        item = self._template_items.pop(template_id, None)
        if item:
            self.removeItem(item)
        self._project.remove_template(template_id)
    
    def get_template_item(self, template_id: str) -> Optional[TemplateItem]:
        """Get a template item by ID."""
        return self._template_items.get(template_id)
    
    # ---------- Grid drawing ----------
    
    def set_grid_visible(self, visible: bool) -> None:
        """Set grid visibility."""
        self._show_grid = visible
        self.update()
    
    def set_grid_size(self, size: int) -> None:
        """Set grid cell size."""
        self._grid_size = size
        self.update()
    
    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw scene background including grid."""
        super().drawBackground(painter, rect)
        
        if not self._show_grid:
            return
        
        # Draw grid
        pen = QPen(self._grid_color)
        pen.setWidth(1)
        painter.setPen(pen)
        
        left = int(rect.left()) - (int(rect.left()) % self._grid_size)
        top = int(rect.top()) - (int(rect.top()) % self._grid_size)
        
        # Vertical lines
        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += self._grid_size
        
        # Horizontal lines
        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += self._grid_size


class MapView(QGraphicsView):
    """
    Custom graphics view for the map editor.
    
    Provides zoom-under-cursor and WASD/arrow key panning.
    """
    
    def __init__(self, scene: MapScene, parent=None):
        super().__init__(scene, parent)
        
        self._map_scene = scene
        
        # Zoom settings
        self._zoom_factor = 1.15
        self._min_zoom = 0.1
        self._max_zoom = 10.0
        self._current_zoom = 1.0
        
        # Pan settings
        self._pan_speed = 20
        self._panning = False
        self._pan_start = QPointF()
        
        # View setup
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Enable focus for keyboard events
        self.setFocusPolicy(Qt.StrongFocus)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle zoom with mouse wheel."""
        # Get the position in scene coordinates before zoom
        old_pos = self.mapToScene(event.pos())
        
        # Calculate zoom factor
        if event.angleDelta().y() > 0:
            factor = self._zoom_factor
        else:
            factor = 1.0 / self._zoom_factor
        
        # Check zoom limits
        new_zoom = self._current_zoom * factor
        if new_zoom < self._min_zoom or new_zoom > self._max_zoom:
            return
        
        self._current_zoom = new_zoom
        
        # Apply zoom
        self.scale(factor, factor)
        
        # Get the new position and adjust to zoom under cursor
        new_pos = self.mapToScene(event.pos())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle WASD and arrow key panning."""
        key = event.key()
        
        dx = 0
        dy = 0
        
        if key in (Qt.Key_W, Qt.Key_Up):
            dy = self._pan_speed
        elif key in (Qt.Key_S, Qt.Key_Down):
            dy = -self._pan_speed
        elif key in (Qt.Key_A, Qt.Key_Left):
            dx = self._pan_speed
        elif key in (Qt.Key_D, Qt.Key_Right):
            dx = -self._pan_speed
        else:
            super().keyPressEvent(event)
            return
        
        # Apply pan (in view coordinates)
        self.translate(dx, dy)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for middle-button panning."""
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for panning."""
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.translate(delta.x(), delta.y())
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
    
    def reset_view(self) -> None:
        """Reset view to default position and zoom."""
        self.resetTransform()
        self._current_zoom = 1.0
        self.centerOn(0, 0)
    
    def set_pan_speed(self, speed: int) -> None:
        """Set pan speed for keyboard navigation."""
        self._pan_speed = speed


class WorkspacePanel(QWidget):
    """
    Dynamic workspace panel that changes based on current mode.
    
    Shows relevant controls for Template, Systems, or Routes mode.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(5, 5, 5, 5)
        
        # Mode label
        self._mode_label = QLabel("Mode: None")
        self._mode_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self._layout.addWidget(self._mode_label)
        
        # Container for mode-specific widgets
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._content_widget)
        
        # Stretch at bottom
        self._layout.addStretch()
        
        # Current workspace widgets (to be created per mode)
        self._template_widgets: Optional[QWidget] = None
        self._systems_widgets: Optional[QWidget] = None
        self._routes_widgets: Optional[QWidget] = None
        
        # Callbacks set by main window
        self.on_load_template = None
        self.on_delete_template = None
        self.on_reset_template = None
        self.on_lock_template = None
        self.on_opacity_changed = None
        self.on_scale_changed = None
        
        self.on_rename_system = None
        self.on_delete_system = None
        
        self.on_delete_route = None
        self.on_rename_route = None
    
    def set_mode(self, mode: EditorMode) -> None:
        """Set the current mode and update workspace."""
        # Clear current content
        self._clear_content()
        
        if mode == EditorMode.TEMPLATE:
            self._mode_label.setText("Mode: Template")
            self._create_template_workspace()
        elif mode == EditorMode.SYSTEMS:
            self._mode_label.setText("Mode: Systems")
            self._create_systems_workspace()
        elif mode == EditorMode.ROUTES:
            self._mode_label.setText("Mode: Routes")
            self._create_routes_workspace()
    
    def _clear_content(self) -> None:
        """Clear all widgets from content area."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def _create_template_workspace(self) -> None:
        """Create template mode workspace."""
        group = QGroupBox("Template Controls")
        layout = QVBoxLayout(group)
        
        # Load template button
        load_btn = QPushButton("Load Template...")
        load_btn.clicked.connect(lambda: self.on_load_template and self.on_load_template())
        layout.addWidget(load_btn)
        
        # Delete template button
        delete_btn = QPushButton("Delete Template")
        delete_btn.clicked.connect(lambda: self.on_delete_template and self.on_delete_template())
        layout.addWidget(delete_btn)
        
        # Reset template button
        reset_btn = QPushButton("Reset Transform")
        reset_btn.clicked.connect(lambda: self.on_reset_template and self.on_reset_template())
        layout.addWidget(reset_btn)
        
        # Lock checkbox
        self._lock_btn = QPushButton("Lock Template")
        self._lock_btn.setCheckable(True)
        self._lock_btn.clicked.connect(lambda: self.on_lock_template and self.on_lock_template(self._lock_btn.isChecked()))
        layout.addWidget(self._lock_btn)
        
        # Opacity slider
        opacity_group = QGroupBox("Opacity")
        opacity_layout = QVBoxLayout(opacity_group)
        self._opacity_slider = QSlider(Qt.Horizontal)
        self._opacity_slider.setRange(0, 100)
        self._opacity_slider.setValue(70)
        self._opacity_slider.valueChanged.connect(
            lambda v: self.on_opacity_changed and self.on_opacity_changed(v / 100.0)
        )
        opacity_layout.addWidget(self._opacity_slider)
        layout.addWidget(opacity_group)
        
        # Scale controls
        scale_group = QGroupBox("Scale")
        scale_layout = QVBoxLayout(scale_group)
        self._scale_spin = QDoubleSpinBox()
        self._scale_spin.setRange(0.01, 10.0)
        self._scale_spin.setSingleStep(0.1)
        self._scale_spin.setValue(1.0)
        self._scale_spin.valueChanged.connect(
            lambda v: self.on_scale_changed and self.on_scale_changed(v)
        )
        scale_layout.addWidget(self._scale_spin)
        layout.addWidget(scale_group)
        
        self._content_layout.addWidget(group)
    
    def _create_systems_workspace(self) -> None:
        """Create systems mode workspace."""
        group = QGroupBox("System Controls")
        layout = QVBoxLayout(group)
        
        # Instructions
        info = QLabel("Click to place systems.\nDrag to move systems.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Rename button
        rename_btn = QPushButton("Rename System...")
        rename_btn.clicked.connect(lambda: self.on_rename_system and self.on_rename_system())
        layout.addWidget(rename_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete System")
        delete_btn.clicked.connect(lambda: self.on_delete_system and self.on_delete_system())
        layout.addWidget(delete_btn)
        
        self._content_layout.addWidget(group)
    
    def _create_routes_workspace(self) -> None:
        """Create routes mode workspace."""
        group = QGroupBox("Route Controls")
        layout = QVBoxLayout(group)
        
        # Instructions
        info = QLabel(
            "Click a start system, then an end system to create a route.\n\n"
            "Click a route to select it and show control handles.\n\n"
            "Drag handles to bend the route."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Rename button
        rename_btn = QPushButton("Rename Route...")
        rename_btn.clicked.connect(lambda: self.on_rename_route and self.on_rename_route())
        layout.addWidget(rename_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete Route")
        delete_btn.clicked.connect(lambda: self.on_delete_route and self.on_delete_route())
        layout.addWidget(delete_btn)
        
        self._content_layout.addWidget(group)
    
    def update_template_controls(self, template: Optional[TemplateData]) -> None:
        """Update template controls for selected template."""
        if hasattr(self, '_opacity_slider') and template:
            self._opacity_slider.setValue(int(template.opacity * 100))
        if hasattr(self, '_scale_spin') and template:
            self._scale_spin.setValue(template.scale)
        if hasattr(self, '_lock_btn') and template:
            self._lock_btn.setChecked(template.locked)


class MapEditorWindow(QMainWindow):
    """
    Main window for the Star Wars Map Editor.
    
    Provides:
    - File menu for new/open/save operations
    - Mode toolbar for switching between Template, Systems, and Routes modes
    - Workspace panel with mode-specific controls
    - Map view with zoom and pan navigation
    - Status bar with mode hints
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Star Wars Map Editor")
        self.setMinimumSize(1200, 800)
        
        # Project and state
        self._project = MapProject()
        self._current_file: Optional[str] = None
        self._current_mode = EditorMode.SYSTEMS
        self._modified = False
        
        # Route creation state
        self._route_start_system: Optional[str] = None
        self._route_preview_line = None
        
        # Build UI
        self._setup_scene_and_view()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_workspace()
        self._setup_status_bar()
        
        # Connect signals
        self._connect_signals()
        
        # Set initial mode
        self._set_mode(EditorMode.SYSTEMS)
    
    def _setup_scene_and_view(self) -> None:
        """Set up the graphics scene and view."""
        self._scene = MapScene(self._project)
        self._view = MapView(self._scene)
        
        # Set as central widget
        self.setCentralWidget(self._view)
    
    def _setup_menus(self) -> None:
        """Set up menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("&Export Map Data...", self)
        export_action.triggered.connect(self._export_map_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        self._grid_action = QAction("Show &Grid", self)
        self._grid_action.setCheckable(True)
        self._grid_action.setChecked(True)
        self._grid_action.triggered.connect(self._toggle_grid)
        view_menu.addAction(self._grid_action)
        
        reset_view_action = QAction("&Reset View", self)
        reset_view_action.setShortcut("Home")
        reset_view_action.triggered.connect(self._view.reset_view)
        view_menu.addAction(reset_view_action)
    
    def _setup_toolbar(self) -> None:
        """Set up mode toolbar."""
        toolbar = QToolBar("Mode")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Mode action group (exclusive)
        mode_group = QActionGroup(self)
        mode_group.setExclusive(True)
        
        # Template mode
        template_action = QAction("Template", self)
        template_action.setCheckable(True)
        template_action.triggered.connect(lambda: self._set_mode(EditorMode.TEMPLATE))
        mode_group.addAction(template_action)
        toolbar.addAction(template_action)
        self._template_action = template_action
        
        # Systems mode
        systems_action = QAction("Systems", self)
        systems_action.setCheckable(True)
        systems_action.setChecked(True)
        systems_action.triggered.connect(lambda: self._set_mode(EditorMode.SYSTEMS))
        mode_group.addAction(systems_action)
        toolbar.addAction(systems_action)
        self._systems_action = systems_action
        
        # Routes mode
        routes_action = QAction("Routes", self)
        routes_action.setCheckable(True)
        routes_action.triggered.connect(lambda: self._set_mode(EditorMode.ROUTES))
        mode_group.addAction(routes_action)
        toolbar.addAction(routes_action)
        self._routes_action = routes_action
    
    def _setup_workspace(self) -> None:
        """Set up the workspace dock panel."""
        dock = QDockWidget("Workspace", self)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        
        self._workspace = WorkspacePanel()
        dock.setWidget(self._workspace)
        
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        
        # Connect workspace callbacks
        self._workspace.on_load_template = self._load_template
        self._workspace.on_delete_template = self._delete_selected_template
        self._workspace.on_reset_template = self._reset_selected_template
        self._workspace.on_lock_template = self._lock_selected_template
        self._workspace.on_opacity_changed = self._set_selected_template_opacity
        self._workspace.on_scale_changed = self._set_selected_template_scale
        
        self._workspace.on_rename_system = self._rename_selected_system
        self._workspace.on_delete_system = self._delete_selected_system
        
        self._workspace.on_delete_route = self._delete_selected_route
        self._workspace.on_rename_route = self._rename_selected_route
    
    def _setup_status_bar(self) -> None:
        """Set up status bar."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._update_status_hint()
    
    def _connect_signals(self) -> None:
        """Connect scene and view signals."""
        # Override mouse events on view for mode-specific behavior
        self._view.mousePressEvent = self._on_view_mouse_press
        self._view.mouseMoveEvent = self._on_view_mouse_move
        self._view.mouseReleaseEvent = self._on_view_mouse_release
    
    # ---------- Mode handling ----------
    
    def _set_mode(self, mode: EditorMode) -> None:
        """Set the current editor mode."""
        self._current_mode = mode
        self._workspace.set_mode(mode)
        self._update_status_hint()
        
        # Clear route creation state when switching modes
        self._cancel_route_creation()
        
        # Clear selection when switching modes
        self._scene.clearSelection()
    
    def _update_status_hint(self) -> None:
        """Update status bar with mode-specific hint."""
        hints = {
            EditorMode.TEMPLATE: "Template mode: Load background images to align. Drag to position, use controls to adjust.",
            EditorMode.SYSTEMS: "Systems mode: Click to place systems. Drag to move. Right-click for options.",
            EditorMode.ROUTES: "Routes mode: Click a start system, then an end system. Drag control points to bend the route.",
        }
        self._status_bar.showMessage(hints.get(self._current_mode, ""))
    
    # ---------- Mouse event handling ----------
    
    def _on_view_mouse_press(self, event: QMouseEvent) -> None:
        """Handle mouse press based on current mode."""
        # Always allow middle button panning
        if event.button() == Qt.MiddleButton:
            MapView.mousePressEvent(self._view, event)
            return
        
        if event.button() != Qt.LeftButton:
            MapView.mousePressEvent(self._view, event)
            return
        
        scene_pos = self._view.mapToScene(event.pos())
        
        if self._current_mode == EditorMode.SYSTEMS:
            self._handle_systems_click(scene_pos, event)
        elif self._current_mode == EditorMode.ROUTES:
            self._handle_routes_click(scene_pos, event)
        else:
            MapView.mousePressEvent(self._view, event)
    
    def _on_view_mouse_move(self, event: QMouseEvent) -> None:
        """Handle mouse move based on current mode."""
        if self._view._panning:
            MapView.mouseMoveEvent(self._view, event)
            return
        
        # Update route preview line if in route creation mode
        if self._current_mode == EditorMode.ROUTES and self._route_start_system:
            # Could add preview line drawing here
            pass
        
        MapView.mouseMoveEvent(self._view, event)
    
    def _on_view_mouse_release(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        MapView.mouseReleaseEvent(self._view, event)
    
    def _handle_systems_click(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        """Handle click in systems mode."""
        # Check if clicking on existing item
        items = self._scene.items(scene_pos)
        system_item = None
        for item in items:
            if isinstance(item, SystemItem):
                system_item = item
                break
        
        if system_item:
            # Select existing system
            MapView.mousePressEvent(self._view, event)
        else:
            # Create new system at click position
            name, ok = QInputDialog.getText(
                self, "New System", "System name:",
                text=f"System {len(self._project.systems) + 1}"
            )
            if ok and name:
                data = self._project.create_system(name=name, x=scene_pos.x(), y=scene_pos.y())
                self._scene._create_system_item(data)
                self._modified = True
    
    def _handle_routes_click(self, scene_pos: QPointF, event: QMouseEvent) -> None:
        """Handle click in routes mode."""
        # Check if clicking on a route (for selection)
        items = self._scene.items(scene_pos)
        
        # First check for system clicks (for route creation)
        system_item = None
        route_item = None
        
        for item in items:
            if isinstance(item, SystemItem) and system_item is None:
                system_item = item
            elif isinstance(item, RouteItem) and route_item is None:
                route_item = item
        
        if system_item:
            # Handle route creation
            if self._route_start_system is None:
                # Start new route
                self._route_start_system = system_item.system_id
                self._status_bar.showMessage(f"Route started from {system_item.data.name}. Click end system...")
            else:
                # Complete route
                end_system_id = system_item.system_id
                
                if end_system_id == self._route_start_system:
                    self._status_bar.showMessage("Cannot create route to same system. Click a different system.")
                    return
                
                # Create the route
                start_sys = self._project.get_system(self._route_start_system)
                end_sys = self._project.get_system(end_system_id)
                
                if start_sys and end_sys:
                    # Calculate a default control point at midpoint
                    mid_x = (start_sys.x + end_sys.x) / 2
                    mid_y = (start_sys.y + end_sys.y) / 2
                    control_points = [QPointF(mid_x, mid_y)]
                    
                    route_data = self._project.create_route(
                        start_system_id=self._route_start_system,
                        end_system_id=end_system_id,
                        control_points=control_points
                    )
                    
                    if route_data:
                        self._scene._create_route_item(route_data)
                        self._modified = True
                        self._status_bar.showMessage(f"Route created: {start_sys.name} → {end_sys.name}")
                
                self._route_start_system = None
        elif route_item:
            # Select route (let default handling take over)
            MapView.mousePressEvent(self._view, event)
        else:
            # Click on empty space - cancel route creation
            if self._route_start_system:
                self._cancel_route_creation()
            else:
                MapView.mousePressEvent(self._view, event)
    
    def _cancel_route_creation(self) -> None:
        """Cancel ongoing route creation."""
        if self._route_start_system:
            self._route_start_system = None
            self._update_status_hint()
    
    # ---------- File operations ----------
    
    def _new_project(self) -> None:
        """Create a new empty project."""
        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes to current project?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                if not self._save_project():
                    return
            elif reply == QMessageBox.Cancel:
                return
        
        self._project = MapProject()
        self._scene.set_project(self._project)
        self._current_file = None
        self._modified = False
        self.setWindowTitle("Star Wars Map Editor")
    
    def _open_project(self) -> None:
        """Open an existing project."""
        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes to current project?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                if not self._save_project():
                    return
            elif reply == QMessageBox.Cancel:
                return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project",
            "", get_project_file_filter()
        )
        
        if file_path:
            project = load_project(file_path)
            if project:
                self._project = project
                self._scene.set_project(project)
                self._current_file = file_path
                self._modified = False
                self.setWindowTitle(f"Star Wars Map Editor - {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load project.")
    
    def _save_project(self) -> bool:
        """Save the current project."""
        if self._current_file:
            if save_project(self._project, self._current_file):
                self._modified = False
                return True
            else:
                QMessageBox.warning(self, "Error", "Failed to save project.")
                return False
        else:
            return self._save_project_as()
    
    def _save_project_as(self) -> bool:
        """Save the project to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project",
            "", get_project_file_filter()
        )
        
        if file_path:
            if save_project(self._project, file_path):
                self._current_file = file_path
                self._modified = False
                self.setWindowTitle(f"Star Wars Map Editor - {os.path.basename(file_path)}")
                return True
            else:
                QMessageBox.warning(self, "Error", "Failed to save project.")
        return False
    
    def _export_map_data(self) -> None:
        """Export map data (placeholder for future functionality)."""
        QMessageBox.information(
            self, "Export",
            "Export functionality will be implemented in a future update."
        )
    
    # ---------- View operations ----------
    
    def _toggle_grid(self) -> None:
        """Toggle grid visibility."""
        self._scene.set_grid_visible(self._grid_action.isChecked())
    
    # ---------- Template operations ----------
    
    def _load_template(self) -> None:
        """Load a template image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Template Image",
            "", "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        
        if file_path:
            data = self._project.create_template(file_path)
            item = self._scene.add_template(data)
            if item.pixmap().isNull():
                QMessageBox.warning(self, "Error", "Failed to load image.")
                self._scene.remove_template(data.id)
            else:
                self._modified = True
    
    def _get_selected_template(self) -> Optional[TemplateItem]:
        """Get the currently selected template item."""
        for item in self._scene.selectedItems():
            if isinstance(item, TemplateItem):
                return item
        return None
    
    def _delete_selected_template(self) -> None:
        """Delete the selected template."""
        item = self._get_selected_template()
        if item:
            self._scene.remove_template(item.template_id)
            self._modified = True
    
    def _reset_selected_template(self) -> None:
        """Reset the selected template's transform."""
        item = self._get_selected_template()
        if item:
            item.reset_transform()
            self._modified = True
    
    def _lock_selected_template(self, locked: bool) -> None:
        """Lock/unlock the selected template."""
        item = self._get_selected_template()
        if item:
            item.set_locked(locked)
            self._modified = True
    
    def _set_selected_template_opacity(self, opacity: float) -> None:
        """Set the selected template's opacity."""
        item = self._get_selected_template()
        if item:
            item.set_template_opacity(opacity)
            self._modified = True
    
    def _set_selected_template_scale(self, scale: float) -> None:
        """Set the selected template's scale."""
        item = self._get_selected_template()
        if item:
            item.set_template_scale(scale)
            self._modified = True
    
    # ---------- System operations ----------
    
    def _get_selected_system(self) -> Optional[SystemItem]:
        """Get the currently selected system item."""
        for item in self._scene.selectedItems():
            if isinstance(item, SystemItem):
                return item
        return None
    
    def _rename_selected_system(self) -> None:
        """Rename the selected system."""
        item = self._get_selected_system()
        if item:
            name, ok = QInputDialog.getText(
                self, "Rename System",
                "New name:",
                text=item.data.name
            )
            if ok and name:
                item.set_name(name)
                self._modified = True
    
    def _delete_selected_system(self) -> None:
        """Delete the selected system."""
        item = self._get_selected_system()
        if item:
            reply = QMessageBox.question(
                self, "Delete System",
                f"Delete system '{item.data.name}'?\nThis will also delete connected routes.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._scene.remove_system(item.system_id)
                self._modified = True
    
    # ---------- Route operations ----------
    
    def _get_selected_route(self) -> Optional[RouteItem]:
        """Get the currently selected route item."""
        for item in self._scene.selectedItems():
            if isinstance(item, RouteItem):
                return item
        return None
    
    def _rename_selected_route(self) -> None:
        """Rename the selected route."""
        item = self._get_selected_route()
        if item:
            name, ok = QInputDialog.getText(
                self, "Rename Route",
                "New name:",
                text=item.data.name
            )
            if ok and name:
                item.set_name(name)
                self._modified = True
    
    def _delete_selected_route(self) -> None:
        """Delete the selected route."""
        item = self._get_selected_route()
        if item:
            reply = QMessageBox.question(
                self, "Delete Route",
                f"Delete route '{item.data.name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._scene.remove_route(item.route_id)
                self._modified = True
    
    # ---------- Close handling ----------
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                if self._save_project():
                    event.accept()
                else:
                    event.ignore()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point for the Star Wars Map Editor."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MapEditorWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
