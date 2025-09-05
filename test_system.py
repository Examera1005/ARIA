#!/usr/bin/env python3
"""
Test rapide du contrôleur système ARIA
"""

from automation.system_controller import SystemController
import time

print("🖥️ Test Contrôleur Système ARIA")
print("="*40)

# Initialisation
controller = SystemController()
print("✅ Contrôleur initialisé")

# Applications disponibles
apps = controller.get_available_applications()
print(f"📱 {len(apps)} applications découvertes")

print("\nTop 10 applications:")
for i, app in enumerate(apps[:10]):
    print(f"  {i+1:2}. {app}")

# Test ouverture du bloc-notes
print("\n🧪 Test ouverture du bloc-notes...")
if controller.open_application('notepad'):
    print("✅ Bloc-notes ouvert avec succès!")
    
    print("⏳ Attente 3 secondes...")
    time.sleep(3)
    
    print("🔒 Fermeture du bloc-notes...")
    if controller.close_application('notepad'):
        print("✅ Bloc-notes fermé avec succès!")
    else:
        print("❌ Échec fermeture du bloc-notes")
else:
    print("❌ Échec ouverture du bloc-notes")

# Test calculatrice
print("\n🧮 Test ouverture de la calculatrice...")
if controller.open_application('calculator'):
    print("✅ Calculatrice ouverte!")
    time.sleep(2)
    
    if controller.close_application('calculator'):
        print("✅ Calculatrice fermée!")
    else:
        print("❌ Échec fermeture calculatrice")
else:
    print("❌ Échec ouverture calculatrice")

print("\n🎉 Tests terminés!")
