"""
🤖 Exécuteur de Tâches IA Avancé pour ARIA
=========================================

Système d'IA capable d'exécuter n'importe quelle tâche demandée :
- Compréhension du langage naturel avancée
- Planification et exécution de tâches complexes
- Contrôle complet du système (souris, clavier, applications)
- Automation web intelligente
- Gestion des emails et communication
"""

import asyncio
import logging
import re
import json
import time
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import queue

# Modules système et automation
import pyautogui
import keyboard
import mouse
import psutil
import subprocess
from pathlib import Path

# Modules locaux ARIA
from .system_controller import SystemController
from .window_manager import WindowManager
try:
    from .web_automation import WebAutomation
except ImportError:
    WebAutomation = None

try:
    from ..core.intent_analyzer import IntentAnalyzer, IntentResult
except ImportError:
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        from core.intent_analyzer import IntentAnalyzer, IntentResult
    except ImportError:
        IntentAnalyzer = None
        IntentResult = None

try:
    from ..apis.gmail_manager import GmailManager
except ImportError:
    try:
        from apis.gmail_manager import GmailManager
    except ImportError:
        GmailManager = None

try:
    from ..apis.calendar_manager import CalendarManager
except ImportError:
    try:
        from apis.calendar_manager import CalendarManager
    except ImportError:
        CalendarManager = None

logger = logging.getLogger(__name__)

@dataclass
class TaskStep:
    """Étape d'une tâche complexe"""
    action: str
    parameters: Dict[str, Any]
    description: str
    completed: bool = False
    result: Any = None
    error: Optional[str] = None

@dataclass
class TaskResult:
    """Résultat d'exécution d'une tâche"""
    success: bool
    message: str
    data: Any = None
    steps_completed: List[TaskStep] = None
    execution_time: float = 0.0

