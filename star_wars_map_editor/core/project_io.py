"""
Project I/O module for Star Wars Map Editor.

Contains functions for saving and loading project files (.swmproj).
"""

import json
import os
from typing import Optional

from .project_model import MapProject


# Project file extension
PROJECT_EXTENSION = ".swmproj"


def save_project(project: MapProject, file_path: str) -> bool:
    """
    Save a project to a .swmproj file.
    
    Args:
        project: The MapProject to save.
        file_path: Path to save to. Will add .swmproj extension if missing.
        
    Returns:
        True if save succeeded, False otherwise.
    """
    # Ensure proper extension
    if not file_path.endswith(PROJECT_EXTENSION):
        file_path += PROJECT_EXTENSION
    
    try:
        data = project.to_dict()
        
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except (OSError, IOError, TypeError, ValueError) as e:
        print(f"Error saving project: {e}")
        return False


def load_project(file_path: str) -> Optional[MapProject]:
    """
    Load a project from a .swmproj file.
    
    Args:
        file_path: Path to the project file.
        
    Returns:
        The loaded MapProject, or None if loading failed.
    """
    if not os.path.exists(file_path):
        print(f"Project file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        project = MapProject.from_dict(data)
        return project
        
    except (OSError, IOError, json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error loading project: {e}")
        return None


def get_project_file_filter() -> str:
    """Get the file filter string for project files."""
    return f"Star Wars Map Project (*{PROJECT_EXTENSION});;All Files (*)"
