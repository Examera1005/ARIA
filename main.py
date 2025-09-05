#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 ARIA - Assistant IA Conversationnel Avancé
=============================================

Assistant IA qui peut :
- 🎤 Comprendre vos commandes vocales en français
- 💻 Contrôler votre ordinateur entièrement  
- 📧 Gérer emails, calendrier, réseaux sociaux
- 🌐 Utiliser des APIs pour automatiser vos tâches
- 🎯 Apprendre de vos habitudes et préférences

Auteur: Assistant IA
Version: 1.0
"""

import asyncio
import sys
import os
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import threading
import queue
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Ajouter le chemin du projet
sys.path.append(str(Path(__file__).parent))

# Configuration du logging basique
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "logs", "aria.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Import des modules disponibles
try:
    from ui.main_window import ARIAMainWindow
except ImportError:
    ARIAMainWindow = None

try:
    from automation.task_executor import AITaskExecutor
    from automation.web_automation import WebAutomation
    from automation.system_controller import SystemController
    from automation.window_manager import WindowManager
except ImportError as e:
    print(f"Certains modules d'automation non disponibles: {e}")
    AITaskExecutor = None
    WebAutomation = None
    SystemController = None
    WindowManager = None

try:
    from core.response_engine import ResponseEngine
except ImportError:
    ResponseEngine = None

try:
    from automation.system_controller import SystemController
except ImportError:
    SystemController = None

class ARIAAssistant:
    """Assistant IA Principal - Version Avancée"""
    
    def __init__(self):
        """Initialiser ARIA avec toutes les capacités"""
        self.logger = logging.getLogger("ARIA")
        self.running = False
        self.listening = False
        
        # File d'attente pour les commandes
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Composants principaux
        self.speech_engine = None
        self.system_controller = None
        self.response_engine = None
        self.task_executor = None
        self.web_automation = None
        self.window_manager = None
        
        # Interface utilisateur
        self.ui_window = None
        
        # Configuration avancée
        self.config = {
            'voice_enabled': True,
            'language': 'fr',
            'browser_preference': 'chrome',
            'headless_browser': False,
            'task_execution_enabled': True,
            'web_automation_enabled': True,
            'email_enabled': True
        }
        
        # Contexte de conversation
        self.conversation_context = {
            "history": [],
            "current_task": None,
            "user_preferences": {},
            "active_sessions": {},
            "last_web_search": None,
            "last_application_opened": None
        }
        
        # Créer les dossiers nécessaires s'ils n'existent pas
        os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(__file__), "config"), exist_ok=True)
        
        self.logger.info("🤖 ARIA Assistant initialisé")
    
    def initialize(self):
        """Initialiser tous les composants avancés"""
        self.logger.info("🚀 Initialisation des composants ARIA avancés...")
        
        try:
            # Initialiser le contrôleur système
            if SystemController:
                self.system_controller = SystemController(self.config)
                self.logger.info("✅ Contrôleur système initialisé")
            
            # Initialiser le gestionnaire de fenêtres
            if WindowManager:
                self.window_manager = WindowManager(self.config)
                self.logger.info("✅ Gestionnaire de fenêtres initialisé")
            
            # Initialiser l'exécuteur de tâches IA
            if AITaskExecutor:
                self.task_executor = AITaskExecutor(self.config)
                self.logger.info("✅ Exécuteur de tâches IA initialisé")
            
            # Initialiser l'automation web
            if WebAutomation:
                self.web_automation = WebAutomation(self.config)
                self.logger.info("✅ Module d'automation web initialisé")
            
            # Initialiser le moteur de réponse
            if ResponseEngine:
                self.response_engine = ResponseEngine()
                self.logger.info("✅ Moteur de réponse initialisé")
            
            # Initialiser l'interface utilisateur
            if ARIAMainWindow:
                self.ui_window = ARIAMainWindow()
                # Connecter les callbacks  
                self.ui_window.set_callback('on_command', self._sync_process_command)
                self.ui_window.set_callback('on_start_listening', self.start_listening)
                self.ui_window.set_callback('on_stop_listening', self.stop_listening)
                self.ui_window.add_response("text", "🤖 Bonjour ! Je suis ARIA, votre assistant IA avancé.\n\nJe peux :\n• Ouvrir et contrôler des applications\n• Naviguer sur le web et rechercher des informations\n• Gérer vos emails et calendrier\n• Contrôler votre système (souris, clavier)\n• Automatiser des tâches complexes\n\nQue puis-je faire pour vous ?")
                self.logger.info("✅ Interface utilisateur initialisée")
            
            self.logger.info("🎯 Tous les composants disponibles ont été initialisés avec succès")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            raise
    
    def start(self):
        """Démarrer l'assistant"""
        self.logger.info("🎯 Démarrage d'ARIA...")
        self.running = True
        
        try:
            # Message de bienvenue dans la console
            print("Bonjour ! Je suis ARIA, votre assistant IA.")
            
            # Lancer l'interface utilisateur si disponible
            if self.ui_window:
                self.ui_window.run()
            else:
                # Interface en mode console
                self.console_interface()
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Arrêt demandé par l'utilisateur")
        except Exception as e:
            self.logger.error(f"❌ Erreur dans la boucle principale: {e}")
        finally:
            self.shutdown()
    
    def console_interface(self):
        """Interface en mode console simple"""
        self.logger.info("Console interactive démarrée")
        print("\nARIA est démarré en mode console. Entrez 'exit' pour quitter.")
        print("====================================================================")
        
        while self.running:
            try:
                # Saisie utilisateur
                command = input("\nVous > ").strip()
                
                if command.lower() in ["exit", "quit", "q", "bye"]:
                    print("\nARIA > Au revoir ! À bientôt.")
                    self.running = False
                    break
                    
                if command:
                    print(f"\nARIA > Je traiterais votre commande : {command}")
                    print("        (Version de démonstration - Fonctionnalités limitées)")
                
            except KeyboardInterrupt:
                print("\nARIA > Au revoir ! À bientôt.")
                self.running = False
                break
            except Exception as e:
                print(f"\nARIA > Désolé, une erreur s'est produite : {e}")
                self.logger.error(f"Erreur console: {e}")
    
    async def process_command(self, command: str):
        """Traite une commande utilisateur avec l'IA avancée"""
        self.logger.info(f"🎯 Traitement de la commande: {command}")
        
        try:
            # Ajouter à l'historique
            self.conversation_context["history"].append({
                "timestamp": datetime.now().isoformat(),
                "type": "user_command",
                "content": command
            })
            
            response = None
            
            # Utiliser l'exécuteur de tâches IA si disponible
            if self.task_executor and self.config.get('task_execution_enabled', True):
                try:
                    self.logger.info("🤖 Utilisation de l'exécuteur de tâches IA")
                    
                    # Exécuter la tâche avec l'IA
                    task_result = await self.task_executor.execute_task(
                        command, 
                        context=self.conversation_context
                    )
                    
                    if task_result.success:
                        response = f"✅ {task_result.message}"
                        
                        # Ajouter des informations supplémentaires si disponibles
                        if task_result.data:
                            if isinstance(task_result.data, dict):
                                if "url" in task_result.data:
                                    response += f"\n🔗 URL: {task_result.data['url']}"
                                if "emails" in task_result.data:
                                    emails = task_result.data["emails"]
                                    response += f"\n📧 {len(emails)} email(s) trouvé(s)"
                                    for email in emails[:3]:  # Limite à 3 emails
                                        response += f"\n  • De: {email.get('from', 'Inconnu')}"
                                        response += f"\n    Sujet: {email.get('subject', 'Sans sujet')}"
                                        if email.get('snippet'):
                                            response += f"\n    Aperçu: {email['snippet'][:100]}..."
                        
                        # Informations sur l'exécution
                        if task_result.execution_time > 0:
                            response += f"\n⏱️ Exécuté en {task_result.execution_time:.2f}s"
                    else:
                        response = f"❌ {task_result.message}"
                        
                        # Ajouter des détails sur les erreurs si disponibles
                        if task_result.steps_completed:
                            failed_steps = [s for s in task_result.steps_completed if s.error]
                            if failed_steps:
                                response += f"\n\nÉtapes en erreur:"
                                for step in failed_steps[:3]:  # Limite à 3 erreurs
                                    response += f"\n• {step.description}: {step.error}"
                    
                except Exception as e:
                    self.logger.error(f"Erreur exécuteur de tâches: {e}")
                    response = f"❌ Erreur lors de l'exécution de la tâche: {e}"
            
            # Fallback vers les commandes basiques si l'IA n'est pas disponible
            else:
                response = await self._handle_basic_commands(command)
            
            # Envoyer la réponse à l'interface utilisateur
            if response and self.ui_window:
                self.ui_window.add_response("text", response)
            
            # Ajouter la réponse à l'historique
            self.conversation_context["history"].append({
                "timestamp": datetime.now().isoformat(),
                "type": "assistant_response", 
                "content": response
            })
            
            self.logger.info(f"✅ Commande traitée avec succès")
            
        except Exception as e:
            error_msg = f"❌ Erreur lors du traitement de la commande: {e}"
            self.logger.error(error_msg)
            
            if self.ui_window:
                self.ui_window.add_response("text", error_msg)
    
    def _sync_process_command(self, command: str):
        """Wrapper synchrone pour process_command"""
        try:
            # Exécute la méthode async dans une nouvelle boucle d'événements
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.process_command(command))
            loop.close()
        except Exception as e:
            self.logger.error(f"Erreur wrapper sync: {e}")
            if self.ui_window:
                self.ui_window.add_response("text", f"❌ Erreur: {e}")
    
    async def _handle_basic_commands(self, command: str) -> str:
        """Gère les commandes de base quand l'IA n'est pas disponible"""
        command_lower = command.lower().strip()
        
        # Commandes d'ouverture d'applications
        if any(word in command_lower for word in ["ouvre", "lance", "démarre", "ouvrir", "lancer"]):
            return self._handle_app_launch_command(command_lower)
        
        # Commandes système
        elif any(word in command_lower for word in ["ferme", "arrête", "éteint", "redémarre"]):
            return self._handle_system_command(command_lower)
        
        # Commandes d'information
        elif any(word in command_lower for word in ["quelle heure", "quel jour", "date", "temps"]):
            return self._handle_info_command(command_lower)
        
        # Commandes générales
        else:
            return f"Je comprends votre demande '{command}'. Cette fonctionnalité sera bientôt disponible."
    
    def _handle_app_launch_command(self, command: str) -> str:
        """Gère les commandes d'ouverture d'applications"""
        # Applications courantes avec leurs noms possibles
        app_mapping = {
            "visual studio code": ["visual studio code", "vscode", "vs code", "code"],
            "notepad": ["bloc-notes", "notepad", "bloc notes"],
            "calculator": ["calculatrice", "calculator", "calc"],
            "chrome": ["chrome", "google chrome", "navigateur"],
            "firefox": ["firefox", "mozilla"],
            "explorer": ["explorateur", "explorer", "dossier", "fichiers"],
            "cmd": ["invite de commande", "cmd", "command prompt", "terminal"],
            "powershell": ["powershell", "power shell"]
        }
        
        # Chercher l'application demandée
        app_to_launch = None
        for app_name, keywords in app_mapping.items():
            if any(keyword in command for keyword in keywords):
                app_to_launch = app_name
                break
        
        if app_to_launch and self.system_controller:
            try:
                success = self.system_controller.open_application(app_to_launch)
                if success:
                    return f"✅ J'ai ouvert {app_to_launch} pour vous."
                else:
                    return f"❌ Je n'ai pas pu ouvrir {app_to_launch}. L'application n'est peut-être pas installée."
            except Exception as e:
                return f"❌ Erreur lors de l'ouverture de {app_to_launch}: {e}"
        else:
            return f"Je comprends que vous voulez ouvrir une application, mais je n'ai pas reconnu laquelle. Pouvez-vous être plus spécifique ?"
    
    def _handle_system_command(self, command: str) -> str:
        """Gère les commandes système"""
        if "ferme" in command or "arrête" in command:
            return "Commandes de fermeture détectées. Cette fonctionnalité sera bientôt disponible."
        elif "éteint" in command or "shutdown" in command:
            return "Commande d'extinction détectée. Cette fonctionnalité sera bientôt disponible."
        elif "redémarre" in command or "restart" in command:
            return "Commande de redémarrage détectée. Cette fonctionnalité sera bientôt disponible."
        else:
            return "Commande système non reconnue."
    
    def _handle_info_command(self, command: str) -> str:
        """Gère les commandes d'information"""
        now = datetime.now()
        
        if "heure" in command:
            return f"Il est actuellement {now.strftime('%H:%M:%S')}."
        elif "date" in command or "jour" in command:
            return f"Nous sommes le {now.strftime('%d/%m/%Y')} ({now.strftime('%A')})."
        else:
            return f"Nous sommes le {now.strftime('%d/%m/%Y')} et il est {now.strftime('%H:%M:%S')}."
    
    def start_listening(self):
        """Démarre l'écoute vocale"""
        self.listening = True
        self.logger.info("🎤 Écoute vocale démarrée")
        # TODO: Implémenter la reconnaissance vocale
        if self.ui_window:
            self.ui_window.add_response("status", "Écoute vocale activée (fonctionnalité en développement)")
    
    def stop_listening(self):
        """Arrête l'écoute vocale"""
        self.listening = False
        self.logger.info("🎤 Écoute vocale arrêtée")
        if self.ui_window:
            self.ui_window.add_response("status", "Écoute vocale désactivée")
    
    def shutdown(self):
        """Arrêter l'assistant proprement"""
        self.logger.info("🛑 Arrêt d'ARIA...")
        self.running = False
        
        try:
            # Fermer l'interface si elle existe
            if hasattr(self, 'ui_window') and self.ui_window:
                try:
                    self.ui_window.quit()
                except:
                    pass
            
            # Fermer les composants
            if self.response_engine:
                try:
                    self.response_engine.shutdown()
                except:
                    pass
            
            self.logger.info("✅ ARIA arrêté proprement")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'arrêt: {e}")

