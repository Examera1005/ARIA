"""
Module de contrôle système pour ARIA
Gère l'ouverture/fermeture d'applications, la manipulation de fichiers,
et l'exécution de commandes système Windows.
"""

import os
import sys
import subprocess
import psutil
import winreg
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import json
import logging
from dataclasses import dataclass
import ctypes
from ctypes import wintypes

logger = logging.getLogger(__name__)

@dataclass
class AppInfo:
    """Informations sur une application"""
    name: str
    path: str
    process_name: str
    description: str = ""
    icon_path: str = ""
    is_running: bool = False
    pid: Optional[int] = None

class SystemController:
    """Contrôleur principal pour les opérations système"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.applications = {}
        self.blocked_processes = {"explorer.exe", "winlogon.exe", "csrss.exe", "dwm.exe"}
        self.app_aliases = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "wordpad": "wordpad.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "outlook": "outlook.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "spotify": "spotify.exe",
            "discord": "discord.exe",
            "steam": "steam.exe",
            "vlc": "vlc.exe"
        }
        self._discover_applications()
    
    def _discover_applications(self):
        """Découvre automatiquement les applications installées"""
        try:
            logger.info("Découverte des applications installées...")
            
            # Applications Windows par défaut
            windows_apps = {
                "notepad": r"C:\Windows\System32\notepad.exe",
                "calculator": r"C:\Windows\System32\calc.exe",
                "paint": r"C:\Windows\System32\mspaint.exe",
                "wordpad": r"C:\Program Files\Windows NT\Accessories\wordpad.exe",
                "cmd": r"C:\Windows\System32\cmd.exe",
                "powershell": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
            }
            
            for app_name, app_path in windows_apps.items():
                if os.path.exists(app_path):
                    process_name = os.path.basename(app_path)
                    self.applications[app_name] = AppInfo(
                        name=app_name,
                        path=app_path,
                        process_name=process_name,
                        description=f"Application Windows : {app_name}"
                    )
            
            # Recherche dans Program Files
            program_dirs = [
                r"C:\Program Files",
                r"C:\Program Files (x86)",
                os.path.expanduser("~\\AppData\\Local"),
                os.path.expanduser("~\\AppData\\Roaming")
            ]
            
            for program_dir in program_dirs:
                if os.path.exists(program_dir):
                    self._scan_directory_for_apps(program_dir)
            
            # Applications via registre Windows
            self._discover_from_registry()
            
            logger.info(f"Découvert {len(self.applications)} applications")
            
        except Exception as e:
            logger.error(f"Erreur lors de la découverte d'applications : {e}")
    
    def _scan_directory_for_apps(self, directory: str, max_depth: int = 2):
        """Scanne un répertoire pour trouver des applications"""
        try:
            for root, dirs, files in os.walk(directory):
                # Limite la profondeur de recherche
                level = root.replace(directory, '').count(os.sep)
                if level >= max_depth:
                    dirs[:] = []
                
                for file in files:
                    if file.lower().endswith('.exe'):
                        exe_path = os.path.join(root, file)
                        app_name = os.path.splitext(file)[0].lower()
                        
                        # Évite les applications système et temporaires
                        if self._is_valid_application(app_name, exe_path):
                            self.applications[app_name] = AppInfo(
                                name=app_name,
                                path=exe_path,
                                process_name=file,
                                description=f"Application trouvée : {file}"
                            )
                            
        except Exception as e:
            logger.error(f"Erreur scan répertoire {directory} : {e}")
    
    def _discover_from_registry(self):
        """Découvre les applications via le registre Windows"""
        try:
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            for hkey, registry_path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, registry_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        app_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                        
                                        if install_location and os.path.exists(install_location):
                                            # Cherche l'executable principal
                                            exe_files = list(Path(install_location).glob("*.exe"))
                                            if exe_files:
                                                main_exe = exe_files[0]  # Prend le premier
                                                app_key = app_name.lower().replace(" ", "_")
                                                
                                                if app_key not in self.applications:
                                                    self.applications[app_key] = AppInfo(
                                                        name=app_key,
                                                        path=str(main_exe),
                                                        process_name=main_exe.name,
                                                        description=app_name
                                                    )
                                    except (FileNotFoundError, OSError):
                                        continue
                            except (OSError, ValueError):
                                continue
                except (OSError, ValueError):
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur découverte registre : {e}")
    
    def _is_valid_application(self, app_name: str, exe_path: str) -> bool:
        """Vérifie si l'application est valide et peut être lancée"""
        try:
            # Évite les applications système critiques
            system_keywords = [
                "system", "windows", "microsoft", "temp", "cache", 
                "unins", "setup", "install", "update", "service"
            ]
            
            if any(keyword in app_name.lower() for keyword in system_keywords):
                return False
            
            # Vérifie que le fichier existe et est exécutable
            if not os.path.exists(exe_path) or not os.access(exe_path, os.X_OK):
                return False
            
            # Évite les fichiers trop petits (probablement des liens ou utilitaires)
            if os.path.getsize(exe_path) < 50000:  # 50KB minimum
                return False
                
            return True
            
        except:
            return False
    
    def open_application(self, app_name: str) -> bool:
        """Ouvre une application"""
        try:
            app_name = app_name.lower().strip()
            
            # Cherche d'abord dans les alias
            if app_name in self.app_aliases:
                process_name = self.app_aliases[app_name]
                
                # Vérifie si déjà en cours d'exécution
                if self._is_process_running(process_name):
                    logger.info(f"Application {app_name} déjà ouverte")
                    return True
                
                # Essaie d'ouvrir via le nom du processus
                try:
                    subprocess.Popen(process_name)
                    logger.info(f"Application {app_name} ouverte via alias")
                    return True
                except:
                    pass
            
            # Cherche dans les applications découvertes
            app_info = None
            for app_key, app_data in self.applications.items():
                if (app_name in app_key or 
                    app_name in app_data.description.lower() or
                    app_name in app_data.process_name.lower()):
                    app_info = app_data
                    break
            
            if app_info:
                # Vérifie si déjà en cours d'exécution
                if self._is_process_running(app_info.process_name):
                    logger.info(f"Application {app_name} déjà ouverte")
                    return True
                
                # Lance l'application
                subprocess.Popen([app_info.path])
                logger.info(f"Application {app_name} ouverte : {app_info.path}")
                
                # Attendre un peu et vérifier si le processus est démarré
                time.sleep(2)
                return self._is_process_running(app_info.process_name)
            
            # Essaie d'ouvrir directement comme commande
            try:
                subprocess.Popen(app_name)
                logger.info(f"Commande {app_name} exécutée")
                return True
            except:
                pass
            
            logger.warning(f"Application {app_name} non trouvée")
            return False
            
        except Exception as e:
            logger.error(f"Erreur ouverture application {app_name} : {e}")
            return False
    
    def close_application(self, app_name: str, force: bool = False) -> bool:
        """Ferme une application"""
        try:
            app_name = app_name.lower().strip()
            processes_to_kill = []
            
            # Cherche les processus correspondants
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower()
                    
                    # Évite les processus système critiques
                    if proc_name in self.blocked_processes:
                        continue
                    
                    # Correspondance par nom
                    if (app_name in proc_name or 
                        (app_name in self.app_aliases and 
                         self.app_aliases[app_name].lower() == proc_name)):
                        processes_to_kill.append(proc)
                        continue
                    
                    # Correspondance par chemin d'exécution
                    if proc_info['exe']:
                        exe_name = os.path.basename(proc_info['exe']).lower()
                        if app_name in exe_name:
                            processes_to_kill.append(proc)
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not processes_to_kill:
                logger.info(f"Aucun processus trouvé pour {app_name}")
                return True
            
            # Ferme les processus trouvés
            success = True
            for proc in processes_to_kill:
                try:
                    if force:
                        proc.kill()
                        logger.info(f"Processus {proc.name()} (PID: {proc.pid}) tué")
                    else:
                        proc.terminate()
                        logger.info(f"Processus {proc.name()} (PID: {proc.pid}) terminé")
                        
                        # Attend la fermeture propre
                        try:
                            proc.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            logger.warning(f"Timeout, tuer le processus {proc.name()}")
                            proc.kill()
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logger.warning(f"Impossible de fermer le processus : {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur fermeture application {app_name} : {e}")
            return False
    
    def _is_process_running(self, process_name: str) -> bool:
        """Vérifie si un processus est en cours d'exécution"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == process_name.lower():
                    return True
            return False
        except:
            return False
    
    def get_running_applications(self) -> List[Dict]:
        """Retourne la liste des applications en cours d'exécution"""
        try:
            running_apps = []
            
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'memory_info', 'cpu_percent']):
                try:
                    proc_info = proc.info
                    
                    # Filtre les processus système
                    if (proc_info['name'].lower() in self.blocked_processes or
                        not proc_info['exe'] or
                        'system32' in proc_info['exe'].lower()):
                        continue
                    
                    running_apps.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'exe': proc_info['exe'],
                        'memory_mb': round(proc_info['memory_info'].rss / 1024 / 1024, 1),
                        'cpu_percent': proc_info['cpu_percent']
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Trie par utilisation mémoire décroissante
            running_apps.sort(key=lambda x: x['memory_mb'], reverse=True)
            
            return running_apps
            
        except Exception as e:
            logger.error(f"Erreur liste applications : {e}")
            return []
    
    def execute_command(self, command: str, shell: bool = True, timeout: int = 30) -> Tuple[bool, str]:
        """Exécute une commande système"""
        try:
            logger.info(f"Exécution commande : {command}")
            
            # Commandes dangereuses à éviter
            dangerous_commands = [
                'format', 'del', 'rm', 'rmdir', 'shutdown', 'restart',
                'registry', 'regedit', 'taskkill', 'net user', 'diskpart'
            ]
            
            if any(dangerous in command.lower() for dangerous in dangerous_commands):
                logger.warning(f"Commande potentiellement dangereuse bloquée : {command}")
                return False, "Commande bloquée pour sécurité"
            
            # Exécute la commande
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            output = result.stdout if result.stdout else result.stderr
            success = result.returncode == 0
            
            logger.info(f"Commande {'réussie' if success else 'échouée'}")
            return success, output.strip()
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout commande : {command}")
            return False, "Timeout de la commande"
        except Exception as e:
            logger.error(f"Erreur exécution commande : {e}")
            return False, str(e)
    
    def open_file_or_folder(self, path: str) -> bool:
        """Ouvre un fichier ou dossier avec l'application par défaut"""
        try:
            path = os.path.expandvars(os.path.expanduser(path))
            
            if not os.path.exists(path):
                logger.warning(f"Chemin inexistant : {path}")
                return False
            
            # Ouvre avec l'application par défaut
            os.startfile(path)
            logger.info(f"Ouvert : {path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur ouverture {path} : {e}")
            return False
    
    def create_file(self, path: str, content: str = "") -> bool:
        """Crée un fichier"""
        try:
            path = os.path.expandvars(os.path.expanduser(path))
            
            # Crée les répertoires parents si nécessaire
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Fichier créé : {path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur création fichier {path} : {e}")
            return False
    
    def copy_file(self, source: str, destination: str) -> bool:
        """Copie un fichier"""
        try:
            source = os.path.expandvars(os.path.expanduser(source))
            destination = os.path.expandvars(os.path.expanduser(destination))
            
            if not os.path.exists(source):
                logger.warning(f"Source inexistante : {source}")
                return False
            
            # Crée le répertoire de destination si nécessaire
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.copy2(source, destination)
            logger.info(f"Fichier copié : {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur copie {source} -> {destination} : {e}")
            return False
    
    def move_file(self, source: str, destination: str) -> bool:
        """Déplace un fichier"""
        try:
            source = os.path.expandvars(os.path.expanduser(source))
            destination = os.path.expandvars(os.path.expanduser(destination))
            
            if not os.path.exists(source):
                logger.warning(f"Source inexistante : {source}")
                return False
            
            # Crée le répertoire de destination si nécessaire
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.move(source, destination)
            logger.info(f"Fichier déplacé : {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur déplacement {source} -> {destination} : {e}")
            return False
    
    def delete_file(self, path: str, confirm: bool = True) -> bool:
        """Supprime un fichier (avec confirmation par défaut)"""
        try:
            path = os.path.expandvars(os.path.expanduser(path))
            
            if not os.path.exists(path):
                logger.warning(f"Fichier inexistant : {path}")
                return False
            
            if confirm:
                # En mode production, on devrait demander confirmation à l'utilisateur
                logger.warning(f"Suppression demandée pour : {path} (confirmation requise)")
                return False
            
            if os.path.isfile(path):
                os.remove(path)
                logger.info(f"Fichier supprimé : {path}")
            elif os.path.isdir(path):
                shutil.rmtree(path)
                logger.info(f"Dossier supprimé : {path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur suppression {path} : {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """Retourne des informations système"""
        try:
            import platform
            
            # Informations CPU
            cpu_info = {
                'count': psutil.cpu_count(),
                'usage': psutil.cpu_percent(interval=1)
            }
            
            # Informations mémoire
            memory = psutil.virtual_memory()
            memory_info = {
                'total_gb': round(memory.total / 1024**3, 1),
                'available_gb': round(memory.available / 1024**3, 1),
                'used_percent': memory.percent
            }
            
            # Informations disque
            disk = psutil.disk_usage('C:')
            disk_info = {
                'total_gb': round(disk.total / 1024**3, 1),
                'free_gb': round(disk.free / 1024**3, 1),
                'used_percent': round((disk.used / disk.total) * 100, 1)
            }
            
            return {
                'platform': platform.system(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'uptime_hours': round(time.time() - psutil.boot_time()) / 3600
            }
            
        except Exception as e:
            logger.error(f"Erreur info système : {e}")
            return {}
    
    def minimize_all_windows(self) -> bool:
        """Minimise toutes les fenêtres"""
        try:
            # Simule Windows+D
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            user32.keybd_event(0x5B, 0, 0, 0)  # Win key down
            user32.keybd_event(0x44, 0, 0, 0)  # D key down
            user32.keybd_event(0x44, 0, 2, 0)  # D key up
            user32.keybd_event(0x5B, 0, 2, 0)  # Win key up
            
            logger.info("Toutes les fenêtres minimisées")
            return True
            
        except Exception as e:
            logger.error(f"Erreur minimisation fenêtres : {e}")
            return False
    
    def lock_workstation(self) -> bool:
        """Verrouille la session Windows"""
        try:
            ctypes.windll.user32.LockWorkStation()
            logger.info("Session verrouillée")
            return True
        except Exception as e:
            logger.error(f"Erreur verrouillage session : {e}")
            return False
    
    def get_available_applications(self) -> List[str]:
        """Retourne la liste des applications disponibles"""
        return list(self.applications.keys())
    
    def search_files(self, pattern: str, directory: str = None, limit: int = 50) -> List[str]:
        """Recherche des fichiers par nom"""
        try:
            if directory is None:
                directory = os.path.expanduser("~")
            
            directory = os.path.expandvars(os.path.expanduser(directory))
            
            if not os.path.exists(directory):
                return []
            
            matches = []
            pattern = pattern.lower()
            
            for root, dirs, files in os.walk(directory):
                # Évite les répertoires système
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in ['system32', 'windows', 'program files']]
                
                for file in files:
                    if pattern in file.lower():
                        matches.append(os.path.join(root, file))
                        
                        if len(matches) >= limit:
                            return matches
            
            return matches
            
        except Exception as e:
            logger.error(f"Erreur recherche fichiers : {e}")
            return []

# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration de logging pour test
    logging.basicConfig(level=logging.INFO)
    
    # Crée le contrôleur système
    controller = SystemController()
    
    print(f"Applications découvertes : {len(controller.get_available_applications())}")
    
    # Exemple : ouvrir le bloc-notes
    if controller.open_application("notepad"):
        print("Notepad ouvert avec succès")
        time.sleep(2)
        
        # Fermer le bloc-notes
        if controller.close_application("notepad"):
            print("Notepad fermé avec succès")
    
    # Affichage des informations système
    info = controller.get_system_info()
    print(f"Système : {info.get('platform')} - CPU: {info.get('cpu', {}).get('usage')}%")
