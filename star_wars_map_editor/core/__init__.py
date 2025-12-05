"""
Core module for Star Wars Map Editor.

Contains data models and logic for systems, routes, templates, and project management.
"""

from .systems import SystemData, SystemItem
from .routes import RouteData, RouteItem, RouteHandleItem
from .templates import TemplateData, TemplateItem
from .project_model import MapProject
from .project_io import save_project, load_project

__all__ = [
    'SystemData', 'SystemItem',
    'RouteData', 'RouteItem', 'RouteHandleItem',
    'TemplateData', 'TemplateItem',
    'MapProject',
    'save_project', 'load_project',
]