# Point d'entrée principal
def main():
    """Fonction principale"""
    # Vérifier les paramètres de ligne de commande
    import argparse
    parser = argparse.ArgumentParser(description="ARIA - Assistant IA Conversationnel")
    parser.add_argument("--test", action="store_true", help="Lancer en mode test")
    parser.add_argument("--debug", action="store_true", help="Activer le mode debug")
    parser.add_argument("--no-gui", action="store_true", help="Désactiver l'interface graphique")
    args = parser.parse_args()
    
    # Configurer le logging en mode debug si demandé
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n🤖 ARIA - Assistant IA Conversationnel Avancé")
    print("=" * 50)
    
    # En mode test, juste vérifier que les modules sont disponibles
    if args.test:
        print("\nTest des modules disponibles :")
        print(f"- Interface graphique: {'✅ Disponible' if ARIAMainWindow else '❌ Non disponible'}")
        print(f"- Contrôleur système: {'✅ Disponible' if SystemController else '❌ Non disponible'}")
        print(f"- Moteur de réponse: {'✅ Disponible' if ResponseEngine else '❌ Non disponible'}")
        return
    
    try:
        # Créer et initialiser l'assistant
        aria = ARIAAssistant()
        aria.initialize()
        
        # Désactiver l'interface graphique si demandé
        if args.no_gui and aria.ui_window:
            aria.ui_window = None
        
        # Démarrer l'assistant
        aria.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Démarrer ARIA
    main()
