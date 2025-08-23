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
from pathlib import Path
import threading
import queue
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Ajouter le chemin du projet
sys.path.append(str(Path(__file__).parent))

# Imports des modules ARIA
from core.speech_engine import SpeechEngine
from core.nlp_processor import NLPProcessor
from core.intent_analyzer import IntentAnalyzer
from core.response_generator import ResponseGenerator
from automation.system_controller import SystemController
from automation.app_controller import AppController
from modules.email_manager import EmailManager
from modules.calendar_manager import CalendarManager
from modules.social_manager import SocialManager
from apis.openai_client import OpenAIClient
from ui.main_window import ARIAWindow
from config.settings import ARIAConfig
from core.logger import setup_logger

class ARIAAssistant:
    """Assistant IA Principal"""
    
    def __init__(self):
        """Initialiser ARIA"""
        self.config = ARIAConfig()
        self.logger = setup_logger("ARIA")
        self.running = False
        self.listening = False
        
        # File d'attente pour les commandes
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Composants principaux
        self.speech_engine = None
        self.nlp_processor = None
        self.intent_analyzer = None
        self.response_generator = None
        self.system_controller = None
        self.app_controller = None
        
        # Gestionnaires de services
        self.email_manager = None
        self.calendar_manager = None
        self.social_manager = None
        
        # Clients API
        self.openai_client = None
        
        # Interface utilisateur
        self.ui_window = None
        
        # Contexte de conversation
        self.conversation_context = {
            "history": [],
            "current_task": None,
            "user_preferences": {},
            "active_sessions": {}
        }
        
        self.logger.info("🤖 ARIA Assistant initialisé")
    
    async def initialize(self):
        """Initialiser tous les composants"""
        self.logger.info("🚀 Initialisation des composants ARIA...")
        
        try:
            # Initialiser les composants principaux
            self.speech_engine = SpeechEngine(self.config)
            await self.speech_engine.initialize()
            
            self.nlp_processor = NLPProcessor(self.config)
            await self.nlp_processor.initialize()
            
            self.intent_analyzer = IntentAnalyzer(self.config)
            self.response_generator = ResponseGenerator(self.config)
            
            # Initialiser les contrôleurs système
            self.system_controller = SystemController(self.config)
            self.app_controller = AppController(self.config)
            
            # Initialiser les gestionnaires de services
            self.email_manager = EmailManager(self.config)
            self.calendar_manager = CalendarManager(self.config)
            self.social_manager = SocialManager(self.config)
            
            # Initialiser les clients API
            self.openai_client = OpenAIClient(self.config)
            
            # Initialiser l'interface utilisateur
            if self.config.ui_enabled:
                self.ui_window = ARIAWindow(self)
            
            # Charger les préférences utilisateur
            await self.load_user_preferences()
            
            self.logger.info("✅ Tous les composants initialisés avec succès")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            raise
    
    async def start(self):
        """Démarrer l'assistant"""
        self.logger.info("🎯 Démarrage d'ARIA...")
        self.running = True
        
        # Démarrer les tâches asynchrones
        tasks = [
            self.voice_listener_task(),
            self.command_processor_task(),
            self.response_handler_task(),
            self.background_monitor_task()
        ]
        
        # Démarrer l'interface utilisateur si activée
        if self.ui_window:
            tasks.append(self.ui_task())
        
        # Message de bienvenue
        await self.speak("Bonjour ! Je suis ARIA, votre assistant IA. Je vous écoute.")
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("🛑 Arrêt demandé par l'utilisateur")
        except Exception as e:
            self.logger.error(f"❌ Erreur dans la boucle principale: {e}")
        finally:
            await self.shutdown()
    
    async def voice_listener_task(self):
        """Tâche d'écoute vocale continue"""
        self.logger.info("🎤 Démarrage de l'écoute vocale...")
        
        while self.running:
            try:
                if self.config.voice_enabled and self.listening:
                    # Écouter une commande vocale
                    audio_data = await self.speech_engine.listen()
                    
                    if audio_data:
                        # Transcrire l'audio en texte
                        text = await self.speech_engine.transcribe(audio_data)
                        
                        if text and len(text.strip()) > 0:
                            self.logger.info(f"🎤 Commande reçue: '{text}'")
                            
                            # Ajouter à la file des commandes
                            command = {
                                "type": "voice",
                                "text": text,
                                "timestamp": datetime.now(),
                                "source": "voice"
                            }
                            self.command_queue.put(command)
                
                # Pause pour éviter la surcharge CPU
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"❌ Erreur dans l'écoute vocale: {e}")
                await asyncio.sleep(1)
    
    async def command_processor_task(self):
        """Tâche de traitement des commandes"""
        self.logger.info("⚙️ Démarrage du processeur de commandes...")
        
        while self.running:
            try:
                if not self.command_queue.empty():
                    command = self.command_queue.get()
                    await self.process_command(command)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"❌ Erreur dans le traitement des commandes: {e}")
                await asyncio.sleep(1)
    
    async def process_command(self, command: Dict[str, Any]):
        """Traiter une commande"""
        try:
            text = command["text"]
            self.logger.info(f"🔄 Traitement: '{text}'")
            
            # Ajouter à l'historique
            self.conversation_context["history"].append({
                "user": text,
                "timestamp": command["timestamp"]
            })
            
            # Analyser l'intention avec l'IA
            intent_result = await self.intent_analyzer.analyze(
                text, 
                self.conversation_context
            )
            
            self.logger.info(f"🎯 Intention détectée: {intent_result['intent']}")
            
            # Exécuter l'action correspondante
            response = await self.execute_intent(intent_result)
            
            # Ajouter la réponse à la file
            if response:
                self.response_queue.put({
                    "type": "response",
                    "text": response["text"],
                    "actions": response.get("actions", []),
                    "timestamp": datetime.now()
                })
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du traitement de la commande: {e}")
            error_response = "Désolé, j'ai rencontré une erreur en traitant votre demande."
            self.response_queue.put({
                "type": "error",
                "text": error_response,
                "timestamp": datetime.now()
            })
    
    async def execute_intent(self, intent_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Exécuter une intention"""
        intent = intent_result["intent"]
        entities = intent_result.get("entities", {})
        confidence = intent_result.get("confidence", 0.0)
        
        self.logger.info(f"🔧 Exécution: {intent} (confiance: {confidence:.2f})")
        
        try:
            # CONTRÔLE SYSTÈME
            if intent == "open_application":
                app_name = entities.get("app_name")
                if app_name:
                    success = await self.app_controller.open_application(app_name)
                    if success:
                        return {"text": f"J'ai ouvert {app_name} pour vous."}
                    else:
                        return {"text": f"Impossible d'ouvrir {app_name}. L'application est-elle installée ?"}
            
            elif intent == "close_application":
                app_name = entities.get("app_name")
                if app_name:
                    success = await self.app_controller.close_application(app_name)
                    if success:
                        return {"text": f"J'ai fermé {app_name}."}
                    else:
                        return {"text": f"Impossible de fermer {app_name}."}
            
            elif intent == "system_command":
                command_type = entities.get("command_type")
                if command_type == "shutdown":
                    await self.speak("Je vais éteindre l'ordinateur dans 30 secondes.")
                    await self.system_controller.shutdown(delay=30)
                    return {"text": "Extinction programmée dans 30 secondes."}
                elif command_type == "restart":
                    await self.speak("Je vais redémarrer l'ordinateur dans 30 secondes.")
                    await self.system_controller.restart(delay=30)
                    return {"text": "Redémarrage programmé dans 30 secondes."}
                elif command_type == "lock":
                    await self.system_controller.lock_screen()
                    return {"text": "Écran verrouillé."}
            
            # GESTION EMAIL
            elif intent == "send_email":
                recipient = entities.get("recipient")
                subject = entities.get("subject") 
                content = entities.get("content")
                
                if recipient and subject and content:
                    success = await self.email_manager.send_email(
                        to=recipient,
                        subject=subject,
                        body=content
                    )
                    if success:
                        return {"text": f"Email envoyé à {recipient}."}
                    else:
                        return {"text": "Erreur lors de l'envoi de l'email."}
                else:
                    # Demander les informations manquantes
                    return {"text": "Pouvez-vous me préciser le destinataire, le sujet et le contenu de l'email ?"}
            
            elif intent == "check_emails":
                emails = await self.email_manager.get_recent_emails(limit=5)
                if emails:
                    summary = f"Vous avez {len(emails)} nouveaux emails:\\n"
                    for email in emails:
                        summary += f"- {email['subject']} de {email['sender']}\\n"
                    return {"text": summary}
                else:
                    return {"text": "Aucun nouvel email."}
            
            # GESTION CALENDRIER
            elif intent == "schedule_event":
                title = entities.get("title")
                date = entities.get("date")
                time = entities.get("time")
                
                if title and date:
                    success = await self.calendar_manager.create_event(
                        title=title,
                        date=date,
                        time=time
                    )
                    if success:
                        return {"text": f"Événement '{title}' programmé pour le {date}."}
                    else:
                        return {"text": "Erreur lors de la création de l'événement."}
            
            elif intent == "check_calendar":
                events = await self.calendar_manager.get_today_events()
                if events:
                    summary = f"Vous avez {len(events)} événements aujourd'hui:\\n"
                    for event in events:
                        summary += f"- {event['title']} à {event['time']}\\n"
                    return {"text": summary}
                else:
                    return {"text": "Aucun événement prévu aujourd'hui."}
            
            # RÉSEAUX SOCIAUX
            elif intent == "post_social":
                platform = entities.get("platform")
                content = entities.get("content")
                
                if platform and content:
                    success = await self.social_manager.post_content(platform, content)
                    if success:
                        return {"text": f"Message publié sur {platform}."}
                    else:
                        return {"text": f"Erreur lors de la publication sur {platform}."}
            
            # CONVERSATION GÉNÉRALE
            elif intent == "general_question":
                # Utiliser OpenAI pour répondre
                response_text = await self.openai_client.get_response(
                    intent_result["original_text"],
                    context=self.conversation_context
                )
                return {"text": response_text}
            
            # CONTRÔLE ARIA
            elif intent == "start_listening":
                self.listening = True
                return {"text": "Je vous écoute maintenant."}
            
            elif intent == "stop_listening":
                self.listening = False
                return {"text": "J'arrête d'écouter. Dites 'ARIA écoute-moi' pour reprendre."}
            
            elif intent == "aria_status":
                status = await self.get_system_status()
                return {"text": f"Statut ARIA: {status}"}
            
            else:
                # Intention non reconnue
                return {"text": "Je ne suis pas sûr de comprendre. Pouvez-vous reformuler ?"}
        
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'exécution de l'intention {intent}: {e}")
            return {"text": "Une erreur s'est produite lors de l'exécution de la commande."}
    
    async def response_handler_task(self):
        """Tâche de gestion des réponses"""
        self.logger.info("📢 Démarrage du gestionnaire de réponses...")
        
        while self.running:
            try:
                if not self.response_queue.empty():
                    response = self.response_queue.get()
                    await self.handle_response(response)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"❌ Erreur dans la gestion des réponses: {e}")
                await asyncio.sleep(1)
    
    async def handle_response(self, response: Dict[str, Any]):
        """Gérer une réponse"""
        try:
            text = response["text"]
            actions = response.get("actions", [])
            
            # Réponse vocale
            if self.config.voice_enabled:
                await self.speak(text)
            
            # Affichage dans l'interface
            if self.ui_window:
                self.ui_window.add_message("ARIA", text)
            
            # Ajouter à l'historique
            self.conversation_context["history"].append({
                "aria": text,
                "timestamp": response["timestamp"]
            })
            
            # Exécuter les actions supplémentaires
            for action in actions:
                await self.execute_action(action)
            
            self.logger.info(f"📢 Réponse: '{text}'")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la gestion de la réponse: {e}")
    
    async def speak(self, text: str):
        """Synthèse vocale"""
        try:
            if self.speech_engine and self.config.voice_enabled:
                await self.speech_engine.speak(text)
        except Exception as e:
            self.logger.error(f"❌ Erreur synthèse vocale: {e}")
    
    async def background_monitor_task(self):
        """Surveillance en arrière-plan"""
        while self.running:
            try:
                # Vérifier les notifications importantes
                await self.check_notifications()
                
                # Sauvegarder les préférences périodiquement
                await self.save_user_preferences()
                
                # Attendre 60 secondes
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"❌ Erreur surveillance: {e}")
                await asyncio.sleep(60)
    
    async def ui_task(self):
        """Tâche de l'interface utilisateur"""
        if self.ui_window:
            await self.ui_window.run()
    
    async def check_notifications(self):
        """Vérifier les notifications importantes"""
        try:
            # Vérifier nouveaux emails importantes
            important_emails = await self.email_manager.get_important_emails()
            for email in important_emails:
                await self.speak(f"Email important reçu de {email['sender']}: {email['subject']}")
            
            # Vérifier événements imminents
            upcoming_events = await self.calendar_manager.get_upcoming_events(minutes=15)
            for event in upcoming_events:
                await self.speak(f"Rappel: {event['title']} dans 15 minutes")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification notifications: {e}")
    
    async def load_user_preferences(self):
        """Charger les préférences utilisateur"""
        try:
            prefs_file = Path(self.config.data_dir) / "user_preferences.json"
            if prefs_file.exists():
                import json
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    self.conversation_context["user_preferences"] = json.load(f)
                self.logger.info("✅ Préférences utilisateur chargées")
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement préférences: {e}")
    
    async def save_user_preferences(self):
        """Sauvegarder les préférences utilisateur"""
        try:
            prefs_file = Path(self.config.data_dir) / "user_preferences.json"
            import json
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_context["user_preferences"], f, 
                         indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde préférences: {e}")
    
    async def get_system_status(self) -> str:
        """Obtenir le statut du système"""
        try:
            status_parts = []
            
            # Statut vocal
            if self.listening:
                status_parts.append("écoute active")
            else:
                status_parts.append("écoute désactivée")
            
            # Statut des services
            if self.email_manager and self.email_manager.is_connected():
                status_parts.append("email connecté")
            
            if self.calendar_manager and self.calendar_manager.is_connected():
                status_parts.append("calendrier connecté")
            
            # Utilisation système
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            status_parts.append(f"CPU {cpu_percent:.1f}%")
            status_parts.append(f"Mémoire {memory_percent:.1f}%")
            
            return ", ".join(status_parts)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur statut système: {e}")
            return "statut indisponible"
    
    async def execute_action(self, action: Dict[str, Any]):
        """Exécuter une action supplémentaire"""
        try:
            action_type = action.get("type")
            
            if action_type == "open_url":
                url = action.get("url")
                if url:
                    await self.system_controller.open_url(url)
            
            elif action_type == "create_file":
                filepath = action.get("filepath")
                content = action.get("content", "")
                if filepath:
                    await self.system_controller.create_file(filepath, content)
            
            # Ajouter d'autres actions selon les besoins
            
        except Exception as e:
            self.logger.error(f"❌ Erreur exécution action: {e}")
    
    async def shutdown(self):
        """Arrêter l'assistant proprement"""
        self.logger.info("🛑 Arrêt d'ARIA...")
        self.running = False
        
        try:
            # Sauvegarder les données
            await self.save_user_preferences()
            
            # Fermer les connexions
            if self.email_manager:
                await self.email_manager.close()
            
            if self.calendar_manager:
                await self.calendar_manager.close()
            
            if self.social_manager:
                await self.social_manager.close()
            
            # Message d'au revoir
            await self.speak("Au revoir ! À bientôt.")
            
            self.logger.info("✅ ARIA arrêté proprement")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'arrêt: {e}")

# Point d'entrée principal
async def main():
    """Fonction principale"""
    print("🤖 ARIA - Assistant IA Conversationnel Avancé")
    print("=" * 50)
    
    try:
        # Créer et initialiser l'assistant
        aria = ARIAAssistant()
        await aria.initialize()
        
        # Démarrer l'assistant
        await aria.start()
        
    except KeyboardInterrupt:
        print("\\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Démarrer ARIA
    asyncio.run(main())
