"""
Module automation pour ARIA
Gestion du contrôle système, applications et fenêtres Windows
"""

from .system_controller import SystemController, AppInfo
from .window_manager import WindowManager, WindowInfo

__all__ = [
    'SystemController',
    'AppInfo', 
    'WindowManager',
    'WindowInfo'
]
