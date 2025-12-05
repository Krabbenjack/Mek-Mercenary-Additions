"""
Project model module for Star Wars Map Editor.

Contains the MapProject class that manages all project data.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable
import uuid

from PyQt5.QtCore import QPointF

from .systems import SystemData
from .routes import RouteData
from .templates import TemplateData


@dataclass
class MapProject:
    """
    Main project model containing all map data.
    
    Manages systems, routes, and templates. Provides methods for
    adding, removing, and querying items.
    
    Attributes:
        name: Project name.
        version: Project format version.
        systems: Dictionary of system ID to SystemData.
        routes: Dictionary of route ID to RouteData.
        templates: Dictionary of template ID to TemplateData.
    """
    name: str = "Untitled Project"
    version: str = "1.0"
    systems: Dict[str, SystemData] = field(default_factory=dict)
    routes: Dict[str, RouteData] = field(default_factory=dict)
    templates: Dict[str, TemplateData] = field(default_factory=dict)
    
    # Internal counter for auto-naming
    _route_counter: int = field(default=0, repr=False)
    _system_counter: int = field(default=0, repr=False)
    
    # ---------- Systems ----------
    
    def add_system(self, system: SystemData) -> SystemData:
        """
        Add a system to the project.
        
        Args:
            system: The SystemData to add.
            
        Returns:
            The added SystemData.
        """
        self.systems[system.id] = system
        return system
    
    def create_system(
        self,
        name: Optional[str] = None,
        x: float = 0.0,
        y: float = 0.0,
        **kwargs
    ) -> SystemData:
        """
        Create and add a new system.
        
        Args:
            name: System name. If None, auto-generates.
            x: X position.
            y: Y position.
            **kwargs: Additional SystemData attributes.
            
        Returns:
            The created SystemData.
        """
        if name is None:
            self._system_counter += 1
            name = f"System {self._system_counter}"
        
        system = SystemData(name=name, x=x, y=y, **kwargs)
        return self.add_system(system)
    
    def remove_system(self, system_id: str) -> Optional[SystemData]:
        """
        Remove a system from the project.
        
        Also removes any routes connected to this system.
        
        Args:
            system_id: The ID of the system to remove.
            
        Returns:
            The removed SystemData, or None if not found.
        """
        system = self.systems.pop(system_id, None)
        
        if system is not None:
            # Remove routes connected to this system
            routes_to_remove = [
                rid for rid, route in self.routes.items()
                if route.start_system_id == system_id or route.end_system_id == system_id
            ]
            for rid in routes_to_remove:
                self.routes.pop(rid, None)
        
        return system
    
    def get_system(self, system_id: str) -> Optional[SystemData]:
        """Get a system by ID."""
        return self.systems.get(system_id)
    
    def get_system_position(self, system_id: str) -> Optional[QPointF]:
        """
        Get a system's position by ID.
        
        Args:
            system_id: The system ID.
            
        Returns:
            QPointF position, or None if system not found.
        """
        system = self.systems.get(system_id)
        if system is not None:
            return system.position()
        return None
    
    def find_system_at(self, pos: QPointF, radius: float = 30.0) -> Optional[SystemData]:
        """
        Find a system near the given position.
        
        Args:
            pos: The position to search near.
            radius: Maximum distance to consider.
            
        Returns:
            The nearest SystemData within radius, or None.
        """
        best_system = None
        best_dist = radius
        
        for system in self.systems.values():
            dx = system.x - pos.x()
            dy = system.y - pos.y()
            dist = (dx * dx + dy * dy) ** 0.5
            
            if dist < best_dist:
                best_dist = dist
                best_system = system
        
        return best_system
    
    # ---------- Routes ----------
    
    def add_route(self, route: RouteData) -> RouteData:
        """
        Add a route to the project.
        
        Args:
            route: The RouteData to add.
            
        Returns:
            The added RouteData.
        """
        self.routes[route.id] = route
        return route
    
    def create_route(
        self,
        start_system_id: str,
        end_system_id: str,
        name: Optional[str] = None,
        control_points: Optional[List[QPointF]] = None,
        **kwargs
    ) -> Optional[RouteData]:
        """
        Create and add a new route between two systems.
        
        Args:
            start_system_id: ID of the starting system.
            end_system_id: ID of the ending system.
            name: Route name. If None, auto-generates.
            control_points: Optional list of control points.
            **kwargs: Additional RouteData attributes.
            
        Returns:
            The created RouteData, or None if either system doesn't exist.
        """
        # Validate systems exist
        if start_system_id not in self.systems or end_system_id not in self.systems:
            return None
        
        if name is None:
            self._route_counter += 1
            name = f"Route {self._route_counter}"
        
        route = RouteData(
            name=name,
            start_system_id=start_system_id,
            end_system_id=end_system_id,
            control_points=control_points or [],
            **kwargs
        )
        return self.add_route(route)
    
    def remove_route(self, route_id: str) -> Optional[RouteData]:
        """
        Remove a route from the project.
        
        Args:
            route_id: The ID of the route to remove.
            
        Returns:
            The removed RouteData, or None if not found.
        """
        return self.routes.pop(route_id, None)
    
    def get_route(self, route_id: str) -> Optional[RouteData]:
        """Get a route by ID."""
        return self.routes.get(route_id)
    
    def get_routes_for_system(self, system_id: str) -> List[RouteData]:
        """
        Get all routes connected to a system.
        
        Args:
            system_id: The system ID.
            
        Returns:
            List of RouteData connected to the system.
        """
        return [
            route for route in self.routes.values()
            if route.start_system_id == system_id or route.end_system_id == system_id
        ]
    
    # ---------- Templates ----------
    
    def add_template(self, template: TemplateData) -> TemplateData:
        """
        Add a template to the project.
        
        Args:
            template: The TemplateData to add.
            
        Returns:
            The added TemplateData.
        """
        self.templates[template.id] = template
        return template
    
    def create_template(
        self,
        file_path: str,
        name: Optional[str] = None,
        **kwargs
    ) -> TemplateData:
        """
        Create and add a new template.
        
        Args:
            file_path: Path to the template image file.
            name: Template name. If None, derives from filename.
            **kwargs: Additional TemplateData attributes.
            
        Returns:
            The created TemplateData.
        """
        if name is None:
            import os
            name = os.path.splitext(os.path.basename(file_path))[0]
        
        template = TemplateData(name=name, file_path=file_path, **kwargs)
        return self.add_template(template)
    
    def remove_template(self, template_id: str) -> Optional[TemplateData]:
        """
        Remove a template from the project.
        
        Args:
            template_id: The ID of the template to remove.
            
        Returns:
            The removed TemplateData, or None if not found.
        """
        return self.templates.pop(template_id, None)
    
    def get_template(self, template_id: str) -> Optional[TemplateData]:
        """Get a template by ID."""
        return self.templates.get(template_id)
    
    # ---------- Serialization ----------
    
    def to_dict(self) -> dict:
        """Convert the project to a dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "systems": {sid: s.to_dict() for sid, s in self.systems.items()},
            "routes": {rid: r.to_dict() for rid, r in self.routes.items()},
            "templates": {tid: t.to_dict() for tid, t in self.templates.items()},
            "_route_counter": self._route_counter,
            "_system_counter": self._system_counter,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MapProject":
        """Create a project from a dictionary."""
        project = cls(
            name=data.get("name", "Untitled Project"),
            version=data.get("version", "1.0"),
        )
        
        # Load systems
        systems_data = data.get("systems", {})
        for sid, sdata in systems_data.items():
            system = SystemData.from_dict(sdata)
            project.systems[sid] = system
        
        # Load routes
        routes_data = data.get("routes", {})
        for rid, rdata in routes_data.items():
            route = RouteData.from_dict(rdata)
            project.routes[rid] = route
        
        # Load templates
        templates_data = data.get("templates", {})
        for tid, tdata in templates_data.items():
            template = TemplateData.from_dict(tdata)
            project.templates[tid] = template
        
        # Restore counters
        project._route_counter = data.get("_route_counter", 0)
        project._system_counter = data.get("_system_counter", 0)
        
        return project
    
    def clear(self) -> None:
        """Clear all project data."""
        self.systems.clear()
        self.routes.clear()
        self.templates.clear()
        self._route_counter = 0
        self._system_counter = 0
        self.name = "Untitled Project"
