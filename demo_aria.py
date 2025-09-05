#!/usr/bin/env python3
"""
🎮 Démo ARIA - Exemples d'utilisation avancée
============================================

Ce script démontre toutes les capacités d'ARIA avec des exemples concrets.
"""

import asyncio
import time
import logging
from pathlib import Path
import sys

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_demo_logging():
    """Configure le logging pour la démo"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def print_demo_header():
    """Affiche l'en-tête de la démo"""
    header = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🎮 DÉMO ARIA - IA AVANCÉE                 ║
    ║              Assistant IA Conversationnel Complet            ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Cette démo vous montre toutes les capacités d'ARIA :       ║
    ║  • 💻 Contrôle système et applications                       ║
    ║  • 🌐 Automation web intelligente                            ║
    ║  • 🎯 Exécution de tâches complexes                          ║
    ║  • 📧 Gestion emails et communication                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(header)

async def demo_system_control():
    """Démontre le contrôle système"""
    print("\n" + "="*60)
    print("🖥️  DÉMO 1: CONTRÔLE SYSTÈME")
    print("="*60)
    
    try:
        from automation.task_executor import AITaskExecutor
        
        executor = AITaskExecutor()
        
        demos = [
            "ouvre le bloc-notes",
            "prends une capture d'écran", 
            "ferme le bloc-notes"
        ]
        
        for i, task in enumerate(demos, 1):
            print(f"\n[{i}/3] Test: '{task}'")
            print("⏳ Exécution en cours...")
            
            result = await executor.execute_task(task)
            
            if result.success:
                print(f"✅ Succès: {result.message}")
            else:
                print(f"❌ Erreur: {result.message}")
            
            await asyncio.sleep(2)
            
    except ImportError as e:
        print(f"❌ Module non disponible: {e}")
        print("💡 Installez les dépendances avec: pip install pyautogui psutil")

async def demo_web_automation():
    """Démontre l'automation web"""
    print("\n" + "="*60)
    print("🌐 DÉMO 2: AUTOMATION WEB")
    print("="*60)
    
    try:
        from automation.web_automation import WebAutomation
        
        web = WebAutomation({'headless': False})
        
        print("\n[1/3] Test: Démarrage du navigateur")
        if web.start_browser('chrome'):
            print("✅ Navigateur Chrome démarré")
            
            print("\n[2/3] Test: Recherche Google")
            url = web.search_google("python programming", 1)
            if url:
                print(f"✅ Premier résultat trouvé: {url[:50]}...")
            else:
                print("❌ Aucun résultat trouvé")
            
            print("\n[3/3] Test: Capture d'écran")
            if web.take_screenshot("demo_screenshot.png"):
                print("✅ Capture d'écran sauvée: demo_screenshot.png")
            
            await asyncio.sleep(3)
            web.close_browser()
            print("🔒 Navigateur fermé")
        else:
            print("❌ Impossible de démarrer le navigateur")
            
    except ImportError as e:
        print(f"❌ Module non disponible: {e}")
        print("💡 Installez Selenium avec: pip install selenium")

async def demo_ai_task_execution():
    """Démontre l'exécution de tâches IA complexes"""
    print("\n" + "="*60)
    print("🤖 DÉMO 3: EXÉCUTION DE TÂCHES IA")
    print("="*60)
    
    try:
        from automation.task_executor import AITaskExecutor
        
        executor = AITaskExecutor()
        
        complex_tasks = [
            "ouvre firefox et va sur google",
            "cherche des vidéos de chats sur youtube et choisis la deuxième",
            "prends une capture d'écran de la page"
        ]
        
        for i, task in enumerate(complex_tasks, 1):
            print(f"\n[{i}/{len(complex_tasks)}] Tâche complexe: '{task}'")
            print("🧠 Analyse et planification IA...")
            
            result = await executor.execute_task(task)
            
            if result.success:
                print(f"✅ Tâche complétée: {result.message}")
                if result.steps_completed:
                    print(f"📋 Étapes exécutées: {len(result.steps_completed)}")
                print(f"⏱️ Temps d'exécution: {result.execution_time:.2f}s")
            else:
                print(f"❌ Échec: {result.message}")
            
            await asyncio.sleep(2)
            
    except ImportError as e:
        print(f"❌ Module non disponible: {e}")

async def demo_intent_analysis():
    """Démontre l'analyse d'intentions"""
    print("\n" + "="*60)
    print("🧠 DÉMO 4: ANALYSE D'INTENTIONS IA")
    print("="*60)
    
    try:
        from core.intent_analyzer import IntentAnalyzer
        
        analyzer = IntentAnalyzer({})
        
        test_phrases = [
            "ouvre firefox et va sur youtube",
            "ferme toutes les fenêtres chrome",
            "lis mes emails de support@exemple.com",
            "cherche cat video sur google et prends la deuxième vidéo",
            "éteins l'ordinateur dans 5 minutes"
        ]
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n[{i}/{len(test_phrases)}] Analyse: '{phrase}'")
            
            result = analyzer.analyze(phrase)
            
            if result:
                print(f"🎯 Intention détectée: {result.intent}")
                print(f"📊 Confiance: {result.confidence:.2f}")
                if result.entities:
                    print(f"🏷️  Entités: {result.entities}")
            else:
                print("❌ Intention non reconnue")
            
    except ImportError as e:
        print(f"❌ Module non disponible: {e}")

