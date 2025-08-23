"""
Module de gestion des fenêtres pour ARIA
Contrôle avancé des fenêtres Windows : focus, redimensionnement, 
positionnement, capture d'écran, etc.
"""

import ctypes
from ctypes import wintypes, windll
import win32gui
import win32con
import win32api
import win32process
import psutil
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from PIL import Image, ImageGrab
import os

logger = logging.getLogger(__name__)

# Constantes Windows
WS_MAXIMIZE = 0x1000000
WS_MINIMIZE = 0x20000000
SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_SHOWMAXIMIZED = 3
SW_SHOWNOACTIVATE = 4
SW_SHOW = 5
SW_MINIMIZE = 6
SW_SHOWMINNOACTIVE = 7
SW_SHOWNA = 8
SW_RESTORE = 9

@dataclass
class WindowInfo:
    """Informations sur une fenêtre"""
    hwnd: int
    title: str
    class_name: str
    pid: int
    process_name: str
    rect: Tuple[int, int, int, int]  # (left, top, right, bottom)
    is_visible: bool
    is_minimized: bool
    is_maximized: bool
    is_active: bool

class WindowManager:
    """Gestionnaire des fenêtres Windows"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.windows_cache = {}
        self.last_update = 0
        
        # Initialise les APIs Windows
        self.user32 = windll.user32
        self.kernel32 = windll.kernel32
        
    def refresh_windows_cache(self):
        """Actualise le cache des fenêtres"""
        current_time = time.time()
        
        # Actualise seulement si nécessaire (toutes les 2 secondes max)
        if current_time - self.last_update < 2:
            return
            
        self.windows_cache = {}
        
        def enum_windows_callback(hwnd, lparam):
            try:
                # Vérifie si la fenêtre est valide
                if not win32gui.IsWindow(hwnd):
                    return True
                    
                # Récupère les informations de base
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                is_visible = win32gui.IsWindowVisible(hwnd)
                
                # Filtre les fenêtres sans titre et invisibles
                if not title.strip() and not is_visible:
                    return True
                
                # Récupère le processus
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = process.name()
                except:
                    pid = 0
                    process_name = "Unknown"
                
                # Récupère la position et taille
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                except:
                    rect = (0, 0, 0, 0)
                
                # Vérifie l'état de la fenêtre
                placement = win32gui.GetWindowPlacement(hwnd)
                is_minimized = placement[1] == win32con.SW_SHOWMINIMIZED
                is_maximized = placement[1] == win32con.SW_SHOWMAXIMIZED
                is_active = win32gui.GetForegroundWindow() == hwnd
                
                # Crée l'objet WindowInfo
                window_info = WindowInfo(
                    hwnd=hwnd,
                    title=title,
                    class_name=class_name,
                    pid=pid,
                    process_name=process_name,
                    rect=rect,
                    is_visible=is_visible,
                    is_minimized=is_minimized,
                    is_maximized=is_maximized,
                    is_active=is_active
                )
                
                self.windows_cache[hwnd] = window_info
                
            except Exception as e:
                logger.debug(f"Erreur énumération fenêtre {hwnd}: {e}")
                
            return True
        
        try:
            win32gui.EnumWindows(enum_windows_callback, 0)
            self.last_update = current_time
            logger.debug(f"Cache actualisé : {len(self.windows_cache)} fenêtres")
        except Exception as e:
            logger.error(f"Erreur actualisation cache : {e}")
    
    def get_all_windows(self) -> List[WindowInfo]:
        """Retourne toutes les fenêtres"""
        self.refresh_windows_cache()
        return list(self.windows_cache.values())
    
    def get_visible_windows(self) -> List[WindowInfo]:
        """Retourne seulement les fenêtres visibles"""
        return [w for w in self.get_all_windows() if w.is_visible and w.title.strip()]
    
    def find_windows_by_title(self, title_pattern: str, exact_match: bool = False) -> List[WindowInfo]:
        """Trouve des fenêtres par titre"""
        windows = []
        title_pattern = title_pattern.lower()
        
        for window in self.get_all_windows():
            window_title = window.title.lower()
            
            if exact_match:
                if window_title == title_pattern:
                    windows.append(window)
            else:
                if title_pattern in window_title:
                    windows.append(window)
        
        return windows
    
    def find_windows_by_process(self, process_name: str) -> List[WindowInfo]:
        """Trouve des fenêtres par nom de processus"""
        windows = []
        process_name = process_name.lower()
        
        for window in self.get_all_windows():
            if process_name in window.process_name.lower():
                windows.append(window)
        
        return windows
    
    def find_window_by_class(self, class_name: str) -> List[WindowInfo]:
        """Trouve des fenêtres par nom de classe"""
        windows = []
        class_name = class_name.lower()
        
        for window in self.get_all_windows():
            if class_name in window.class_name.lower():
                windows.append(window)
        
        return windows
    
    def activate_window(self, window: WindowInfo) -> bool:
        """Active une fenêtre (lui donne le focus)"""
        try:
            hwnd = window.hwnd
            
            # Vérifie si la fenêtre existe encore
            if not win32gui.IsWindow(hwnd):
                logger.warning(f"Fenêtre {hwnd} n'existe plus")
                return False
            
            # Restaure la fenêtre si elle est minimisée
            if window.is_minimized:
                win32gui.ShowWindow(hwnd, SW_RESTORE)
                time.sleep(0.1)
            
            # Amène la fenêtre au premier plan
            win32gui.SetForegroundWindow(hwnd)
            win32gui.BringWindowToTop(hwnd)
            
            logger.info(f"Fenêtre activée : {window.title}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur activation fenêtre : {e}")
            return False
    
    def minimize_window(self, window: WindowInfo) -> bool:
        """Minimise une fenêtre"""
        try:
            win32gui.ShowWindow(window.hwnd, SW_MINIMIZE)
            logger.info(f"Fenêtre minimisée : {window.title}")
            return True
        except Exception as e:
            logger.error(f"Erreur minimisation fenêtre : {e}")
            return False
    
    def maximize_window(self, window: WindowInfo) -> bool:
        """Maximise une fenêtre"""
        try:
            win32gui.ShowWindow(window.hwnd, SW_MAXIMIZE)
            logger.info(f"Fenêtre maximisée : {window.title}")
            return True
        except Exception as e:
            logger.error(f"Erreur maximisation fenêtre : {e}")
            return False
    
    def restore_window(self, window: WindowInfo) -> bool:
        """Restaure une fenêtre à sa taille normale"""
        try:
            win32gui.ShowWindow(window.hwnd, SW_RESTORE)
            logger.info(f"Fenêtre restaurée : {window.title}")
            return True
        except Exception as e:
            logger.error(f"Erreur restauration fenêtre : {e}")
            return False
    
    def close_window(self, window: WindowInfo, force: bool = False) -> bool:
        """Ferme une fenêtre"""
        try:
            if force:
                # Fermeture forcée
                win32gui.PostMessage(window.hwnd, win32con.WM_CLOSE, 0, 0)
            else:
                # Fermeture normale
                win32gui.SendMessage(window.hwnd, win32con.WM_SYSCOMMAND, win32con.SC_CLOSE, 0)
            
            logger.info(f"Fenêtre fermée : {window.title}")
            return True
        except Exception as e:
            logger.error(f"Erreur fermeture fenêtre : {e}")
            return False
    
    def move_window(self, window: WindowInfo, x: int, y: int) -> bool:
        """Déplace une fenêtre à une position spécifique"""
        try:
            # Récupère la taille actuelle
            left, top, right, bottom = window.rect
            width = right - left
            height = bottom - top
            
            # Déplace la fenêtre
            win32gui.SetWindowPos(
                window.hwnd,
                0,  # hwndInsertAfter
                x, y,  # nouvelle position
                width, height,  # taille inchangée
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )
            
            logger.info(f"Fenêtre déplacée : {window.title} -> ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Erreur déplacement fenêtre : {e}")
            return False
    
    def resize_window(self, window: WindowInfo, width: int, height: int) -> bool:
        """Redimensionne une fenêtre"""
        try:
            # Récupère la position actuelle
            left, top, _, _ = window.rect
            
            # Redimensionne la fenêtre
            win32gui.SetWindowPos(
                window.hwnd,
                0,  # hwndInsertAfter
                left, top,  # position inchangée
                width, height,  # nouvelle taille
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )
            
            logger.info(f"Fenêtre redimensionnée : {window.title} -> {width}x{height}")
            return True
        except Exception as e:
            logger.error(f"Erreur redimensionnement fenêtre : {e}")
            return False
    
    def move_and_resize_window(self, window: WindowInfo, x: int, y: int, width: int, height: int) -> bool:
        """Déplace et redimensionne une fenêtre en une seule opération"""
        try:
            win32gui.SetWindowPos(
                window.hwnd,
                0,  # hwndInsertAfter
                x, y,  # nouvelle position
                width, height,  # nouvelle taille
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )
            
            logger.info(f"Fenêtre repositionnée : {window.title} -> ({x}, {y}, {width}x{height})")
            return True
        except Exception as e:
            logger.error(f"Erreur repositionnement fenêtre : {e}")
            return False
    
    def center_window(self, window: WindowInfo, monitor_index: int = 0) -> bool:
        """Centre une fenêtre sur l'écran spécifié"""
        try:
            # Récupère les informations de l'écran
            monitors = win32api.EnumDisplayMonitors()
            
            if monitor_index >= len(monitors):
                monitor_index = 0
            
            monitor_info = win32api.GetMonitorInfo(monitors[monitor_index][0])
            monitor_rect = monitor_info['Monitor']
            
            screen_width = monitor_rect[2] - monitor_rect[0]
            screen_height = monitor_rect[3] - monitor_rect[1]
            
            # Récupère la taille de la fenêtre
            left, top, right, bottom = window.rect
            window_width = right - left
            window_height = bottom - top
            
            # Calcule la position centrée
            center_x = monitor_rect[0] + (screen_width - window_width) // 2
            center_y = monitor_rect[1] + (screen_height - window_height) // 2
            
            # Déplace la fenêtre
            return self.move_window(window, center_x, center_y)
            
        except Exception as e:
            logger.error(f"Erreur centrage fenêtre : {e}")
            return False
    
    def tile_windows_horizontal(self, windows: List[WindowInfo]) -> bool:
        """Arrange les fenêtres horizontalement"""
        try:
            if not windows:
                return False
            
            # Récupère les informations de l'écran principal
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            
            # Calcule la taille de chaque fenêtre
            window_width = screen_width // len(windows)
            window_height = screen_height
            
            # Positionne chaque fenêtre
            for i, window in enumerate(windows):
                x = i * window_width
                y = 0
                
                if not self.move_and_resize_window(window, x, y, window_width, window_height):
                    return False
            
            logger.info(f"{len(windows)} fenêtres arrangées horizontalement")
            return True
            
        except Exception as e:
            logger.error(f"Erreur arrangement horizontal : {e}")
            return False
    
    def tile_windows_vertical(self, windows: List[WindowInfo]) -> bool:
        """Arrange les fenêtres verticalement"""
        try:
            if not windows:
                return False
            
            # Récupère les informations de l'écran principal
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            
            # Calcule la taille de chaque fenêtre
            window_width = screen_width
            window_height = screen_height // len(windows)
            
            # Positionne chaque fenêtre
            for i, window in enumerate(windows):
                x = 0
                y = i * window_height
                
                if not self.move_and_resize_window(window, x, y, window_width, window_height):
                    return False
            
            logger.info(f"{len(windows)} fenêtres arrangées verticalement")
            return True
            
        except Exception as e:
            logger.error(f"Erreur arrangement vertical : {e}")
            return False
    
    def tile_windows_grid(self, windows: List[WindowInfo], columns: int = None) -> bool:
        """Arrange les fenêtres en grille"""
        try:
            if not windows:
                return False
            
            num_windows = len(windows)
            
            if columns is None:
                # Calcule automatiquement le nombre de colonnes
                import math
                columns = math.ceil(math.sqrt(num_windows))
            
            rows = math.ceil(num_windows / columns)
            
            # Récupère les informations de l'écran principal
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            
            # Calcule la taille de chaque fenêtre
            window_width = screen_width // columns
            window_height = screen_height // rows
            
            # Positionne chaque fenêtre
            for i, window in enumerate(windows):
                row = i // columns
                col = i % columns
                
                x = col * window_width
                y = row * window_height
                
                if not self.move_and_resize_window(window, x, y, window_width, window_height):
                    return False
            
            logger.info(f"{len(windows)} fenêtres arrangées en grille {columns}x{rows}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur arrangement grille : {e}")
            return False
    
    def capture_window_screenshot(self, window: WindowInfo, save_path: str = None) -> Optional[Image.Image]:
        """Capture une image de la fenêtre"""
        try:
            # Active la fenêtre si elle n'est pas visible
            if not window.is_visible or window.is_minimized:
                self.activate_window(window)
                time.sleep(0.5)
            
            # Récupère les coordonnées de la fenêtre
            left, top, right, bottom = window.rect
            
            # Capture la région
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            
            # Sauvegarde si un chemin est fourni
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                screenshot.save(save_path)
                logger.info(f"Screenshot sauvé : {save_path}")
            
            return screenshot
            
        except Exception as e:
            logger.error(f"Erreur capture fenêtre : {e}")
            return None
    
    def get_active_window(self) -> Optional[WindowInfo]:
        """Retourne la fenêtre actuellement active"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            self.refresh_windows_cache()
            return self.windows_cache.get(hwnd)
        except Exception as e:
            logger.error(f"Erreur récupération fenêtre active : {e}")
            return None
    
    def hide_window(self, window: WindowInfo) -> bool:
        """Cache une fenêtre"""
        try:
            win32gui.ShowWindow(window.hwnd, SW_HIDE)
            logger.info(f"Fenêtre cachée : {window.title}")
            return True
        except Exception as e:
            logger.error(f"Erreur cache fenêtre : {e}")
            return False
    
    def show_window(self, window: WindowInfo) -> bool:
        """Affiche une fenêtre cachée"""
        try:
            win32gui.ShowWindow(window.hwnd, SW_SHOW)
            logger.info(f"Fenêtre affichée : {window.title}")
            return True
        except Exception as e:
            logger.error(f"Erreur affichage fenêtre : {e}")
            return False
    
    def set_window_always_on_top(self, window: WindowInfo, always_on_top: bool = True) -> bool:
        """Définit si une fenêtre reste toujours au premier plan"""
        try:
            if always_on_top:
                flag = win32con.HWND_TOPMOST
            else:
                flag = win32con.HWND_NOTOPMOST
            
            win32gui.SetWindowPos(
                window.hwnd,
                flag,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )
            
            state = "activé" if always_on_top else "désactivé"
            logger.info(f"Always on top {state} : {window.title}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur always on top : {e}")
            return False
    
    def get_window_under_cursor(self) -> Optional[WindowInfo]:
        """Retourne la fenêtre sous le curseur de la souris"""
        try:
            point = win32gui.GetCursorPos()
            hwnd = win32gui.WindowFromPoint(point)
            
            # Remonte jusqu'à la fenêtre parent principale
            while True:
                parent = win32gui.GetParent(hwnd)
                if not parent:
                    break
                hwnd = parent
            
            self.refresh_windows_cache()
            return self.windows_cache.get(hwnd)
            
        except Exception as e:
            logger.error(f"Erreur fenêtre sous curseur : {e}")
            return None
    
    def minimize_all_except(self, exception_windows: List[WindowInfo]) -> bool:
        """Minimise toutes les fenêtres sauf celles spécifiées"""
        try:
            exception_hwnds = {w.hwnd for w in exception_windows}
            minimized_count = 0
            
            for window in self.get_visible_windows():
                if window.hwnd not in exception_hwnds and not window.is_minimized:
                    if self.minimize_window(window):
                        minimized_count += 1
            
            logger.info(f"{minimized_count} fenêtres minimisées")
            return True
            
        except Exception as e:
            logger.error(f"Erreur minimisation sélective : {e}")
            return False

# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration de logging pour test
    logging.basicConfig(level=logging.INFO)
    
    # Crée le gestionnaire de fenêtres
    wm = WindowManager()
    
    # Affiche toutes les fenêtres visibles
    windows = wm.get_visible_windows()
    print(f"Fenêtres visibles : {len(windows)}")
    
    for window in windows[:5]:  # Limite à 5 pour l'exemple
        print(f"- {window.title} ({window.process_name})")
    
    # Exemple : centre la première fenêtre
    if windows:
        wm.center_window(windows[0])
        print(f"Fenêtre centrée : {windows[0].title}")
