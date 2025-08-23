"""
🎤 Moteur de Reconnaissance et Synthèse Vocale
============================================

Système avancé pour :
- Reconnaissance vocale en français (multi-moteurs)
- Synthèse vocale naturelle
- Détection de mots-clés d'activation
- Filtrage du bruit et amélioration audio
"""

import asyncio
import speech_recognition as sr
import pyttsx3
import pyaudio
import wave
import json
import logging
import numpy as np
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading
import queue
import time

# Tentative d'import des moteurs avancés
try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

class SpeechEngine:
    """Moteur de reconnaissance et synthèse vocale"""
    
    def __init__(self, config):
        """Initialiser le moteur vocal"""
        self.config = config
        self.logger = logging.getLogger("ARIA.Speech")
        
        # Moteurs de reconnaissance
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Moteur de synthèse
        self.tts_engine = None
        
        # Modèles offline (Vosk)
        self.vosk_model = None
        self.vosk_recognizer = None
        
        # Paramètres audio
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio_queue = queue.Queue()
        
        # Mots-clés d'activation
        self.wake_words = [
            "aria", "arya", "area", "aria écoute", "ária",
            "hey aria", "ok aria", "salut aria"
        ]
        
        # État
        self.listening = False
        self.speaking = False
        self.wake_word_detected = False
        
        # Configuration du recognizer
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.operation_timeout = None
        
        self.logger.info("🎤 Moteur vocal initialisé")
    
    async def initialize(self):
        """Initialiser tous les composants vocaux"""
        self.logger.info("🚀 Initialisation du moteur vocal...")
        
        try:
            # Initialiser la synthèse vocale
            await self.init_tts()
            
            # Initialiser les moteurs de reconnaissance
            await self.init_recognition_engines()
            
            # Calibrer le microphone
            await self.calibrate_microphone()
            
            # Tester les composants
            await self.test_components()
            
            self.logger.info("✅ Moteur vocal initialisé avec succès")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation moteur vocal: {e}")
            raise
    
    async def init_tts(self):
        """Initialiser la synthèse vocale"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configuration de la voix
            voices = self.tts_engine.getProperty('voices')
            
            # Chercher une voix française
            french_voice = None
            for voice in voices:
                if 'french' in voice.name.lower() or 'fr' in voice.id.lower():
                    french_voice = voice
                    break
            
            if french_voice:
                self.tts_engine.setProperty('voice', french_voice.id)
                self.logger.info(f"🗣️ Voix française sélectionnée: {french_voice.name}")
            else:
                self.logger.warning("⚠️ Aucune voix française trouvée, utilisation de la voix par défaut")
            
            # Configuration des paramètres
            self.tts_engine.setProperty('rate', self.config.tts_rate)  # Vitesse
            self.tts_engine.setProperty('volume', self.config.tts_volume)  # Volume
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation TTS: {e}")
            raise
    
    async def init_recognition_engines(self):
        """Initialiser les moteurs de reconnaissance"""
        engines_loaded = []
        
        # 1. Moteur offline Vosk
        if VOSK_AVAILABLE and self.config.use_vosk:
            try:
                model_path = Path(self.config.vosk_model_path)
                if model_path.exists():
                    self.vosk_model = vosk.Model(str(model_path))
                    self.vosk_recognizer = vosk.KaldiRecognizer(
                        self.vosk_model, 
                        self.sample_rate
                    )
                    engines_loaded.append("Vosk (offline)")
                    self.logger.info("✅ Moteur Vosk chargé")
                else:
                    self.logger.warning(f"⚠️ Modèle Vosk non trouvé: {model_path}")
            except Exception as e:
                self.logger.error(f"❌ Erreur chargement Vosk: {e}")
        
        # 2. Google Speech Recognition
        if self.config.use_google_sr:
            engines_loaded.append("Google Speech Recognition")
            self.logger.info("✅ Google Speech Recognition activé")
        
        # 3. Azure Speech Services
        if AZURE_AVAILABLE and self.config.azure_speech_key:
            try:
                self.azure_speech_config = speechsdk.SpeechConfig(
                    subscription=self.config.azure_speech_key,
                    region=self.config.azure_speech_region
                )
                self.azure_speech_config.speech_recognition_language = "fr-FR"
                engines_loaded.append("Azure Speech Services")
                self.logger.info("✅ Azure Speech Services configuré")
            except Exception as e:
                self.logger.error(f"❌ Erreur Azure Speech: {e}")
        
        # 4. OpenAI Whisper
        if OPENAI_AVAILABLE and self.config.openai_api_key:
            engines_loaded.append("OpenAI Whisper")
            self.logger.info("✅ OpenAI Whisper activé")
        
        self.logger.info(f"🎤 Moteurs de reconnaissance chargés: {', '.join(engines_loaded)}")
    
    async def calibrate_microphone(self):
        """Calibrer le microphone pour le bruit ambiant"""
        try:
            self.logger.info("🎙️ Calibration du microphone...")
            
            with self.microphone as source:
                # Ajuster pour le bruit ambiant
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            
            self.logger.info(f"✅ Microphone calibré (seuil: {self.recognizer.energy_threshold})")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calibration microphone: {e}")
    
    async def test_components(self):
        """Tester les composants vocaux"""
        try:
            # Test synthèse vocale
            if self.config.test_on_startup:
                await self.speak("Test du système vocal ARIA.", wait=True)
            
            self.logger.info("✅ Composants vocaux testés")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur test composants: {e}")
    
    async def listen(self, timeout: float = None) -> Optional[sr.AudioData]:
        """Écouter et capturer l'audio"""
        try:
            with self.microphone as source:
                # Écouter l'audio
                audio_data = self.recognizer.listen(
                    source,
                    timeout=timeout or self.config.listen_timeout,
                    phrase_time_limit=self.config.phrase_time_limit
                )
                
                return audio_data
        
        except sr.WaitTimeoutError:
            # Timeout normal, pas d'erreur
            return None
        except Exception as e:
            self.logger.error(f"❌ Erreur capture audio: {e}")
            return None
    
    async def transcribe(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcrire l'audio en texte"""
        transcriptions = []
        
        # Essayer plusieurs moteurs pour plus de précision
        engines = []
        
        # 1. Vosk (offline, rapide)
        if self.vosk_recognizer:
            engines.append(("vosk", self.transcribe_vosk))
        
        # 2. Google (online, précis)
        if self.config.use_google_sr:
            engines.append(("google", self.transcribe_google))
        
        # 3. Azure (online, très précis)
        if hasattr(self, 'azure_speech_config'):
            engines.append(("azure", self.transcribe_azure))
        
        # 4. OpenAI Whisper (online, excellent)
        if OPENAI_AVAILABLE and self.config.openai_api_key:
            engines.append(("whisper", self.transcribe_whisper))
        
        # Transcrire avec chaque moteur
        for engine_name, transcribe_func in engines:
            try:
                text = await transcribe_func(audio_data)
                if text and len(text.strip()) > 0:
                    transcriptions.append({
                        "engine": engine_name,
                        "text": text.strip().lower(),
                        "confidence": self.estimate_confidence(text)
                    })
                    self.logger.debug(f"🎤 {engine_name}: '{text}'")
            except Exception as e:
                self.logger.error(f"❌ Erreur {engine_name}: {e}")
        
        # Sélectionner la meilleure transcription
        if transcriptions:
            # Trier par confiance
            transcriptions.sort(key=lambda x: x["confidence"], reverse=True)
            best = transcriptions[0]
            
            self.logger.info(f"🎯 Meilleure transcription ({best['engine']}): '{best['text']}'")
            return best["text"]
        
        return None
    
    async def transcribe_vosk(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcription avec Vosk (offline)"""
        try:
            # Convertir en format requis par Vosk
            audio_np = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
            
            if self.vosk_recognizer.AcceptWaveform(audio_np.tobytes()):
                result = json.loads(self.vosk_recognizer.Result())
                return result.get("text", "")
            else:
                result = json.loads(self.vosk_recognizer.PartialResult())
                return result.get("partial", "")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur Vosk: {e}")
            return None
    
    async def transcribe_google(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcription avec Google Speech Recognition"""
        try:
            text = self.recognizer.recognize_google(
                audio_data, 
                language="fr-FR",
                show_all=False
            )
            return text
        except sr.UnknownValueError:
            return None
        except Exception as e:
            self.logger.error(f"❌ Erreur Google SR: {e}")
            return None
    
    async def transcribe_azure(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcription avec Azure Speech Services"""
        try:
            # Convertir l'audio pour Azure
            audio_format = speechsdk.audio.AudioStreamFormat(
                samples_per_second=audio_data.sample_rate,
                bits_per_sample=audio_data.sample_width * 8,
                channels=1
            )
            
            audio_stream = speechsdk.audio.PushAudioInputStream(audio_format)
            audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
            
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.azure_speech_config,
                audio_config=audio_config
            )
            
            # Envoyer les données audio
            audio_stream.write(audio_data.get_raw_data())
            audio_stream.close()
            
            # Reconnaître
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erreur Azure Speech: {e}")
            return None
    
    async def transcribe_whisper(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcription avec OpenAI Whisper"""
        try:
            # Sauvegarder temporairement l'audio
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_data.get_wav_data())
                tmp_file_path = tmp_file.name
            
            try:
                # Utiliser l'API Whisper
                client = openai.OpenAI(api_key=self.config.openai_api_key)
                
                with open(tmp_file_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="fr"
                    )
                
                return transcript.text
                
            finally:
                # Nettoyer le fichier temporaire
                os.unlink(tmp_file_path)
                
        except Exception as e:
            self.logger.error(f"❌ Erreur Whisper: {e}")
            return None
    
    def estimate_confidence(self, text: str) -> float:
        """Estimer la confiance d'une transcription"""
        if not text or len(text.strip()) == 0:
            return 0.0
        
        confidence = 0.5  # Base
        
        # Bonus pour la longueur
        if len(text) > 10:
            confidence += 0.2
        
        # Bonus pour les mots français courants
        french_words = ["le", "la", "les", "de", "du", "des", "un", "une", 
                       "et", "ou", "que", "qui", "avec", "dans", "sur", "pour"]
        
        words = text.lower().split()
        french_count = sum(1 for word in words if word in french_words)
        
        if words:
            french_ratio = french_count / len(words)
            confidence += french_ratio * 0.3
        
        return min(confidence, 1.0)
    
    async def detect_wake_word(self, text: str) -> bool:
        """Détecter les mots-clés d'activation"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                self.logger.info(f"🔊 Mot-clé détecté: '{wake_word}' dans '{text}'")
                return True
        
        return False
    
    async def speak(self, text: str, wait: bool = False):
        """Synthèse vocale"""
        if self.speaking:
            return  # Éviter les conflits
        
        self.speaking = True
        
        try:
            self.logger.info(f"🗣️ Synthèse: '{text}'")
            
            if wait:
                # Synthèse synchrone
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                # Synthèse asynchrone
                def speak_async():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                
                thread = threading.Thread(target=speak_async)
                thread.daemon = True
                thread.start()
        
        except Exception as e:
            self.logger.error(f"❌ Erreur synthèse vocale: {e}")
        
        finally:
            self.speaking = False
    
    async def listen_for_wake_word(self) -> bool:
        """Écouter en permanence pour les mots-clés d'activation"""
        try:
            # Écoute courte pour wake word
            audio_data = await self.listen(timeout=2.0)
            
            if audio_data:
                # Transcription rapide (uniquement offline)
                if self.vosk_recognizer:
                    text = await self.transcribe_vosk(audio_data)
                    if text and await self.detect_wake_word(text):
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur détection wake word: {e}")
            return False
    
    async def listen_command(self) -> Optional[str]:
        """Écouter une commande complète après activation"""
        try:
            self.logger.info("🎤 Écoute d'une commande...")
            
            # Écoute plus longue pour la commande
            audio_data = await self.listen(timeout=10.0)
            
            if audio_data:
                # Transcription complète avec tous les moteurs
                text = await self.transcribe(audio_data)
                
                if text:
                    self.logger.info(f"🎯 Commande reçue: '{text}'")
                    return text
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Erreur écoute commande: {e}")
            return None
    
    def get_available_engines(self) -> List[str]:
        """Obtenir la liste des moteurs disponibles"""
        engines = []
        
        if VOSK_AVAILABLE and self.vosk_model:
            engines.append("Vosk (offline)")
        
        if self.config.use_google_sr:
            engines.append("Google Speech Recognition")
        
        if AZURE_AVAILABLE and self.config.azure_speech_key:
            engines.append("Azure Speech Services")
        
        if OPENAI_AVAILABLE and self.config.openai_api_key:
            engines.append("OpenAI Whisper")
        
        return engines
    
    async def set_voice_settings(self, rate: int = None, volume: float = None):
        """Modifier les paramètres de la voix"""
        try:
            if rate is not None:
                self.tts_engine.setProperty('rate', rate)
                self.config.tts_rate = rate
            
            if volume is not None:
                self.tts_engine.setProperty('volume', volume)
                self.config.tts_volume = volume
            
            self.logger.info(f"🔧 Paramètres vocaux mis à jour: rate={rate}, volume={volume}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur modification paramètres vocaux: {e}")
    
    async def cleanup(self):
        """Nettoyer les ressources"""
        try:
            if self.tts_engine:
                self.tts_engine.stop()
            
            self.logger.info("🧹 Ressources vocales nettoyées")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur nettoyage ressources: {e}")