class AITaskExecutor:
    """Exécuteur de tâches IA principal"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger("ARIA.TaskExecutor")
        
        # Initialisation des modules
        self.system_controller = SystemController(config)
        self.window_manager = WindowManager(config)
        
        # Analyseur d'intentions (optionnel)
        if IntentAnalyzer:
            self.intent_analyzer = IntentAnalyzer(config)
        else:
            self.intent_analyzer = None
        
        # Modules optionnels
        self.web_automation = WebAutomation(config) if WebAutomation else None
        self.gmail_manager = GmailManager(config) if GmailManager else None
        self.calendar_manager = CalendarManager(config) if CalendarManager else None
        
        # Configuration de PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        # Cache des résultats et contexte
        self.task_history = []
        self.current_context = {}
        
        # Patterns de tâches avancées
        self.task_patterns = self._load_task_patterns()
        
        self.logger.info("🤖 Exécuteur de tâches IA initialisé")
    
    def _load_task_patterns(self) -> Dict[str, Dict]:
        """Charge les patterns de tâches complexes"""
        return {
            "open_application": {
                "keywords": ["ouvre", "lance", "démarre", "open", "start"],
                "executor": self._execute_open_application
            },
            "close_application": {
                "keywords": ["ferme", "quitte", "arrête", "close", "quit", "stop"],
                "executor": self._execute_close_application
            },
            "web_search": {
                "keywords": ["recherche", "cherche", "google", "search", "find"],
                "executor": self._execute_web_search
            },
            "web_navigation": {
                "keywords": ["va sur", "navigue", "visite", "go to", "navigate"],
                "executor": self._execute_web_navigation
            },
            "youtube_search": {
                "keywords": ["youtube", "vidéo", "video", "regarde"],
                "executor": self._execute_youtube_search
            },
            "email_management": {
                "keywords": ["email", "mail", "courrier", "message"],
                "executor": self._execute_email_management
            },
            "system_control": {
                "keywords": ["éteins", "redémarre", "verrouille", "shutdown", "restart", "lock"],
                "executor": self._execute_system_control
            },
            "window_management": {
                "keywords": ["fenêtre", "window", "minimise", "maximise", "arrange"],
                "executor": self._execute_window_management
            },
            "mouse_keyboard": {
                "keywords": ["clique", "tape", "écris", "click", "type", "write"],
                "executor": self._execute_mouse_keyboard
            },
            "screenshot": {
                "keywords": ["capture", "screenshot", "photo écran"],
                "executor": self._execute_screenshot
            }
        }
    
    async def execute_task(self, task_description: str, context: Dict = None) -> TaskResult:
        """Exécute une tâche décrite en langage naturel"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🎯 Exécution de la tâche : {task_description}")
            
            # Analyse de l'intention
            intent_result = await self._analyze_intent(task_description, context)
            
            if not intent_result:
                return TaskResult(
                    success=False,
                    message="Impossible de comprendre la tâche demandée",
                    execution_time=time.time() - start_time
                )
            
            # Planification des étapes
            steps = await self._plan_task_steps(intent_result, context)
            
            if not steps:
                return TaskResult(
                    success=False,
                    message="Impossible de planifier l'exécution de cette tâche",
                    execution_time=time.time() - start_time
                )
            
            # Exécution des étapes
            completed_steps = []
            overall_success = True
            final_message = "Tâche exécutée avec succès"
            final_data = None
            
            for step in steps:
                self.logger.info(f"📋 Exécution étape : {step.description}")
                
                try:
                    # Trouve l'exécuteur approprié
                    executor = self._find_executor(step.action)
                    
                    if executor:
                        step.result = await executor(step.parameters, intent_result)
                        step.completed = True
                        
                        if step.result and hasattr(step.result, 'success'):
                            if not step.result.success:
                                step.error = step.result.message
                                overall_success = False
                        
                        # Sauvegarde du résultat final
                        if step.action in ["web_search", "youtube_search", "email_management"]:
                            final_data = step.result
                    else:
                        step.error = f"Exécuteur non trouvé pour l'action : {step.action}"
                        overall_success = False
                    
                    completed_steps.append(step)
                    
                    # Petite pause entre les étapes
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    step.error = str(e)
                    step.completed = False
                    completed_steps.append(step)
                    overall_success = False
                    self.logger.error(f"Erreur étape '{step.description}' : {e}")
            
            # Construction du message final
            if not overall_success:
                failed_steps = [s for s in completed_steps if s.error]
                final_message = f"Tâche partiellement échouée. {len(failed_steps)} étape(s) en erreur."
            
            execution_time = time.time() - start_time
            
            # Sauvegarde dans l'historique
            result = TaskResult(
                success=overall_success,
                message=final_message,
                data=final_data,
                steps_completed=completed_steps,
                execution_time=execution_time
            )
            
            self.task_history.append({
                "timestamp": datetime.now(),
                "task": task_description,
                "result": result
            })
            
            self.logger.info(f"✅ Tâche terminée en {execution_time:.2f}s : {final_message}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Erreur critique lors de l'exécution : {e}"
            self.logger.error(error_msg)
            
            return TaskResult(
                success=False,
                message=error_msg,
                execution_time=execution_time
            )
    
    async def _analyze_intent(self, task_description: str, context: Dict = None) -> Optional[Any]:
        """Analyse l'intention de la tâche"""
        try:
            if not self.intent_analyzer:
                # Fallback: analyse basique par mots-clés
                return self._basic_intent_analysis(task_description)
                
            # Utilise l'analyseur d'intentions existant
            intent_result = self.intent_analyzer.analyze(task_description, context)
            return intent_result
            
        except Exception as e:
            self.logger.error(f"Erreur analyse intention : {e}")
            return self._basic_intent_analysis(task_description)
    
    def _basic_intent_analysis(self, task_description: str) -> Any:
        """Analyse d'intention basique sans IA"""
        text = task_description.lower()
        
        # Simple class to mimic IntentResult
        class BasicIntentResult:
            def __init__(self, intent, entities, confidence, original_text):
                self.intent = intent
                self.entities = entities
                self.confidence = confidence
                self.original_text = original_text
        
        # Analyse par mots-clés
        if any(word in text for word in ["ouvre", "lance", "démarre", "open", "start"]):
            # Extrait le nom de l'application
            for pattern in ["ouvre ", "lance ", "démarre ", "open ", "start "]:
                if pattern in text:
                    app_name = text.split(pattern)[1].split()[0]
                    return BasicIntentResult("open_application", {"application": app_name}, 0.8, task_description)
        
        elif any(word in text for word in ["ferme", "quitte", "close", "quit"]):
            for pattern in ["ferme ", "quitte ", "close ", "quit "]:
                if pattern in text:
                    app_name = text.split(pattern)[1].split()[0] if len(text.split(pattern)) > 1 else ""
                    return BasicIntentResult("close_application", {"application": app_name}, 0.8, task_description)
        
        elif any(word in text for word in ["google", "recherche", "cherche", "search"]):
            return BasicIntentResult("web_search", {"query": task_description}, 0.7, task_description)
        
        elif any(word in text for word in ["youtube", "vidéo", "video"]):
            return BasicIntentResult("youtube_search", {"query": task_description}, 0.7, task_description)
        
        elif any(word in text for word in ["capture", "screenshot"]):
            return BasicIntentResult("screenshot", {}, 0.9, task_description)
        
        else:
            return BasicIntentResult("unknown", {}, 0.1, task_description)
    
    async def _plan_task_steps(self, intent_result: Any, context: Dict = None) -> List[TaskStep]:
        """Planifie les étapes nécessaires pour accomplir la tâche"""
        steps = []
        
        try:
            intent = intent_result.intent
            entities = intent_result.entities
            
            # Planification basée sur l'intention
            if intent == "open_application":
                app_name = entities.get("application", entities.get("target", ""))
                steps.append(TaskStep(
                    action="open_application",
                    parameters={"app_name": app_name},
                    description=f"Ouvrir l'application {app_name}"
                ))
            
            elif intent == "close_application":
                app_name = entities.get("application", entities.get("target", ""))
                steps.append(TaskStep(
                    action="close_application", 
                    parameters={"app_name": app_name},
                    description=f"Fermer l'application {app_name}"
                ))
            
            elif intent == "web_search":
                query = entities.get("query", entities.get("search_term", ""))
                result_number = entities.get("result_number", 1)
                
                steps.append(TaskStep(
                    action="web_search",
                    parameters={"query": query, "result_number": result_number},
                    description=f"Rechercher '{query}' et aller au résultat #{result_number}"
                ))
            
            elif intent == "youtube_search":
                query = entities.get("query", entities.get("search_term", ""))
                result_number = entities.get("result_number", 1)
                
                steps.append(TaskStep(
                    action="youtube_search", 
                    parameters={"query": query, "result_number": result_number},
                    description=f"Rechercher '{query}' sur YouTube et lire la vidéo #{result_number}"
                ))
            
            elif intent == "email_read":
                sender = entities.get("sender", "")
                steps.append(TaskStep(
                    action="email_management",
                    parameters={"action": "read", "sender": sender},
                    description=f"Lire les emails de {sender}" if sender else "Lire les emails"
                ))
            
            elif intent == "system_command":
                command = entities.get("command", "")
                steps.append(TaskStep(
                    action="system_control",
                    parameters={"command": command},
                    description=f"Exécuter la commande système : {command}"
                ))
            
            # Cas complexes nécessitant plusieurs étapes
            elif "firefox" in intent_result.original_text.lower() and "google" in intent_result.original_text.lower():
                # Exemple : "ouvre firefox et va sur google puis cherche cat video et choisis la deuxième vidéo"
                steps.extend([
                    TaskStep("open_application", {"app_name": "firefox"}, "Ouvrir Firefox"),
                    TaskStep("web_navigation", {"url": "google.com"}, "Aller sur Google"),
                    TaskStep("web_search", {"query": "cat video", "result_number": 2}, "Chercher 'cat video' et choisir le 2ème résultat")
                ])
            
            return steps
            
        except Exception as e:
            self.logger.error(f"Erreur planification : {e}")
            return []
    
    def _find_executor(self, action: str) -> Optional[callable]:
        """Trouve l'exécuteur approprié pour une action"""
        return self.task_patterns.get(action, {}).get("executor")
    
    # ========== EXÉCUTEURS SPÉCIALISÉS ==========
    
    async def _execute_open_application(self, params: Dict, intent: Any) -> TaskResult:
        """Exécute l'ouverture d'une application"""
        app_name = params.get("app_name", "")
        
        try:
            success = self.system_controller.open_application(app_name)
            
            if success:
                # Petite attente pour que l'application se lance
                await asyncio.sleep(2)
                return TaskResult(True, f"Application {app_name} ouverte avec succès")
            else:
                return TaskResult(False, f"Impossible d'ouvrir l'application {app_name}")
                
        except Exception as e:
            return TaskResult(False, f"Erreur ouverture {app_name}: {e}")
    
    async def _execute_close_application(self, params: Dict, intent: Any) -> TaskResult:
        """Exécute la fermeture d'une application"""
        app_name = params.get("app_name", "")
        
        try:
            success = self.system_controller.close_application(app_name)
            
            if success:
                return TaskResult(True, f"Application {app_name} fermée avec succès")
            else:
                return TaskResult(False, f"Impossible de fermer l'application {app_name}")
                
        except Exception as e:
            return TaskResult(False, f"Erreur fermeture {app_name}: {e}")
    
    async def _execute_web_search(self, params: Dict, intent: Any) -> TaskResult:
        """Exécute une recherche web"""
        if not self.web_automation:
            return TaskResult(False, "Module d'automation web non disponible")
        
        query = params.get("query", "")
        result_number = params.get("result_number", 1)
        
        try:
            # Démarre le navigateur si nécessaire
            if not self.web_automation.driver:
                if not self.web_automation.start_browser():
                    return TaskResult(False, "Impossible de démarrer le navigateur")
            
            # Effectue la recherche
            url = self.web_automation.search_google(query, result_number)
            
            if url:
                # Navigue vers le résultat
                self.web_automation.navigate_to(url)
                return TaskResult(True, f"Recherche '{query}' effectuée, résultat #{result_number} ouvert", {"url": url})
            else:
                return TaskResult(False, f"Aucun résultat trouvé pour '{query}'")
                
        except Exception as e:
            return TaskResult(False, f"Erreur recherche web: {e}")
    
    async def _execute_web_navigation(self, params: Dict, intent: Any) -> TaskResult:
        """Exécute une navigation web"""
        if not self.web_automation:
            return TaskResult(False, "Module d'automation web non disponible")
        
        url = params.get("url", "")
        
        try:
            # Démarre le navigateur si nécessaire
            if not self.web_automation.driver:
                if not self.web_automation.start_browser():
                    return TaskResult(False, "Impossible de démarrer le navigateur")
            
            success = self.web_automation.navigate_to(url)
            
            if success:
                return TaskResult(True, f"Navigation vers {url} réussie")
            else:
                return TaskResult(False, f"Impossible de naviguer vers {url}")
                
        except Exception as e:
            return TaskResult(False, f"Erreur navigation: {e}")
    
    async def _execute_youtube_search(self, params: Dict, intent: Any) -> TaskResult:
        """Exécute une recherche YouTube"""
        if not self.web_automation:
            return TaskResult(False, "Module d'automation web non disponible")
        
        query = params.get("query", "")
        result_number = params.get("result_number", 1)
        
        try:
            # Démarre le navigateur si nécessaire
            if not self.web_automation.driver:
                if not self.web_automation.start_browser():
                    return TaskResult(False, "Impossible de démarrer le navigateur")
            
            # Effectue la recherche YouTube
            url = self.web_automation.search_youtube_videos(query, result_number)
            
            if url:
                # Navigue vers la vidéo
                self.web_automation.navigate_to(url)
                return TaskResult(True, f"Vidéo '{query}' #{result_number} en cours de lecture", {"url": url})
            else:
                return TaskResult(False, f"Aucune vidéo trouvée pour '{query}'")
                
        except Exception as e:
            return TaskResult(False, f"Erreur recherche YouTube: {e}")
    
    async def _execute_email_management(self, params: Dict, intent: Any) -> TaskResult:
        """Exécute la gestion des emails"""
        if not self.gmail_manager:
            return TaskResult(False, "Module Gmail non disponible")
        
        action = params.get("action", "read")
        sender = params.get("sender", "")
        
        try:
            if action == "read":
                emails = self.gmail_manager.get_recent_emails(sender_filter=sender, max_results=10)
                
                if emails:
                    # Résumé des emails
                    summary = []
                    for email in emails[:5]:  # Limite à 5 emails
                        summary.append({
                            "from": email.get("from", "Inconnu"),
                            "subject": email.get("subject", "Sans sujet"),
                            "snippet": email.get("snippet", "")[:100]
                        })
                    
                    return TaskResult(True, f"{len(emails)} email(s) trouvé(s)", {"emails": summary})
                else:
                    return TaskResult(True, "Aucun email trouvé", {"emails": []})
            
            return TaskResult(False, f"Action email non supportée: {action}")
            
        except Exception as e:
            return TaskResult(False, f"Erreur gestion email: {e}")
    
    async def _execute_system_control(self, params: Dict, intent: Any) -> TaskResult:
        """Exécute les commandes système"""
        command = params.get("command", "")
        
        try:
            if "shutdown" in command or "éteins" in command:
                success = self.system_controller.shutdown_system()
            elif "restart" in command or "redémarre" in command:
                success = self.system_controller.restart_system() 
            elif "lock" in command or "verrouille" in command:
                success = self.system_controller.lock_workstation()
            elif "sleep" in command or "veille" in command:
                success = self.system_controller.sleep_system()
            else:
                return TaskResult(False, f"Commande système non reconnue: {command}")
            
            if success:
                return TaskResult(True, f"Commande système '{command}' exécutée")
            else:
                return TaskResult(False, f"Échec de la commande système '{command}'")
                
        except Exception as e:
            return TaskResult(False, f"Erreur commande système: {e}")
    
    async def _execute_window_management(self, params: Dict, intent: Any) -> TaskResult:
        """Exécute la gestion des fenêtres"""
        action = params.get("action", "")
        
        try:
            if "minimize" in action or "minimise" in action:
                success = self.system_controller.minimize_all_windows()
            elif "maximize" in action or "maximise" in action:
                windows = self.window_manager.get_visible_windows()
                success = len(windows) > 0
                for window in windows:
                    self.window_manager.maximize_window(window)
            else:
                return TaskResult(False, f"Action fenêtre non reconnue: {action}")
            
            if success:
                return TaskResult(True, f"Gestion fenêtres '{action}' exécutée")
            else:
                return TaskResult(False, f"Échec gestion fenêtres '{action}'")
                
        except Exception as e:
            return TaskResult(False, f"Erreur gestion fenêtres: {e}")
    
    async def _execute_mouse_keyboard(self, params: Dict, intent: Any) -> TaskResult:
        """Exécute les actions souris/clavier"""
        action = params.get("action", "")
        target = params.get("target", "")
        text = params.get("text", "")
        
        try:
            if "click" in action or "clique" in action:
                # Clic souris - peut être amélioré avec reconnaissance d'images
                pyautogui.click()
                return TaskResult(True, "Clic de souris exécuté")
            
            elif "type" in action or "tape" in action or "écris" in action:
                if text:
                    pyautogui.write(text)
                    return TaskResult(True, f"Texte tapé: {text}")
                else:
                    return TaskResult(False, "Aucun texte à taper spécifié")
            
            elif "key" in action or "touche" in action:
                if target:
                    pyautogui.press(target)
                    return TaskResult(True, f"Touche {target} pressée")
                else:
                    return TaskResult(False, "Aucune touche spécifiée")
            
            return TaskResult(False, f"Action souris/clavier non reconnue: {action}")
            
        except Exception as e:
            return TaskResult(False, f"Erreur action souris/clavier: {e}")
    
    async def _execute_screenshot(self, params: Dict, intent: Any) -> TaskResult:
        """Prend une capture d'écran"""
        save_path = params.get("save_path", f"screenshot_{int(time.time())}.png")
        
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            
            return TaskResult(True, f"Capture d'écran sauvée: {save_path}", {"path": save_path})
            
        except Exception as e:
            return TaskResult(False, f"Erreur capture d'écran: {e}")
    
    def get_task_history(self) -> List[Dict]:
        """Retourne l'historique des tâches"""
        return self.task_history.copy()
    
    def clear_task_history(self):
        """Vide l'historique des tâches"""
        self.task_history.clear()
        self.logger.info("Historique des tâches vidé")

# Exemple d'utilisation
if __name__ == "__main__":
    async def test_executor():
        logging.basicConfig(level=logging.INFO)
        
        executor = AITaskExecutor()
        
        # Test de différentes tâches
        tasks = [
            "ouvre firefox",
            "va sur google et cherche cat video puis choisis la deuxième vidéo",
            "prends une capture d'écran",
            "ferme firefox"
        ]
        
        for task in tasks:
            print(f"\n🎯 Test: {task}")
            result = await executor.execute_task(task)
            print(f"✅ Résultat: {result.message}")
            await asyncio.sleep(2)
    
    # Exécution des tests
    asyncio.run(test_executor())
