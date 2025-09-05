#!/usr/bin/env python3
"""
Test rapide de l'automation web ARIA
"""

import time
from automation.web_automation import WebAutomation

print("🌐 Test Automation Web ARIA")
print("="*40)

# Initialisation
web = WebAutomation({'headless': False})
print("✅ WebAutomation initialisé")

try:
    print("\n🚀 Démarrage du navigateur Chrome...")
    if web.start_browser('chrome'):
        print("✅ Navigateur Chrome démarré!")
        
        print("\n📍 Navigation vers Google...")
        if web.navigate_to("https://www.google.com"):
            print("✅ Navigation vers Google réussie!")
            
            print("\n🔍 Test recherche 'Hello World'...")
            result_url = web.search_google("Hello World", 1)
            if result_url:
                print(f"✅ Premier résultat trouvé: {result_url[:60]}...")
            else:
                print("❌ Aucun résultat trouvé")
            
            print("\n📸 Capture d'écran...")
            if web.take_screenshot("test_web.png"):
                print("✅ Capture sauvée: test_web.png")
            
            print("\n⏳ Attente 3 secondes...")
            time.sleep(3)
        else:
            print("❌ Échec navigation vers Google")
        
        print("\n🔒 Fermeture du navigateur...")
        web.close_browser()
        print("✅ Navigateur fermé")
    else:
        print("❌ Impossible de démarrer le navigateur")
        print("💡 Vérifiez que Chrome est installé")

except Exception as e:
    print(f"❌ Erreur: {e}")
    if web.driver:
        web.close_browser()

print("\n🎉 Test terminé!")
