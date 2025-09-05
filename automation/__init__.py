"""
Module automation pour ARIA
Gestion du contrôle système, applications, fenêtres et automation web
"""

from .system_controller import SystemController, AppInfo
from .window_manager import WindowManager, WindowInfo

try:
    from .web_automation import WebAutomation, WebElement, SearchResult
except ImportError:
    WebAutomation = None
    WebElement = None
    SearchResult = None

try:
    from .task_executor import AITaskExecutor, TaskStep, TaskResult
except ImportError:
    AITaskExecutor = None
    TaskStep = None
    TaskResult = None

__all__ = [
    'SystemController',
    'AppInfo', 
    'WindowManager',
    'WindowInfo',
    'WebAutomation',
    'WebElement',
    'SearchResult',
    'AITaskExecutor',
    'TaskStep',
    'TaskResult'
]
