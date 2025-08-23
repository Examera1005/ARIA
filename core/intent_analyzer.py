"""
🧠 Analyseur d'Intentions Avancé
==============================

Système d'IA pour comprendre les intentions des utilisateurs :
- Reconnaissance d'intentions complexes
- Extraction d'entités (noms, dates, lieux, etc.)
- Analyse contextuelle
- Support multi-langues (français principal)
"""

import asyncio
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import spacy
from dataclasses import dataclass

# Tentative d'import des modèles NLP avancés
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class IntentResult:
    """Résultat de l'analyse d'intention"""
    intent: str
    entities: Dict[str, Any]
    confidence: float
    original_text: str
    context_used: bool = False
    suggestions: List[str] = None

class IntentAnalyzer:
    """Analyseur d'intentions avancé avec IA"""
    
    def __init__(self, config):
        """Initialiser l'analyseur d'intentions"""
        self.config = config
        self.logger = logging.getLogger("ARIA.Intent")
        
        # Modèles NLP
        self.nlp = None  # SpaCy
        self.intent_classifier = None  # Transformers
        
        # Base de connaissances des intentions
        self.intent_patterns = self.load_intent_patterns()
        self.entity_extractors = self.load_entity_extractors()
        
        # Cache des résultats récents
        self.recent_intents = {}
        self.context_memory = []
        
        self.logger.info("🧠 Analyseur d'intentions initialisé")
    
    def load_intent_patterns(self) -> Dict[str, List[str]]:
        """Charger les patterns d'intentions"""
        return {
            # CONTRÔLE SYSTÈME
            "open_application": [
                r"ouvr(ir|e|ez) (.+)",
                r"lanc(er|e|ez) (.+)", 
                r"démarre(?:r)? (.+)",
                r"affiche(?:r)? (.+)",
                r"va sur (.+)",
                r"ouvre (.+) s'il te plaît",
                r"peux-tu ouvrir (.+)",
            ],
            
            "close_application": [
                r"ferm(er|e|ez) (.+)",
                r"quitt(er|e|ez) (.+)",
                r"arrêt(er|e|ez) (.+)",
                r"stoppe(?:r)? (.+)",
                r"termine(?:r)? (.+)",
            ],
            
            "system_command": [
                r"éteins? (?:l')?ordinateur",
                r"arrête (?:l')?ordinateur", 
                r"shut ?down",
                r"redémarre (?:l')?ordinateur",
                r"restart",
                r"verrouille (?:l')?écran",
                r"lock",
                r"met(?:s)? en veille",
            ],
            
            # EMAIL
            "send_email": [
                r"envoi(e|er) un e-?mail à (.+)",
                r"écris un mail à (.+)",
                r"compose un message pour (.+)",
                r"contact(er?) (.+) par e-?mail",
                r"envoi(e|er) un message à (.+)",
            ],
            
            "check_emails": [
                r"vérifie (?:mes )?e-?mails?",
                r"regarde (?:mes )?messages?",
                r"as-tu reçu (?:des )?e-?mails?",
                r"nouveaux? e-?mails?",
                r"check (?:my )?emails?",
            ],
            
            # CALENDRIER
            "schedule_event": [
                r"programme (?:un )?(?:rendez-vous|rdv|événement|meeting) (.+)",
                r"ajoute (.+) à (?:mon )?calendrier",
                r"planifie (.+)",
                r"crée (?:un )?événement (.+)",
                r"rappelle-moi de (.+)",
            ],
            
            "check_calendar": [
                r"qu'est-ce que j'ai (?:aujourd'hui|demain|cette semaine)",
                r"mes rendez-vous",
                r"mon planning",
                r"vérifie (?:mon )?calendrier",
                r"what's on my calendar",
            ],
            
            # RÉSEAUX SOCIAUX
            "post_social": [
                r"publie (.+) sur (.+)",
                r"poste (.+) sur (.+)",
                r"partage (.+) sur (.+)",
                r"tweete (.+)",
                r"mets à jour (?:mon )?statut",
            ],
            
            # RECHERCHE ET INFORMATION
            "web_search": [
                r"recherche (.+)",
                r"cherche (.+) sur (?:google|internet|le web)",
                r"trouve (?:moi )?(.+)",
                r"google (.+)",
                r"search (?:for )?(.+)",
            ],
            
            "get_weather": [
                r"météo",
                r"temps qu'il fait",
                r"prévisions météo",
                r"weather",
                r"il fait quel temps",
            ],
            
            "get_news": [
                r"actualités?",
                r"nouvelles?",
                r"infos?",
                r"news",
                r"que se passe-t-il",
            ],
            
            # MULTIMÉDIA
            "play_music": [
                r"joue (?:de la )?musique",
                r"lance (.+) sur spotify",
                r"mets (.+)",
                r"play (.+)",
                r"écoute(?:r)? (.+)",
            ],
            
            "control_volume": [
                r"monte le son",
                r"baisse le son",
                r"volume à (\d+)",
                r"mute",
                r"coupe le son",
            ],
            
            # CONTRÔLE ARIA
            "start_listening": [
                r"aria écoute(?:-moi)?",
                r"commence à écouter",
                r"active(?:r)? (?:l')?écoute",
                r"hey aria",
                r"salut aria",
            ],
            
            "stop_listening": [
                r"arrête d'écouter",
                r"désactive (?:l')?écoute",
                r"stop (?:listening)?",
                r"silence",
                r"chut",
            ],
            
            "aria_status": [
                r"statut",
                r"état du système",
                r"comment ça va",
                r"status",
                r"how are you",
            ],
            
            # AIDE ET CONVERSATION
            "help": [
                r"aide(?:-moi)?",
                r"help",
                r"que peux-tu faire",
                r"commandes disponibles",
                r"comment ça marche",
            ],
            
            "greeting": [
                r"bonjour",
                r"salut",
                r"hello",
                r"bonsoir",
                r"bonne nuit",
                r"hi",
            ],
            
            "farewell": [
                r"au revoir",
                r"bye",
                r"à bientôt",
                r"goodbye",
                r"see you",
            ],
            
            # QUESTION GÉNÉRALE (fallback)
            "general_question": [
                r"(.+)\?",  # Toute question
                r"dis-moi (.+)",
                r"explique (.+)",
                r"comment (.+)",
                r"pourquoi (.+)",
                r"qu'est-ce que (.+)",
            ]
        }
    
    def load_entity_extractors(self) -> Dict[str, List[str]]:
        """Charger les extracteurs d'entités"""
        return {
            "apps": [
                "chrome", "firefox", "edge", "safari",
                "word", "excel", "powerpoint", "outlook",
                "notepad", "calculator", "paint",
                "spotify", "vlc", "steam", "discord",
                "skype", "zoom", "teams", "slack",
                "photoshop", "illustrator", "premiere",
                "visual studio", "vscode", "pycharm",
                "file explorer", "explorateur",
            ],
            
            "social_platforms": [
                "twitter", "facebook", "instagram", "linkedin",
                "tiktok", "youtube", "snapchat", "discord",
                "whatsapp", "telegram", "messenger"
            ],
            
            "time_expressions": [
                r"aujourd'hui", r"demain", r"après-demain",
                r"cette semaine", r"la semaine prochaine",
                r"ce mois", r"le mois prochain",
                r"dans (\d+) (?:heure|minute|jour|semaine|mois)s?",
                r"à (\d{1,2}h\d{2}|\d{1,2}:\d{2})",
                r"le (\d{1,2})/(\d{1,2})",
            ],
            
            "email_addresses": [
                r"[\w\.-]+@[\w\.-]+\.\w+",
            ],
            
            "names": [
                r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)*"
            ]
        }
    
    async def analyze(self, text: str, context: Dict[str, Any] = None) -> IntentResult:
        """Analyser l'intention d'un texte"""
        try:
            self.logger.info(f"🔍 Analyse: '{text}'")
            
            # Nettoyer et normaliser le texte
            clean_text = self.preprocess_text(text)
            
            # Essayer plusieurs méthodes de reconnaissance
            results = []
            
            # 1. Reconnaissance par patterns
            pattern_result = await self.analyze_with_patterns(clean_text)
            if pattern_result:
                results.append(pattern_result)
            
            # 2. Reconnaissance avec modèle Transformers
            if TRANSFORMERS_AVAILABLE and self.intent_classifier:
                transformer_result = await self.analyze_with_transformers(clean_text)
                if transformer_result:
                    results.append(transformer_result)
            
            # 3. Reconnaissance avec OpenAI
            if OPENAI_AVAILABLE and self.config.openai_api_key:
                openai_result = await self.analyze_with_openai(clean_text, context)
                if openai_result:
                    results.append(openai_result)
            
            # 4. Analyse contextuelle
            context_result = await self.analyze_with_context(clean_text, context)
            if context_result:
                results.append(context_result)
            
            # Sélectionner le meilleur résultat
            best_result = self.select_best_result(results)
            
            if not best_result:
                # Fallback : question générale
                best_result = IntentResult(
                    intent="general_question",
                    entities={"query": clean_text},
                    confidence=0.3,
                    original_text=text
                )
            
            # Extraire les entités
            best_result.entities.update(
                await self.extract_entities(clean_text, best_result.intent)
            )
            
            # Ajouter au cache et contexte
            self.add_to_cache(text, best_result)
            self.update_context(text, best_result, context)
            
            self.logger.info(f"✅ Intention: {best_result.intent} ({best_result.confidence:.2f})")
            
            return best_result
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse intention: {e}")
            return IntentResult(
                intent="unknown",
                entities={},
                confidence=0.0,
                original_text=text
            )
    
    def preprocess_text(self, text: str) -> str:
        """Préprocesser le texte"""
        # Nettoyer
        text = text.strip().lower()
        
        # Normaliser les caractères
        replacements = {
            "à": "a", "é": "e", "è": "e", "ê": "e", "ë": "e",
            "î": "i", "ï": "i", "ô": "o", "ù": "u", "û": "u", "ü": "u",
            "ç": "c", "ñ": "n"
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    async def analyze_with_patterns(self, text: str) -> Optional[IntentResult]:
        """Analyser avec des patterns regex"""
        best_match = None
        best_confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Calculer la confiance basée sur la qualité du match
                    confidence = len(match.group(0)) / len(text)
                    confidence = min(confidence * 1.2, 1.0)  # Bonus pour patterns
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        
                        # Extraire les groupes capturés
                        entities = {}
                        if match.groups():
                            if intent in ["open_application", "close_application"]:
                                entities["app_name"] = match.groups()[0]
                            elif intent == "send_email":
                                entities["recipient"] = match.groups()[0]
                            elif intent == "schedule_event":
                                entities["title"] = match.groups()[0]
                        
                        best_match = IntentResult(
                            intent=intent,
                            entities=entities,
                            confidence=confidence,
                            original_text=text
                        )
        
        return best_match
    
    async def analyze_with_transformers(self, text: str) -> Optional[IntentResult]:
        """Analyser avec un modèle Transformers"""
        try:
            if not self.intent_classifier:
                return None
            
            result = self.intent_classifier(text)
            
            return IntentResult(
                intent=result[0]['label'].lower(),
                entities={},
                confidence=result[0]['score'],
                original_text=text
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erreur Transformers: {e}")
            return None
    
    async def analyze_with_openai(self, text: str, context: Dict[str, Any] = None) -> Optional[IntentResult]:
        """Analyser avec OpenAI GPT"""
        try:
            # Construire le prompt
            prompt = self.build_openai_prompt(text, context)
            
            client = openai.OpenAI(api_key=self.config.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parser la réponse JSON
            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)
            
            return IntentResult(
                intent=result_data.get("intent", "unknown"),
                entities=result_data.get("entities", {}),
                confidence=result_data.get("confidence", 0.8),
                original_text=text,
                context_used=True
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erreur OpenAI: {e}")
            return None
    
    def build_openai_prompt(self, text: str, context: Dict[str, Any] = None) -> Dict[str, str]:
        """Construire le prompt pour OpenAI"""
        system_prompt = """Tu es ARIA, un assistant IA expert en analyse d'intentions.
        
        Intentions disponibles:
        - open_application: ouvrir une application
        - close_application: fermer une application  
        - system_command: commandes système (shutdown, restart, lock)
        - send_email: envoyer un email
        - check_emails: vérifier les emails
        - schedule_event: programmer un événement
        - check_calendar: consulter le calendrier
        - post_social: publier sur réseaux sociaux
        - web_search: recherche web
        - get_weather: météo
        - get_news: actualités
        - play_music: jouer de la musique
        - control_volume: contrôler le volume
        - start_listening: activer l'écoute
        - stop_listening: désactiver l'écoute
        - aria_status: statut du système
        - help: demande d'aide
        - greeting: salutation
        - farewell: au revoir
        - general_question: question générale
        
        Réponds UNIQUEMENT en JSON avec:
        {
          "intent": "nom_intention",
          "entities": {"entité1": "valeur1", "entité2": "valeur2"},
          "confidence": 0.95
        }"""
        
        user_prompt = f"Analyse cette phrase: '{text}'"
        
        # Ajouter le contexte si disponible
        if context and context.get("history"):
            recent_history = context["history"][-3:]  # 3 derniers échanges
            history_text = "\\n".join([
                f"User: {h.get('user', '')}" for h in recent_history if h.get('user')
            ])
            user_prompt += f"\\n\\nContexte récent:\\n{history_text}"
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    async def analyze_with_context(self, text: str, context: Dict[str, Any] = None) -> Optional[IntentResult]:
        """Analyser en utilisant le contexte conversationnel"""
        if not context or not context.get("history"):
            return None
        
        try:
            # Chercher des patterns de continuation
            recent_exchanges = context["history"][-5:]  # 5 derniers échanges
            
            # Détection de réponses courtes avec contexte
            if len(text.split()) <= 3:
                # Chercher une question récente d'ARIA
                for exchange in reversed(recent_exchanges):
                    aria_msg = exchange.get("aria", "")
                    if "?" in aria_msg:
                        # C'est probablement une réponse à une question
                        if "destinataire" in aria_msg or "à qui" in aria_msg:
                            return IntentResult(
                                intent="send_email",
                                entities={"recipient": text},
                                confidence=0.8,
                                original_text=text,
                                context_used=True
                            )
                        elif "sujet" in aria_msg:
                            return IntentResult(
                                intent="send_email", 
                                entities={"subject": text},
                                confidence=0.8,
                                original_text=text,
                                context_used=True
                            )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse contextuelle: {e}")
            return None
    
    async def extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """Extraire les entités du texte"""
        entities = {}
        
        try:
            # Extraction selon l'intention
            if intent in ["open_application", "close_application"]:
                app_name = self.extract_app_name(text)
                if app_name:
                    entities["app_name"] = app_name
            
            elif intent == "system_command":
                command_type = self.extract_system_command(text)
                if command_type:
                    entities["command_type"] = command_type
            
            elif intent == "send_email":
                email_entities = self.extract_email_entities(text)
                entities.update(email_entities)
            
            elif intent == "schedule_event":
                event_entities = self.extract_event_entities(text)
                entities.update(event_entities)
            
            elif intent == "post_social":
                social_entities = self.extract_social_entities(text)
                entities.update(social_entities)
            
            # Extraction d'entités génériques
            entities.update(self.extract_generic_entities(text))
            
        except Exception as e:
            self.logger.error(f"❌ Erreur extraction entités: {e}")
        
        return entities
    
    def extract_app_name(self, text: str) -> Optional[str]:
        """Extraire le nom d'application"""
        for app in self.entity_extractors["apps"]:
            if app.lower() in text.lower():
                return app
        
        # Extraction par pattern
        patterns = [
            r"ouvr(?:ir|e|ez) (.+?)(?:\s|$)",
            r"lanc(?:er|e|ez) (.+?)(?:\s|$)",
            r"ferm(?:er|e|ez) (.+?)(?:\s|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_system_command(self, text: str) -> Optional[str]:
        """Extraire le type de commande système"""
        if any(word in text for word in ["éteins", "arrête", "shutdown"]):
            return "shutdown"
        elif any(word in text for word in ["redémarre", "restart"]):
            return "restart"  
        elif any(word in text for word in ["verrouille", "lock"]):
            return "lock"
        elif any(word in text for word in ["veille", "sleep"]):
            return "sleep"
        
        return None
    
    def extract_email_entities(self, text: str) -> Dict[str, str]:
        """Extraire les entités d'email"""
        entities = {}
        
        # Adresse email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        if email_match:
            entities["recipient"] = email_match.group(0)
        
        # Nom de destinataire
        recipient_patterns = [
            r"(?:à|pour) ([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",
            r"envoi(?:e|er) (?:un )?(?:e-?mail|message) à (.+?)(?:\s|$)",
        ]
        
        for pattern in recipient_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and "recipient" not in entities:
                entities["recipient"] = match.group(1).strip()
                break
        
        # Sujet (si "sujet" est mentionné)
        subject_match = re.search(r"sujet[:\s]+(.+)", text, re.IGNORECASE)
        if subject_match:
            entities["subject"] = subject_match.group(1).strip()
        
        return entities
    
    def extract_event_entities(self, text: str) -> Dict[str, str]:
        """Extraire les entités d'événement"""
        entities = {}
        
        # Titre de l'événement
        title_patterns = [
            r"programme (?:un )?(?:rendez-vous|rdv|événement|meeting) (.+?)(?:\s(?:le|à|pour|demain|aujourd'hui)|$)",
            r"ajoute (.+?) à (?:mon )?calendrier",
            r"planifie (.+?)(?:\s(?:le|à|pour|demain|aujourd'hui)|$)",
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities["title"] = match.group(1).strip()
                break
        
        # Date et heure
        time_entities = self.extract_time_entities(text)
        entities.update(time_entities)
        
        return entities
    
    def extract_social_entities(self, text: str) -> Dict[str, str]:
        """Extraire les entités de réseaux sociaux"""
        entities = {}
        
        # Platform
        for platform in self.entity_extractors["social_platforms"]:
            if platform.lower() in text.lower():
                entities["platform"] = platform
                break
        
        # Contenu à publier
        content_patterns = [
            r"publie (.+?) sur",
            r"poste (.+?) sur", 
            r"partage (.+?) sur",
            r"tweete (.+)",
        ]
        
        for pattern in content_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities["content"] = match.group(1).strip()
                break
        
        return entities
    
    def extract_time_entities(self, text: str) -> Dict[str, str]:
        """Extraire les entités temporelles"""
        entities = {}
        
        # Heure
        time_match = re.search(r"(\d{1,2}h\d{2}|\d{1,2}:\d{2})", text)
        if time_match:
            entities["time"] = time_match.group(1)
        
        # Date
        if "aujourd'hui" in text:
            entities["date"] = "today"
        elif "demain" in text:
            entities["date"] = "tomorrow"
        elif "après-demain" in text:
            entities["date"] = "day_after_tomorrow"
        
        # Date numérique
        date_match = re.search(r"(\d{1,2})/(\d{1,2})", text)
        if date_match:
            entities["date"] = f"{date_match.group(1)}/{date_match.group(2)}"
        
        return entities
    
    def extract_generic_entities(self, text: str) -> Dict[str, Any]:
        """Extraire des entités génériques"""
        entities = {}
        
        # Nombres
        numbers = re.findall(r"\d+", text)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]
        
        # Urls
        urls = re.findall(r"https?://[\w\.-]+(?:/[\w\.-]*)*", text)
        if urls:
            entities["urls"] = urls
        
        # Noms propres (basique)
        names = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", text)
        if names:
            entities["names"] = names
        
        return entities
    
    def select_best_result(self, results: List[IntentResult]) -> Optional[IntentResult]:
        """Sélectionner le meilleur résultat parmi plusieurs"""
        if not results:
            return None
        
        # Trier par confiance
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        # Bonus pour les résultats avec contexte
        for result in results:
            if result.context_used:
                result.confidence += 0.1
        
        # Re-trier
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results[0]
    
    def add_to_cache(self, text: str, result: IntentResult):
        """Ajouter au cache des résultats"""
        self.recent_intents[text] = {
            "result": result,
            "timestamp": datetime.now()
        }
        
        # Nettoyer le cache (garder seulement les 100 derniers)
        if len(self.recent_intents) > 100:
            oldest_key = min(self.recent_intents.keys(), 
                           key=lambda k: self.recent_intents[k]["timestamp"])
            del self.recent_intents[oldest_key]
    
    def update_context(self, text: str, result: IntentResult, context: Dict[str, Any] = None):
        """Mettre à jour le contexte conversationnel"""
        self.context_memory.append({
            "text": text,
            "intent": result.intent,
            "entities": result.entities,
            "timestamp": datetime.now()
        })
        
        # Garder seulement les 50 derniers éléments
        if len(self.context_memory) > 50:
            self.context_memory = self.context_memory[-50:]
    
    def get_suggestions(self, partial_text: str) -> List[str]:
        """Obtenir des suggestions pour un texte partial"""
        suggestions = []
        
        # Suggestions basées sur les intentions fréquentes
        common_commands = [
            "ouvre chrome",
            "vérifie mes emails", 
            "quelle est la météo",
            "programme un rendez-vous",
            "arrête d'écouter",
            "aide-moi"
        ]
        
        for command in common_commands:
            if partial_text.lower() in command:
                suggestions.append(command)
        
        return suggestions[:5]  # Max 5 suggestions
