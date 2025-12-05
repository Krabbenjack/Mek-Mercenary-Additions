"""
Project I/O module for Star Wars Map Editor.

Contains functions for saving and loading project files (.swmproj).
"""

import json
import logging
import os
from typing import Optional, Tuple

from .project_model import MapProject


# Set up logging for this module
logger = logging.getLogger(__name__)

# Project file extension
PROJECT_EXTENSION = ".swmproj"


class ProjectIOError(Exception):
    """Exception raised for project I/O errors."""
    pass


def save_project(project: MapProject, file_path: str) -> Tuple[bool, str]:
    """
    Save a project to a .swmproj file.
    
    Args:
        project: The MapProject to save.
        file_path: Path to save to. Will add .swmproj extension if missing.
        
    Returns:
        Tuple of (success: bool, error_message: str). 
        error_message is empty on success.
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
        
        return True, ""
        
    except (OSError, IOError) as e:
        error_msg = f"Failed to write file: {e}"
        logger.error(error_msg)
        return False, error_msg
    except (TypeError, ValueError) as e:
        error_msg = f"Failed to serialize project data: {e}"
        logger.error(error_msg)
        return False, error_msg


def load_project(file_path: str) -> Tuple[Optional[MapProject], str]:
    """
    Load a project from a .swmproj file.
    
    Args:
        file_path: Path to the project file.
        
    Returns:
        Tuple of (project: MapProject or None, error_message: str).
        error_message is empty on success.
    """
    if not os.path.exists(file_path):
        error_msg = f"Project file not found: {file_path}"
        logger.error(error_msg)
        return None, error_msg
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        project = MapProject.from_dict(data)
        return project, ""
        
    except (OSError, IOError) as e:
        error_msg = f"Failed to read file: {e}"
        logger.error(error_msg)
        return None, error_msg
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON format: {e}"
        logger.error(error_msg)
        return None, error_msg
    except (KeyError, TypeError) as e:
        error_msg = f"Invalid project format: {e}"
        logger.error(error_msg)
        return None, error_msg


def get_project_file_filter() -> str:
    """Get the file filter string for project files."""
    return f"Star Wars Map Project (*{PROJECT_EXTENSION});;All Files (*)"
