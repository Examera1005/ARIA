"""
Module de réponse vocale pour ARIA
Synthèse vocale avancée et gestion des voix pour les réponses de l'assistant
"""

import logging
import threading
import time
import queue
import os
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
import json

# Text-to-Speech engines
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_TTS_AVAILABLE = True
except ImportError:
    AZURE_TTS_AVAILABLE = False

try:
    import gtts
    from io import BytesIO
    import pygame
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class VoiceSettings:
    """Paramètres de la voix"""
    engine: str = "pyttsx3"  # pyttsx3, azure, gtts
    voice_id: str = ""
    rate: int = 200  # Vitesse de parole
    volume: float = 0.8  # Volume (0.0 à 1.0)
    pitch: int = 0  # Hauteur de voix
    language: str = "fr-FR"
    gender: str = "female"  # male, female, neutral

class ResponseEngine:
    """Moteur de réponse vocale d'ARIA"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.voice_settings = VoiceSettings()
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.stop_current_speech = False
        
        # Moteurs TTS
        self.engines = {
            'pyttsx3': None,
            'azure': None,
            'gtts': None
        }
        
        # Callbacks
        self.callbacks = {
            'on_speech_start': None,
            'on_speech_end': None,
            'on_speech_error': None
        }
        
        # Thread de synthèse vocale
        self.tts_thread = None
        self.is_running = False
        
        self._initialize_engines()
        self._start_speech_thread()
    
    def _initialize_engines(self):
        """Initialise les moteurs de synthèse vocale disponibles"""
        try:
            # Pyttsx3 (local)
            if PYTTSX3_AVAILABLE:
                self.engines['pyttsx3'] = pyttsx3.init()
                self._configure_pyttsx3()
                logger.info("Moteur pyttsx3 initialisé")
            
            # Azure Cognitive Services
            if AZURE_TTS_AVAILABLE and self.config.get('azure_speech_key'):
                speech_key = self.config['azure_speech_key']
                speech_region = self.config.get('azure_speech_region', 'westeurope')
                
                speech_config = speechsdk.SpeechConfig(
                    subscription=speech_key, 
                    region=speech_region
                )
                speech_config.speech_synthesis_language = self.voice_settings.language
                self.engines['azure'] = speech_config
                logger.info("Moteur Azure Speech initialisé")
            
            # Google Text-to-Speech
            if GTTS_AVAILABLE:
                try:
                    pygame.mixer.init()
                    self.engines['gtts'] = True
                    logger.info("Moteur gTTS initialisé")
                except:
                    logger.warning("Impossible d'initialiser pygame pour gTTS")
            
            # Sélection du moteur par défaut
            if self.engines['pyttsx3']:
                self.voice_settings.engine = 'pyttsx3'
            elif self.engines['azure']:
                self.voice_settings.engine = 'azure'
            elif self.engines['gtts']:
                self.voice_settings.engine = 'gtts'
            else:
                logger.warning("Aucun moteur TTS disponible")
                
        except Exception as e:
            logger.error(f"Erreur initialisation moteurs TTS : {e}")
    
    def _configure_pyttsx3(self):
        """Configure le moteur pyttsx3"""
        try:
            if not self.engines['pyttsx3']:
                return
            
            engine = self.engines['pyttsx3']
            
            # Définit la vitesse
            engine.setProperty('rate', self.voice_settings.rate)
            
            # Définit le volume
            engine.setProperty('volume', self.voice_settings.volume)
            
            # Sélectionne la voix
            voices = engine.getProperty('voices')
            if voices:
                # Recherche une voix française
                french_voice = None
                female_voice = None
                
                for voice in voices:
                    voice_name = voice.name.lower()
                    voice_id = voice.id.lower()
                    
                    # Priorité aux voix françaises
                    if 'fr' in voice_id or 'french' in voice_name:
                        if not french_voice:
                            french_voice = voice.id
                        # Priorité aux voix féminines
                        if ('female' in voice_name or 'femme' in voice_name or 
                            'julie' in voice_name or 'marie' in voice_name):
                            french_voice = voice.id
                            break
                    
                    # Recherche voix féminine générale
                    if 'female' in voice_name and not female_voice:
                        female_voice = voice.id
                
                # Sélectionne la meilleure voix
                selected_voice = french_voice or female_voice or voices[0].id
                engine.setProperty('voice', selected_voice)
                self.voice_settings.voice_id = selected_voice
                
                logger.info(f"Voix sélectionnée : {selected_voice}")
            
        except Exception as e:
            logger.error(f"Erreur configuration pyttsx3 : {e}")
    
    def _start_speech_thread(self):
        """Démarre le thread de synthèse vocale"""
        self.is_running = True
        self.tts_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.tts_thread.start()
        logger.info("Thread de synthèse vocale démarré")
    
    def _speech_worker(self):
        """Worker thread pour la synthèse vocale"""
        while self.is_running:
            try:
                # Attend un texte à synthétiser
                try:
                    speech_request = self.speech_queue.get(timeout=0.5)
                    
                    if speech_request is None:  # Signal d'arrêt
                        break
                    
                    text = speech_request.get('text', '')
                    priority = speech_request.get('priority', 'normal')
                    interrupt = speech_request.get('interrupt', False)
                    
                    if interrupt:
                        self._stop_current_speech()
                    
                    # Synthétise le texte
                    self._synthesize_text(text)
                    
                    self.speech_queue.task_done()
                    
                except queue.Empty:
                    continue
                    
            except Exception as e:
                logger.error(f"Erreur dans le worker TTS : {e}")
                
            time.sleep(0.1)
    
    def _synthesize_text(self, text: str) -> bool:
        """Synthétise un texte selon le moteur configuré"""
        if not text.strip():
            return False
        
        self.is_speaking = True
        self.stop_current_speech = False
        
        # Callback début de parole
        if self.callbacks['on_speech_start']:
            try:
                self.callbacks['on_speech_start'](text)
            except Exception as e:
                logger.error(f"Erreur callback speech_start : {e}")
        
        try:
            success = False
            
            if self.voice_settings.engine == 'pyttsx3':
                success = self._synthesize_pyttsx3(text)
            elif self.voice_settings.engine == 'azure':
                success = self._synthesize_azure(text)
            elif self.voice_settings.engine == 'gtts':
                success = self._synthesize_gtts(text)
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur synthèse vocale : {e}")
            if self.callbacks['on_speech_error']:
                try:
                    self.callbacks['on_speech_error'](str(e))
                except:
                    pass
            return False
            
        finally:
            self.is_speaking = False
            # Callback fin de parole
            if self.callbacks['on_speech_end']:
                try:
                    self.callbacks['on_speech_end'](text)
                except Exception as e:
                    logger.error(f"Erreur callback speech_end : {e}")
    
    def _synthesize_pyttsx3(self, text: str) -> bool:
        """Synthèse avec pyttsx3"""
        try:
            if not self.engines['pyttsx3']:
                return False
            
            engine = self.engines['pyttsx3']
            
            # Nettoie le texte
            clean_text = self._clean_text_for_speech(text)
            
            # Synthétise
            engine.say(clean_text)
            engine.runAndWait()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur pyttsx3 : {e}")
            return False
    
    def _synthesize_azure(self, text: str) -> bool:
        """Synthèse avec Azure Cognitive Services"""
        try:
            if not self.engines['azure']:
                return False
            
            speech_config = self.engines['azure']
            
            # Configure la voix
            if self.voice_settings.voice_id:
                speech_config.speech_synthesis_voice_name = self.voice_settings.voice_id
            else:
                # Voix par défaut française
                speech_config.speech_synthesis_voice_name = "fr-FR-DeniseNeural"
            
            # Crée le synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
            
            # Nettoie le texte
            clean_text = self._clean_text_for_speech(text)
            
            # Synthétise
            result = synthesizer.speak_text_async(clean_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return True
            else:
                logger.error(f"Erreur Azure TTS : {result.reason}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur Azure TTS : {e}")
            return False
    
    def _synthesize_gtts(self, text: str) -> bool:
        """Synthèse avec Google Text-to-Speech"""
        try:
            if not self.engines['gtts']:
                return False
            
            # Nettoie le texte
            clean_text = self._clean_text_for_speech(text)
            
            # Crée l'objet gTTS
            tts = gtts.gTTS(
                text=clean_text,
                lang=self.voice_settings.language.split('-')[0],  # 'fr' de 'fr-FR'
                slow=False
            )
            
            # Sauvegarde temporairement
            temp_file = BytesIO()
            tts.write_to_fp(temp_file)
            temp_file.seek(0)
            
            # Joue avec pygame
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Attend la fin de la lecture
            while pygame.mixer.music.get_busy():
                if self.stop_current_speech:
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur gTTS : {e}")
            return False
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Nettoie le texte pour la synthèse vocale"""
        # Supprime les caractères indésirables
        clean_text = text.replace('\n', ' ').replace('\r', ' ')
        clean_text = clean_text.replace('\t', ' ')
        
        # Normalise les espaces multiples
        import re
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Supprime les caractères de formatage markdown
        clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)  # **gras**
        clean_text = re.sub(r'\*(.*?)\*', r'\1', clean_text)      # *italique*
        clean_text = re.sub(r'`(.*?)`', r'\1', clean_text)        # `code`
        
        # Remplace certaines abréviations
        replacements = {
            'URL': 'U R L',
            'API': 'A P I',
            'IA': 'I A',
            'AI': 'A I',
            'HTTP': 'H T T P',
            'JSON': 'J S O N',
            'XML': 'X M L',
            'PDF': 'P D F'
        }
        
        for abbrev, pronunciation in replacements.items():
            clean_text = clean_text.replace(abbrev, pronunciation)
        
        return clean_text.strip()
    
    def speak(self, text: str, priority: str = 'normal', interrupt: bool = False) -> bool:
        """Ajoute un texte à la queue de synthèse vocale"""
        if not text.strip():
            return False
        
        try:
            speech_request = {
                'text': text,
                'priority': priority,
                'interrupt': interrupt
            }
            
            if interrupt:
                # Vide la queue et ajoute en priorité
                self._clear_speech_queue()
            
            self.speech_queue.put(speech_request)
            return True
            
        except Exception as e:
            logger.error(f"Erreur ajout synthèse vocale : {e}")
            return False
    
    def speak_immediately(self, text: str) -> bool:
        """Synthétise immédiatement un texte (bloquant)"""
        if not text.strip():
            return False
        
        self._stop_current_speech()
        return self._synthesize_text(text)
    
    def stop_speaking(self) -> bool:
        """Arrête la synthèse vocale en cours"""
        try:
            self._stop_current_speech()
            self._clear_speech_queue()
            return True
        except Exception as e:
            logger.error(f"Erreur arrêt synthèse vocale : {e}")
            return False
    
    def _stop_current_speech(self):
        """Arrête la synthèse vocale en cours"""
        self.stop_current_speech = True
        
        try:
            # Arrêt pyttsx3
            if self.engines['pyttsx3'] and self.is_speaking:
                self.engines['pyttsx3'].stop()
            
            # Arrêt pygame (gTTS)
            if self.engines['gtts']:
                pygame.mixer.music.stop()
                
        except Exception as e:
            logger.debug(f"Erreur arrêt synthèse : {e}")
    
    def _clear_speech_queue(self):
        """Vide la queue de synthèse vocale"""
        try:
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except queue.Empty:
                    break
        except Exception as e:
            logger.error(f"Erreur vidage queue : {e}")
    
    def set_voice_settings(self, **settings):
        """Met à jour les paramètres de la voix"""
        for key, value in settings.items():
            if hasattr(self.voice_settings, key):
                setattr(self.voice_settings, key, value)
        
        # Reconfigure le moteur si nécessaire
        if self.voice_settings.engine == 'pyttsx3':
            self._configure_pyttsx3()
    
    def get_available_voices(self) -> List[Dict]:
        """Retourne la liste des voix disponibles"""
        voices = []
        
        try:
            if self.engines['pyttsx3']:
                engine = self.engines['pyttsx3']
                pyttsx3_voices = engine.getProperty('voices')
                
                for voice in pyttsx3_voices:
                    voices.append({
                        'engine': 'pyttsx3',
                        'id': voice.id,
                        'name': voice.name,
                        'language': getattr(voice, 'languages', ['unknown']),
                        'gender': 'unknown'
                    })
            
            # Pour Azure, liste prédéfinie des voix françaises populaires
            if self.engines['azure']:
                azure_voices = [
                    {'id': 'fr-FR-DeniseNeural', 'name': 'Denise (Femme)', 'gender': 'female'},
                    {'id': 'fr-FR-HenriNeural', 'name': 'Henri (Homme)', 'gender': 'male'},
                    {'id': 'fr-FR-AlainNeural', 'name': 'Alain (Homme)', 'gender': 'male'},
                    {'id': 'fr-FR-BrigitteNeural', 'name': 'Brigitte (Femme)', 'gender': 'female'},
                    {'id': 'fr-FR-CelesteNeural', 'name': 'Celeste (Femme)', 'gender': 'female'},
                    {'id': 'fr-FR-ClaudeNeural', 'name': 'Claude (Homme)', 'gender': 'male'},
                ]
                
                for voice in azure_voices:
                    voices.append({
                        'engine': 'azure',
                        'id': voice['id'],
                        'name': voice['name'],
                        'language': ['fr-FR'],
                        'gender': voice['gender']
                    })
            
            # gTTS - une seule "voix" par langue
            if self.engines['gtts']:
                voices.append({
                    'engine': 'gtts',
                    'id': 'gtts-fr',
                    'name': 'Google TTS Français',
                    'language': ['fr'],
                    'gender': 'neutral'
                })
                
        except Exception as e:
            logger.error(f"Erreur récupération voix : {e}")
        
        return voices
    
    def set_callback(self, event: str, callback: Callable):
        """Définit un callback pour les événements de synthèse vocale"""
        if event in self.callbacks:
            self.callbacks[event] = callback
    
    def is_speaking_now(self) -> bool:
        """Retourne True si la synthèse vocale est en cours"""
        return self.is_speaking
    
    def get_queue_size(self) -> int:
        """Retourne la taille de la queue de synthèse vocale"""
        return self.speech_queue.qsize()
    
    def save_voice_settings(self, filepath: str = None):
        """Sauvegarde les paramètres de voix"""
        try:
            if filepath is None:
                filepath = os.path.join(
                    os.path.dirname(__file__), "..", "config", "voice_settings.json"
                )
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            settings_dict = {
                'engine': self.voice_settings.engine,
                'voice_id': self.voice_settings.voice_id,
                'rate': self.voice_settings.rate,
                'volume': self.voice_settings.volume,
                'pitch': self.voice_settings.pitch,
                'language': self.voice_settings.language,
                'gender': self.voice_settings.gender
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2)
                
            logger.info(f"Paramètres vocaux sauvegardés : {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde paramètres vocaux : {e}")
            return False
    
    def load_voice_settings(self, filepath: str = None):
        """Charge les paramètres de voix sauvegardés"""
        try:
            if filepath is None:
                filepath = os.path.join(
                    os.path.dirname(__file__), "..", "config", "voice_settings.json"
                )
            
            if not os.path.exists(filepath):
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
            
            # Met à jour les paramètres
            for key, value in settings_dict.items():
                if hasattr(self.voice_settings, key):
                    setattr(self.voice_settings, key, value)
            
            # Reconfigure le moteur
            if self.voice_settings.engine == 'pyttsx3':
                self._configure_pyttsx3()
            
            logger.info(f"Paramètres vocaux chargés : {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur chargement paramètres vocaux : {e}")
            return False
    
    def shutdown(self):
        """Arrête le moteur de réponse vocale"""
        try:
            logger.info("Arrêt du moteur de réponse vocale")
            
            # Arrête la synthèse en cours
            self._stop_current_speech()
            
            # Arrête le thread worker
            self.is_running = False
            self.speech_queue.put(None)  # Signal d'arrêt
            
            if self.tts_thread and self.tts_thread.is_alive():
                self.tts_thread.join(timeout=2)
            
            # Ferme les moteurs
            if self.engines['pyttsx3']:
                try:
                    self.engines['pyttsx3'].stop()
                except:
                    pass
            
            if self.engines['gtts']:
                try:
                    pygame.mixer.quit()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Erreur arrêt moteur vocal : {e}")

