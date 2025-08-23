"""
⚙️ Configuration ARIA - Assistant IA Conversationnel
==================================================

Configuration complète pour toutes les fonctionnalités d'ARIA
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json

@dataclass
class ARIAConfig:
    """Configuration principale d'ARIA"""
    
    # ===== CONFIGURATION GÉNÉRALE =====
    app_name: str = "ARIA"
    version: str = "1.0.0"
    debug: bool = True
    
    # Répertoires
    base_dir: str = field(default_factory=lambda: str(Path(__file__).parent.parent))
    data_dir: str = field(default_factory=lambda: str(Path(__file__).parent.parent / "data"))
    logs_dir: str = field(default_factory=lambda: str(Path(__file__).parent.parent / "logs"))
    
    # ===== RECONNAISSANCE VOCALE =====
    voice_enabled: bool = True
    
    # Moteurs de reconnaissance
    use_google_sr: bool = True
    use_vosk: bool = False  # Offline (nécessite téléchargement de modèle)
    vosk_model_path: str = "models/vosk-model-fr-0.22"
    
    # Paramètres audio
    listen_timeout: float = 5.0
    phrase_time_limit: float = 10.0
    energy_threshold: int = 4000
    
    # ===== SYNTHÈSE VOCALE =====
    tts_rate: int = 180  # Vitesse de parole (mots par minute)
    tts_volume: float = 0.9  # Volume (0.0 - 1.0)
    test_on_startup: bool = False  # Test vocal au démarrage
    
    # ===== APIs EXTERNES =====
    
    # OpenAI (pour GPT et Whisper)
    openai_api_key: str = ""  # À configurer
    openai_model: str = "gpt-3.5-turbo"
    
    # Google APIs
    google_credentials_file: str = "config/google_credentials.json"
    
    # Azure Speech Services
    azure_speech_key: str = ""  # À configurer
    azure_speech_region: str = "francecentral"
    
    # Gmail API
    gmail_enabled: bool = False
    gmail_scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ])
    
    # Calendar API
    calendar_enabled: bool = False
    calendar_scopes: List[str] = field(default_factory=lambda: [
        'https://www.googleapis.com/auth/calendar'
    ])
    
    # ===== RÉSEAUX SOCIAUX =====
    
    # Twitter/X
    twitter_enabled: bool = False
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_token_secret: str = ""
    
    # Discord
    discord_enabled: bool = False
    discord_bot_token: str = ""
    
    # Telegram
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    
    # ===== INTERFACE UTILISATEUR =====
    ui_enabled: bool = True
    ui_theme: str = "dark"  # dark, light, auto
    ui_width: int = 800
    ui_height: int = 600
    
    # ===== AUTOMATION SYSTÈME =====
    
    # Permissions
    allow_system_shutdown: bool = True
    allow_file_operations: bool = True
    allow_app_control: bool = True
    
    # Applications favorites (ouverture rapide)
    favorite_apps: Dict[str, str] = field(default_factory=lambda: {
        "chrome": "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "firefox": "C:/Program Files/Mozilla Firefox/firefox.exe", 
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "powerpoint": "powerpnt.exe",
        "explorer": "explorer.exe"
    })
    
    # ===== NOTIFICATIONS =====
    notifications_enabled: bool = True
    email_notifications: bool = True
    calendar_notifications: bool = True
    system_notifications: bool = True
    
    # ===== SÉCURITÉ =====
    
    # Authentification
    require_confirmation_for: List[str] = field(default_factory=lambda: [
        "system_shutdown", "system_restart", "file_delete", "email_send"
    ])
    
    # Commandes interdites  
    blocked_commands: List[str] = field(default_factory=lambda: [
        "format", "rmdir /s", "del /s", "rd /s"
    ])
    
    # ===== PERFORMANCE =====
    max_concurrent_tasks: int = 5
    response_timeout: float = 30.0
    cache_enabled: bool = True
    cache_size: int = 1000
    
    # ===== LOGGING =====
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_to_file: bool = True
    log_to_console: bool = True
    max_log_files: int = 10
    max_log_size_mb: int = 10
    
    # ===== FONCTIONNALITÉS AVANCÉES =====
    
    # Apprentissage
    learning_enabled: bool = True
    save_conversations: bool = True
    personalization_enabled: bool = True
    
    # Contexte
    context_window_size: int = 10
    remember_preferences: bool = True
    
    # Proactivité
    proactive_suggestions: bool = True
    background_monitoring: bool = True
    
    def __post_init__(self):
        """Initialisation après création"""
        self._create_directories()
        self._load_environment_variables()
    
    def _create_directories(self):
        """Créer les répertoires nécessaires"""
        directories = [
            self.data_dir,
            self.logs_dir,
            os.path.join(self.base_dir, "models", "saved"),
            os.path.join(self.base_dir, "config", "credentials")
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _load_environment_variables(self):
        """Charger les variables d'environnement"""
        # OpenAI
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Azure
        if not self.azure_speech_key:
            self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY", "")
        
        # Twitter
        if not self.twitter_api_key:
            self.twitter_api_key = os.getenv("TWITTER_API_KEY", "")
            self.twitter_api_secret = os.getenv("TWITTER_API_SECRET", "")
            self.twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
            self.twitter_access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
        
        # Discord
        if not self.discord_bot_token:
            self.discord_bot_token = os.getenv("DISCORD_BOT_TOKEN", "")
        
        # Telegram
        if not self.telegram_bot_token:
            self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ARIAConfig':
        """Charger la configuration depuis un fichier JSON"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return cls(**config_dict)
    
    def save_to_file(self, config_path: str):
        """Sauvegarder la configuration dans un fichier JSON"""
        # Convertir en dictionnaire en excluant les méthodes
        config_dict = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_') and not callable(value):
                config_dict[key] = value
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    def validate(self) -> List[str]:
        """Valider la configuration et retourner les erreurs"""
        errors = []
        
        # Vérifier les clés API
        if self.voice_enabled and not any([
            self.use_google_sr,
            self.use_vosk and Path(self.vosk_model_path).exists(),
            self.azure_speech_key,
            self.openai_api_key
        ]):
            errors.append("Aucun moteur de reconnaissance vocale configuré")
        
        # Vérifier les APIs externes
        if self.gmail_enabled and not Path(self.google_credentials_file).exists():
            errors.append("Fichier de credentials Google manquant pour Gmail")
        
        if self.calendar_enabled and not Path(self.google_credentials_file).exists():
            errors.append("Fichier de credentials Google manquant pour Calendar")
        
        # Vérifier les répertoires
        if not Path(self.data_dir).exists():
            errors.append(f"Répertoire de données manquant: {self.data_dir}")
        
        return errors
    
    def get_enabled_features(self) -> List[str]:
        """Obtenir la liste des fonctionnalités activées"""
        features = []
        
        if self.voice_enabled:
            features.append("Reconnaissance vocale")
        
        if self.gmail_enabled:
            features.append("Gmail")
        
        if self.calendar_enabled:
            features.append("Calendrier Google")
        
        if self.twitter_enabled:
            features.append("Twitter/X")
        
        if self.discord_enabled:
            features.append("Discord")
        
        if self.telegram_enabled:
            features.append("Telegram")
        
        if self.ui_enabled:
            features.append("Interface graphique")
        
        if self.notifications_enabled:
            features.append("Notifications")
        
        if self.learning_enabled:
            features.append("Apprentissage automatique")
        
        return features
    
    def update_from_dict(self, updates: Dict[str, Any]):
        """Mettre à jour la configuration depuis un dictionnaire"""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        config_dict = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_') and not callable(value):
                config_dict[key] = value
        return config_dict
    
    def reset_to_defaults(self):
        """Réinitialiser aux valeurs par défaut"""
        default_config = ARIAConfig()
        for key, value in default_config.__dict__.items():
            if not key.startswith('_'):
                setattr(self, key, value)
    
    def copy(self) -> 'ARIAConfig':
        """Créer une copie de la configuration"""
        return ARIAConfig(**self.to_dict())

# Configuration par défaut pour les tests
def create_test_config() -> ARIAConfig:
    """Créer une configuration de test"""
    config = ARIAConfig()
    config.debug = True
    config.voice_enabled = False  # Désactiver pour les tests
    config.ui_enabled = False
    config.test_on_startup = False
    return config

# Configuration minimale
def create_minimal_config() -> ARIAConfig:
    """Créer une configuration minimale"""
    config = ARIAConfig()
    config.voice_enabled = False
    config.ui_enabled = False
    config.gmail_enabled = False
    config.calendar_enabled = False
    config.twitter_enabled = False
    config.discord_enabled = False
    config.telegram_enabled = False
    config.notifications_enabled = False
    return config
