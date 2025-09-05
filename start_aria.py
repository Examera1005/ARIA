#!/usr/bin/env python3
"""
🚀 Script de démarrage rapide pour ARIA
=====================================

Ce script lance ARIA avec toutes ses capacités avancées.
"""

import sys
import os
import logging
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Vérifie que les dépendances critiques sont installées"""
    critical_deps = [
        'pyautogui',
        'selenium', 
        'psutil',
        'keyboard',
        'mouse'
    ]
    
    missing_deps = []
    
    for dep in critical_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    if missing_deps:
        print("❌ Dépendances manquantes détectées:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n🔧 Exécutez 'install_dependencies.bat' pour installer les dépendances.")
        print("   Ou installez manuellement: pip install " + " ".join(missing_deps))
        return False
    
    return True

def setup_logging():
    """Configure le logging pour ARIA"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "aria.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def print_banner():
    """Affiche la bannière ARIA"""
    banner = """
    ██████╗ ███████╗██╗  ██╗██╗██╗████╗
   ██╔══██╗██╔══██║██║  ██║██║██║████║
   ██████╔╝█████╔╝ ██║  ██║██║██║ ██╔╝
   ██╔══██╗██╔══██╗██║  ██║██║██║ ██║ 
   ██║  ██║██║  ██║██║  ██║██║██║ ██║
   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝ ╚═╝

   🤖 Assistant IA Conversationnel Avancé
   =====================================
   
   ✨ Capacités:
   • 💻 Contrôle complet du système
   • 🌐 Automation web intelligente  
   • 📧 Gestion emails et calendrier
   • 🎯 Exécution de tâches complexes
   • 🎤 Reconnaissance vocale
   • 🗣️ Synthèse vocale
   
   🚀 Version: 2.0 - AI Enhanced
   """
    print(banner)

def main():
    """Fonction principale de démarrage"""
    print_banner()
    
    print("🔍 Vérification des dépendances...")
    if not check_dependencies():
        return 1
    
    print("✅ Toutes les dépendances sont disponibles!")
    
    print("📝 Configuration du logging...")
    setup_logging()
    
    print("🚀 Démarrage d'ARIA...")
    
    try:
        # Import et démarrage d'ARIA
        from main import ARIAAssistant
        
        # Créer et initialiser l'assistant
        aria = ARIAAssistant()
        aria.initialize()
        
        # Démarrer ARIA
        aria.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
        return 0
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("🔧 Certains modules peuvent être manquants. Exécutez install_dependencies.bat")
        return 1
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