# Exemple d'utilisation et test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    def on_speech_start(text):
        print(f"🎤 Début synthèse : {text[:50]}...")
    
    def on_speech_end(text):
        print(f"✓ Fin synthèse")
    
    def on_speech_error(error):
        print(f"❌ Erreur : {error}")
    
    # Test du moteur
    config = {
        # 'azure_speech_key': 'votre_clé_azure',
        # 'azure_speech_region': 'westeurope'
    }
    
    engine = ResponseEngine(config)
    
    # Configure les callbacks
    engine.set_callback('on_speech_start', on_speech_start)
    engine.set_callback('on_speech_end', on_speech_end)
    engine.set_callback('on_speech_error', on_speech_error)
    
    # Affiche les voix disponibles
    voices = engine.get_available_voices()
    print(f"Voix disponibles ({len(voices)}) :")
    for voice in voices:
        print(f"  - {voice['engine']}: {voice['name']} ({voice['id']})")
    
    # Test de synthèse
    print("\nTest de synthèse vocale...")
    engine.speak("Bonjour ! Je suis ARIA, votre assistant intelligent. Comment allez-vous ?")
    
    # Attendre un peu pour le test
    time.sleep(3)
    
    # Test avec priorité
    engine.speak("Ceci est un message prioritaire !", priority='high', interrupt=True)
    
    # Attendre avant la fermeture
    time.sleep(5)
    
    print("Fermeture du moteur...")
    engine.shutdown()
