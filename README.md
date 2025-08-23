# ARIA - Assistant IA Conversationnel Avancé

![ARIA Logo](https://img.shields.io/badge/ARIA-Assistant%20IA-blue) 
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

ARIA est un assistant IA conversationnel avancé capable de comprendre le langage naturel, d'exploiter des APIs externes (Gmail, calendrier, réseaux sociaux), de contrôler votre PC Windows, et de répondre vocalement. Il combine reconnaissance vocale, traitement du langage naturel, et automation système dans une interface moderne.

## ✨ Fonctionnalités Principales

### 🎤 **Reconnaissance Vocale Multi-Moteur**
- Support de Vosk (offline), Google Speech, Azure Cognitive Services, OpenAI Whisper
- Détection de mots-clés d'activation (wake words)
- Calibration automatique du microphone
- Évaluation de la confiance des transcriptions

### 🧠 **Intelligence Artificielle Avancée**
- Analyse d'intentions avec patterns regex et modèles Transformers
- Support d'OpenAI GPT pour l'enrichissement contextuel
- Extraction d'entités (applications, dates, emails, etc.)
- Gestion de contexte conversationnel

### 🖥️ **Contrôle Système Windows**
- Ouverture/fermeture d'applications
- Gestion avancée des fenêtres (redimensionnement, positionnement, arrangements)
- Manipulation de fichiers et dossiers
- Exécution de commandes système sécurisées
- Capture d'écran et informations système

### 📧 **Intégration APIs Externes**
- **Gmail** : Envoi, réception, gestion des emails avec pièces jointes
- **Google Calendar** : Création, modification, consultation d'événements
- Support extensible pour autres APIs (WhatsApp, réseaux sociaux)

### 🎨 **Interface Utilisateur Moderne**
- GUI moderne avec CustomTkinter (thème sombre/clair)
- Interface conversationnelle intuitive
- Sauvegarde des conversations
- Paramètres personnalisables

### 🔊 **Synthèse Vocale Multi-Moteur**
- Support de pyttsx3, Azure TTS, Google TTS
- Voix françaises de qualité
- Gestion de la queue de synthèse
- Paramètres vocaux configurables

## 🚀 Installation

### 1. Prérequis
- Python 3.8 ou supérieur
- Windows 10/11
- Microphone fonctionnel
- Haut-parleurs ou casque

### 2. Installation des dépendances

```bash
# Clone ou télécharge le projet
cd C:\Users\theli\ARIA

# Installation des dépendances principales
pip install -r requirements.txt

# Pour une installation complète avec toutes les fonctionnalités
pip install vosk speechrecognition pyaudio google-api-python-client google-auth-httplib2 google-auth-oauthlib azure-cognitiveservices-speech gtts pygame customtkinter transformers torch openai psutil pywin32 pillow pytz
```

### 3. Configuration des APIs (Optionnel)

#### Google APIs (Gmail/Calendar)
1. Créez un projet sur [Google Cloud Console](https://console.cloud.google.com/)
2. Activez les APIs Gmail et Calendar
3. Créez des credentials OAuth 2.0
4. Téléchargez le fichier `credentials.json` dans le dossier `config/`

#### Azure Cognitive Services
1. Créez un compte [Azure](https://azure.microsoft.com/fr-fr/)
2. Créez un service Cognitive Services
3. Récupérez votre clé API et région
4. Configurez dans `config/settings.py`

#### OpenAI (Optionnel)
1. Créez un compte [OpenAI](https://openai.com/)
2. Générez une clé API
3. Configurez dans `config/settings.py`

## 📋 Configuration

### Configuration de Base
Éditez le fichier `config/settings.py` :

```python
# Configuration ARIA
config = ARIAConfig(
    # Reconnaissance vocale
    speech_recognition_engine="vosk",  # vosk, google, azure, whisper
    
    # Synthèse vocale
    text_to_speech_engine="pyttsx3",   # pyttsx3, azure, gtts
    
    # APIs (optionnel)
    openai_api_key="votre_clé_openai",
    azure_speech_key="votre_clé_azure",
    azure_speech_region="westeurope",
    
    # Interface
    gui_enabled=True,
    theme="dark",
    
    # Sécurité
    safe_mode=True,
    confirm_dangerous_actions=True
)
```

### Configuration Vocale
Les paramètres vocaux sont configurables via l'interface ou le fichier `config/voice_settings.json` :

```json
{
  "engine": "pyttsx3",
  "voice_id": "",
  "rate": 200,
  "volume": 0.8,
  "language": "fr-FR",
  "gender": "female"
}
```

## 🎯 Utilisation

### Lancement d'ARIA

```bash
# Lancement avec interface graphique
python main.py

# Lancement en mode console
python main.py --no-gui

# Lancement avec configuration spécifique
python main.py --config custom_config.py
```

### Commandes Vocales Exemple

ARIA comprend le langage naturel français. Voici quelques exemples :

#### **Contrôle Applications**
- "Ouvre le bloc-notes"
- "Lance Chrome"
- "Ferme Word"
- "Minimise toutes les fenêtres"

#### **Gestion Email**
- "Lis mes emails non lus"
- "Envoie un email à contact@example.com"
- "Recherche les emails de Pierre"
- "Archive ce message"

#### **Calendrier**
- "Quels sont mes rendez-vous aujourd'hui ?"
- "Crée un événement demain à 14h"
- "Trouve un créneau libre cette semaine"
- "Annule mon meeting de 15h"

#### **Système**
- "Quelles applications sont ouvertes ?"
- "Informations système"
- "Prends une capture d'écran"
- "Recherche le fichier projet.docx"

### Interface Graphique

L'interface ARIA propose :

- **Zone de conversation** : Historique des échanges
- **Saisie textuelle** : Alternative à la commande vocale
- **Bouton microphone** : Activation/désactivation de l'écoute
- **Contrôles** : Effacer, sauvegarder, paramètres
- **Indicateurs** : État d'écoute, traitement en cours

**Raccourcis clavier :**
- `Ctrl+L` : Activer/désactiver le microphone
- `Ctrl+S` : Sauvegarder la conversation
- `Ctrl+Q` : Quitter
- `Échap` : Arrêter l'écoute vocale

## 🏗️ Architecture

```
ARIA/
├── main.py                    # Point d'entrée principal
├── core/                      # Moteur principal
│   ├── speech_engine.py       # Reconnaissance vocale
│   ├── intent_analyzer.py     # Analyse des intentions
│   └── response_engine.py     # Synthèse vocale
├── automation/                # Contrôle système
│   ├── system_controller.py   # Gestion applications
│   └── window_manager.py      # Gestion fenêtres
├── apis/                      # Intégrations externes
│   ├── gmail_manager.py       # API Gmail
│   └── calendar_manager.py    # API Calendar
├── ui/                        # Interface utilisateur
│   └── main_window.py         # GUI principale
├── config/                    # Configuration
│   └── settings.py            # Paramètres ARIA
├── data/                      # Données
├── logs/                      # Journaux
└── requirements.txt           # Dépendances
```

## 🔧 Développement et Extension

### Ajouter de Nouvelles Commandes

1. **Patterns d'intention** dans `core/intent_analyzer.py` :
```python
intent_patterns['nouvelle_action'] = [
    r'fais (.*)',
    r'exécute (.*)',
    r'lance (.*)' 
]
```

2. **Gestionnaire de commande** dans `main.py` :
```python
async def handle_nouvelle_action(self, entities):
    # Votre logique ici
    return "Action exécutée avec succès"
```

### Ajouter de Nouvelles APIs

1. Créez un nouveau fichier dans `apis/`
2. Implémentez votre classe de gestionnaire
3. Ajoutez l'import dans `apis/__init__.py`
4. Intégrez dans le moteur principal

### Personnaliser l'Interface

L'interface utilise CustomTkinter pour un look moderne. Vous pouvez :
- Modifier les thèmes dans `ui/main_window.py`
- Ajouter de nouveaux widgets
- Personnaliser les couleurs et polices

## 📈 Performance et Optimisation

### Recommandations
- **RAM** : 4 GB minimum, 8 GB recommandé
- **CPU** : Processeur multi-cœur pour les modèles IA
- **Stockage** : 2 GB d'espace libre
- **Réseau** : Connexion internet pour APIs cloud

### Optimisations
- Mode offline avec Vosk pour la reconnaissance vocale
- Cache des modèles IA localement
- Réglage des timeouts et seuils de confiance

## 🛡️ Sécurité

ARIA intègre plusieurs mesures de sécurité :

- **Mode sécurisé** : Bloque les commandes dangereuses
- **Confirmation** : Demande validation pour actions critiques
- **Logs** : Traçabilité complète des actions
- **Isolation** : Exécution sécurisée des commandes système

### Commandes Bloquées par Défaut
- Suppression de fichiers système
- Modification du registre Windows
- Commandes réseau dangereuses
- Arrêt/redémarrage système sans confirmation

## 🐛 Dépannage

### Problèmes Courants

#### **Reconnaissance Vocale ne Fonctionne Pas**
- Vérifiez que le microphone est connecté et autorisé
- Testez avec différents moteurs (vosk, google)
- Ajustez la sensibilité dans les paramètres

#### **Erreurs d'API Gmail/Calendar**
- Vérifiez que `credentials.json` est présent
- Ré-autorisez l'application si nécessaire
- Vérifiez la connectivité internet

#### **Interface ne s'Affiche Pas**
- Installez CustomTkinter : `pip install customtkinter`
- Essayez le mode console : `python main.py --no-gui`

#### **Synthèse Vocale Silencieuse**
- Vérifiez le volume système et ARIA
- Testez différents moteurs TTS
- Vérifiez que les haut-parleurs fonctionnent

### Logs et Debug

Les logs sont disponibles dans `logs/aria.log` :

```bash
# Afficher les logs récents
tail -f logs/aria.log

# Mode debug
python main.py --debug
```

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créez une Pull Request

### Guidelines
- Code Python conforme à PEP 8
- Documentation complète des nouvelles fonctions
- Tests unitaires pour les nouvelles fonctionnalités
- Logs appropriés pour le debug

## 📝 Changelog

### Version 1.0.0 (2024)
- ✅ Reconnaissance vocale multi-moteur
- ✅ Analyse d'intentions IA avancée  
- ✅ Contrôle système Windows complet
- ✅ Intégration Gmail et Calendar
- ✅ Interface graphique moderne
- ✅ Synthèse vocale multi-moteur
- ✅ Configuration flexible
- ✅ Mode sécurisé

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **OpenAI** pour les modèles de langage
- **Google** pour les APIs Speech et Calendar
- **Microsoft** pour Azure Cognitive Services
- **Python Community** pour les excellentes bibliothèques
- **CustomTkinter** pour l'interface moderne

## 📞 Support

Pour toute question ou problème :

- 📧 Email : support@aria-assistant.com
- 🐛 Issues : [GitHub Issues](https://github.com/votre-nom/aria/issues)
- 📖 Documentation : [Wiki](https://github.com/votre-nom/aria/wiki)

---

**ARIA - Votre Assistant IA Personnel** 🤖✨

*"L'intelligence artificielle au service de votre productivité"*
