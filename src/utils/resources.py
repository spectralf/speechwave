"""
Utility for resolving paths to bundled resources.
"""

import sys
import os
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """
    Get the absolute path to a resource, accounting for PyInstaller's bundling.

    Args:
        relative_path: The path relative to the application root or bundle.

    Returns:
        Path: The absolute path to the resource.
    """
    # Check if running as a PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running as a script - assume resource relative to project root
        # This might need adjustment depending on where resources are placed
        # Assuming project root is parent of 'src'
        base_path = Path(__file__).resolve().parent.parent.parent 
        
    resource_path = base_path / relative_path
    
    if not resource_path.exists():
        # Fallback or raise error if resource not found
        # For now, raise an error to make missing resources obvious
        raise FileNotFoundError(f"Resource not found at expected location: {resource_path}")
        
    return resource_path 