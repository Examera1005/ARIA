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
    from core.response_engine import ResponseEngine
except ImportError:
    ResponseEngine = None

try:
    from automation.system_controller import SystemController
except ImportError:
    SystemController = None

class ARIAAssistant:
    """Assistant IA Principal"""
    
    def __init__(self):
        """Initialiser ARIA"""
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
        
        # Interface utilisateur
        self.ui_window = None
        
        # Contexte de conversation
        self.conversation_context = {
            "history": [],
            "current_task": None,
            "user_preferences": {},
            "active_sessions": {}
        }
        
        # Créer les dossiers nécessaires s'ils n'existent pas
        os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(__file__), "config"), exist_ok=True)
        
        self.logger.info("🤖 ARIA Assistant initialisé")
    
    def initialize(self):
        """Initialiser tous les composants"""
        self.logger.info("🚀 Initialisation des composants ARIA...")
        
        try:
            # Initialiser les composants disponibles
            if SystemController:
                self.system_controller = SystemController()
            
            if ResponseEngine:
                self.response_engine = ResponseEngine()
            
            # Initialiser l'interface utilisateur
            if ARIAMainWindow:
                self.ui_window = ARIAMainWindow()
                # Connecter les callbacks
                self.ui_window.set_callback('on_command', self.process_command)
                self.ui_window.set_callback('on_start_listening', self.start_listening)
                self.ui_window.set_callback('on_stop_listening', self.stop_listening)
                self.ui_window.add_response("text", "Bonjour ! Je suis ARIA, votre assistant IA. Comment puis-je vous aider ?")
            
            self.logger.info("✅ Composants disponibles initialisés avec succès")
            
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
    
    def process_command(self, command: str):
        """Traite une commande utilisateur"""
        self.logger.info(f"Traitement de la commande: {command}")
        
        try:
            # Ajouter à l'historique
            self.conversation_context["history"].append({
                "timestamp": datetime.now().isoformat(),
                "type": "user_command",
                "content": command
            })
            
            # Traitement de base des commandes
            command_lower = command.lower().strip()
            response = None
            
            # Commandes d'ouverture d'applications
            if any(word in command_lower for word in ["ouvre", "lance", "démarre", "ouvrir", "lancer"]):
                response = self._handle_app_launch_command(command_lower)
            
            # Commandes système
            elif any(word in command_lower for word in ["ferme", "arrête", "éteint", "redémarre"]):
                response = self._handle_system_command(command_lower)
            
            # Commandes d'information
            elif any(word in command_lower for word in ["quelle heure", "quel jour", "date", "temps"]):
                response = self._handle_info_command(command_lower)
            
            # Commandes générales
            else:
                response = f"Je comprends votre demande '{command}'. Cette fonctionnalité sera bientôt disponible."
            
            # Envoyer la réponse à l'interface
            if self.ui_window and response:
                self.ui_window.add_response("text", response)
                
                # Synthèse vocale si disponible
                if self.response_engine:
                    try:
                        self.response_engine.speak(response)
                    except Exception as e:
                        self.logger.error(f"Erreur synthèse vocale: {e}")
            
        except Exception as e:
            self.logger.error(f"Erreur traitement commande: {e}")
            if self.ui_window:
                self.ui_window.add_response("error", f"Erreur lors du traitement: {e}")
    
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
