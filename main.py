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