def demo_configuration():
    """Démontre le système de configuration"""
    print("\n" + "="*60)
    print("⚙️  DÉMO 5: SYSTÈME DE CONFIGURATION")
    print("="*60)
    
    try:
        from config.settings import ARIAConfig
        
        config = ARIAConfig()
        
        print("📋 Configuration actuelle:")
        print(f"   • Navigateur préféré: {config.get('web.browser_preference', 'Non défini')}")
        print(f"   • Mode headless: {config.get('web.headless_browser', False)}")
        print(f"   • Timeout web: {config.get('web.wait_timeout', 10)}s")
        print(f"   • Automation activée: {config.is_feature_enabled('web_automation')}")
        print(f"   • Contrôle système: {config.is_feature_enabled('system_control')}")
        
        print("\n🔧 Test modification configuration:")
        original_browser = config.get('web.browser_preference')
        
        if config.set('web.browser_preference', 'firefox'):
            print(f"   ✅ Navigateur changé: {original_browser} → firefox")
            
            # Restaurer la valeur originale
            config.set('web.browser_preference', original_browser)
            print(f"   🔄 Valeur restaurée: firefox → {original_browser}")
        
    except ImportError as e:
        print(f"❌ Module non disponible: {e}")

def demo_file_structure():
    """Affiche la structure du projet"""
    print("\n" + "="*60)
    print("📁 STRUCTURE DU PROJET ARIA")
    print("="*60)
    
    structure = """
    ARIA/
    ├── 🚀 start_aria.py          # Lanceur principal
    ├── 🤖 main.py                # Assistant principal  
    ├── 📦 install_dependencies.bat # Installation automatique
    ├── 📋 requirements.txt       # Dépendances Python
    │
    ├── automation/               # 🎯 Modules d'automation
    │   ├── task_executor.py      #   → Exécuteur de tâches IA
    │   ├── web_automation.py     #   → Automation web (Selenium)
    │   ├── system_controller.py  #   → Contrôle système Windows
    │   └── window_manager.py     #   → Gestion des fenêtres
    │
    ├── core/                     # 🧠 Moteurs IA
    │   ├── intent_analyzer.py    #   → Analyse d'intentions NLP
    │   ├── response_engine.py    #   → Génération de réponses
    │   └── speech_engine.py      #   → Reconnaissance vocale
    │
    ├── apis/                     # 🌐 Intégrations externes
    │   ├── gmail_manager.py      #   → Gestion Gmail
    │   └── calendar_manager.py   #   → Calendrier Google
    │
    ├── ui/                       # 🎨 Interface utilisateur
    │   └── main_window.py        #   → Interface graphique
    │
    ├── config/                   # ⚙️ Configuration
    │   └── settings.py           #   → Paramètres centralisés
    │
    └── logs/                     # 📝 Journaux et données
        └── aria.log              #   → Logs d'exécution
    """
    
    print(structure)

async def demo_interactive_mode():
    """Mode interactif de démonstration"""
    print("\n" + "="*60)
    print("🎮 MODE INTERACTIF")
    print("="*60)
    
    print("\nCommandes disponibles:")
    print("  • 'system' - Démo contrôle système")
    print("  • 'web' - Démo automation web")
    print("  • 'ai' - Démo tâches IA complexes")
    print("  • 'intent' - Démo analyse d'intentions")
    print("  • 'config' - Démo configuration")
    print("  • 'structure' - Structure du projet")
    print("  • 'all' - Toutes les démos")
    print("  • 'quit' - Quitter")
    
    while True:
        try:
            choice = input("\n🎯 Votre choix > ").strip().lower()
            
            if choice == 'quit' or choice == 'q':
                print("👋 Au revoir !")
                break
            elif choice == 'system':
                await demo_system_control()
            elif choice == 'web':
                await demo_web_automation()
            elif choice == 'ai':
                await demo_ai_task_execution()
            elif choice == 'intent':
                await demo_intent_analysis()
            elif choice == 'config':
                demo_configuration()
            elif choice == 'structure':
                demo_file_structure()
            elif choice == 'all':
                await demo_system_control()
                await demo_web_automation()
                await demo_ai_task_execution()
                await demo_intent_analysis()
                demo_configuration()
                demo_file_structure()
            else:
                print("❌ Commande non reconnue. Tapez 'quit' pour quitter.")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

async def main():
    """Fonction principale de la démo"""
    setup_demo_logging()
    print_demo_header()
    
    print("\n🔍 Vérification des modules...")
    
    # Vérifier les modules critiques
    modules_status = {
        'automation.task_executor': '❓',
        'automation.web_automation': '❓', 
        'automation.system_controller': '❓',
        'core.intent_analyzer': '❓',
        'config.settings': '❓'
    }
    
    for module_name in modules_status:
        try:
            __import__(module_name)
            modules_status[module_name] = '✅'
        except ImportError:
            modules_status[module_name] = '❌'
    
    print("\n📊 Status des modules:")
    for module, status in modules_status.items():
        print(f"   {status} {module}")
    
    available_modules = sum(1 for status in modules_status.values() if status == '✅')
    total_modules = len(modules_status)
    
    print(f"\n📈 Modules disponibles: {available_modules}/{total_modules}")
    
    if available_modules == 0:
        print("❌ Aucun module disponible. Installez les dépendances avec:")
        print("   install_dependencies.bat")
        return
    
    print("\n🎮 Démarrage du mode interactif...")
    await demo_interactive_mode()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Démo interrompue par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
