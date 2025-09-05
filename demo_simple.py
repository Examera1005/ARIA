#!/usr/bin/env python3
"""
🎮 Démo ARIA Simplifiée - Modules Disponibles
============================================

Démo des modules disponibles sans dépendances complexes.
"""

import asyncio
import time
import logging
import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🎮 DÉMO ARIA SIMPLIFIÉE                   ║
    ║              Modules Disponibles - Tests Pratiques           ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def test_system_controller():
    """Test le contrôleur système"""
    print("\n" + "="*50)
    print("🖥️  TEST: CONTRÔLEUR SYSTÈME")
    print("="*50)
    
    try:
        from automation.system_controller import SystemController
        
        controller = SystemController()
        print("✅ SystemController initialisé")
        
        # Liste des applications disponibles
        apps = controller.get_available_applications()
        print(f"📱 Applications découvertes: {len(apps)}")
        
        # Affiche quelques applications
        for i, app in enumerate(apps[:5]):
            print(f"   {i+1}. {app}")
        
        if len(apps) > 5:
            print(f"   ... et {len(apps) - 5} autres")
        
        print("\n🧪 Test d'ouverture d'application...")
        print("   Tentative d'ouverture du bloc-notes...")
        
        if controller.open_application("notepad"):
            print("✅ Bloc-notes ouvert avec succès!")
            time.sleep(2)
            
            print("   Fermeture du bloc-notes...")
            if controller.close_application("notepad"):
                print("✅ Bloc-notes fermé avec succès!")
            else:
                print("❌ Échec fermeture bloc-notes")
        else:
            print("❌ Échec ouverture bloc-notes")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_web_automation():
    """Test l'automation web"""
    print("\n" + "="*50)
    print("🌐 TEST: AUTOMATION WEB")
    print("="*50)
    
    try:
        from automation.web_automation import WebAutomation
        
        print("⚙️  Initialisation WebAutomation (mode visible)...")
        web = WebAutomation({'headless': False})
        print("✅ WebAutomation initialisé")
        
        print("\n🚀 Démarrage du navigateur Chrome...")
        if web.start_browser('chrome'):
            print("✅ Navigateur démarré!")
            
            print("\n🔍 Test navigation vers Google...")
            if web.navigate_to("https://www.google.com"):
                print("✅ Navigation vers Google réussie!")
                
                print("\n📸 Prise de capture d'écran...")
                if web.take_screenshot("test_google.png"):
                    print("✅ Capture d'écran sauvée: test_google.png")
                
                print("\n⏳ Attendre 3 secondes...")
                time.sleep(3)
            else:
                print("❌ Échec navigation vers Google")
            
            print("\n🔒 Fermeture du navigateur...")
            web.close_browser()
            print("✅ Navigateur fermé")
        else:
            print("❌ Impossible de démarrer le navigateur")
            print("💡 Assurez-vous que Chrome est installé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("💡 Installez Selenium: pip install selenium")
        return False

def test_window_manager():
    """Test le gestionnaire de fenêtres"""
    print("\n" + "="*50)
    print("🪟 TEST: GESTIONNAIRE DE FENÊTRES")
    print("="*50)
    
    try:
        from automation.window_manager import WindowManager
        
        wm = WindowManager()
        print("✅ WindowManager initialisé")
        
        print("\n🔍 Recherche des fenêtres ouvertes...")
        windows = wm.get_visible_windows()
        print(f"📱 Fenêtres trouvées: {len(windows)}")
        
        # Affiche les fenêtres
        for i, window in enumerate(windows[:5]):
            print(f"   {i+1}. {window.title[:50]}...")
        
        if len(windows) > 5:
            print(f"   ... et {len(windows) - 5} autres")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def interactive_demo():
    """Mode interactif simplifié"""
    print("\n" + "="*50)
    print("🎮 MODE INTERACTIF SIMPLIFIÉ")
    print("="*50)
    
    print("\nCommandes disponibles:")
    print("  • 'system' - Test contrôleur système")
    print("  • 'web' - Test automation web")
    print("  • 'windows' - Test gestionnaire fenêtres")
    print("  • 'all' - Tous les tests")
    print("  • 'quit' - Quitter")
    
    while True:
        try:
            choice = input("\n🎯 Votre choix > ").strip().lower()
            
            if choice in ['quit', 'q', 'exit']:
                print("👋 Au revoir!")
                break
            elif choice == 'system':
                test_system_controller()
            elif choice == 'web':
                test_web_automation()
            elif choice == 'windows':
                test_window_manager()
            elif choice == 'all':
                print("🚀 Exécution de tous les tests...")
                test_system_controller()
                test_web_automation() 
                test_window_manager()
                print("\n🎉 Tous les tests terminés!")
            else:
                print("❌ Commande non reconnue")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    setup_logging()
    print_banner()
    
    print("🔍 Vérification des modules disponibles...")
    
    modules = {
        'SystemController': False,
        'WebAutomation': False,
        'WindowManager': False
    }
    
    # Test SystemController
    try:
        from automation.system_controller import SystemController
        modules['SystemController'] = True
        print("✅ SystemController disponible")
    except Exception as e:
        print(f"❌ SystemController: {e}")
    
    # Test WebAutomation
    try:
        from automation.web_automation import WebAutomation
        modules['WebAutomation'] = True
        print("✅ WebAutomation disponible")
    except Exception as e:
        print(f"❌ WebAutomation: {e}")
    
    # Test WindowManager
    try:
        from automation.window_manager import WindowManager
        modules['WindowManager'] = True
        print("✅ WindowManager disponible")
    except Exception as e:
        print(f"❌ WindowManager: {e}")
    
    available = sum(modules.values())
    total = len(modules)
    
    print(f"\n📊 Modules disponibles: {available}/{total}")
    
    if available == 0:
        print("❌ Aucun module disponible!")
        return
    
    print("\n🎮 Démarrage du mode interactif...")
    interactive_demo()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Démo interrompue")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
