"""
Module de gestion Google Calendar pour ARIA
Gère la création, modification et consultation d'événements de calendrier
"""

import os
import pickle
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import pytz

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class CalendarEvent:
    """Informations sur un événement de calendrier"""
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str
    attendees: List[str]
    creator: str
    is_all_day: bool = False
    recurrence: List[str] = None
    reminders: Dict = None
    status: str = "confirmed"
    visibility: str = "default"

@dataclass
class CalendarInfo:
    """Informations sur un calendrier"""
    id: str
    name: str
    description: str
    timezone: str
    is_primary: bool = False
    access_role: str = "reader"
    color: str = ""

class CalendarManager:
    """Gestionnaire pour l'API Google Calendar"""
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        if not GOOGLE_APIS_AVAILABLE:
            logger.error("Les APIs Google ne sont pas disponibles. Installez google-api-python-client")
            raise ImportError("google-api-python-client requis")
        
        self.credentials_file = credentials_file or "credentials.json"
        self.token_file = token_file or "calendar_token.pickle"
        
        # Scopes nécessaires pour Calendar
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        
        self.service = None
        self.timezone = pytz.timezone('Europe/Paris')  # Timezone par défaut
        self._authenticate()
    
    def _authenticate(self):
        """Authentification avec Google Calendar API"""
        try:
            creds = None
            
            # Charge le token existant
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # Si pas de credentials valides, lance le flow d'authentification
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Fichier credentials manquant : {self.credentials_file}")
                        logger.info("Téléchargez credentials.json depuis Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                
                # Sauvegarde le token
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Crée le service Calendar
            self.service = build('calendar', 'v3', credentials=creds)
            
            logger.info("Authentifié avec Google Calendar")
            return True
            
        except Exception as e:
            logger.error(f"Erreur authentification Calendar : {e}")
            return False
    
    def get_calendars(self) -> List[CalendarInfo]:
        """Récupère la liste des calendriers"""
        try:
            if not self.service:
                logger.error("Service Calendar non disponible")
                return []
            
            calendar_list = self.service.calendarList().list().execute()
            calendars = []
            
            for calendar_item in calendar_list.get('items', []):
                calendar_info = CalendarInfo(
                    id=calendar_item['id'],
                    name=calendar_item['summary'],
                    description=calendar_item.get('description', ''),
                    timezone=calendar_item.get('timeZone', 'UTC'),
                    is_primary=calendar_item.get('primary', False),
                    access_role=calendar_item.get('accessRole', 'reader'),
                    color=calendar_item.get('colorId', '')
                )
                calendars.append(calendar_info)
            
            logger.info(f"{len(calendars)} calendriers récupérés")
            return calendars
            
        except Exception as e:
            logger.error(f"Erreur récupération calendriers : {e}")
            return []
    
    def get_primary_calendar_id(self) -> Optional[str]:
        """Récupère l'ID du calendrier principal"""
        try:
            calendars = self.get_calendars()
            for calendar in calendars:
                if calendar.is_primary:
                    return calendar.id
            return 'primary'  # Fallback
        except:
            return 'primary'
    
    def create_event(self,
                    title: str,
                    start_time: datetime,
                    end_time: datetime,
                    description: str = "",
                    location: str = "",
                    attendees: List[str] = None,
                    calendar_id: str = None,
                    is_all_day: bool = False,
                    reminders: List[int] = None) -> Optional[str]:
        """Crée un nouvel événement"""
        try:
            if not self.service:
                logger.error("Service Calendar non disponible")
                return None
            
            if calendar_id is None:
                calendar_id = self.get_primary_calendar_id()
            
            # Prépare les données de l'événement
            event_data = {
                'summary': title,
                'description': description,
                'location': location,
            }
            
            # Gère les dates/heures
            if is_all_day:
                event_data['start'] = {'date': start_time.strftime('%Y-%m-%d')}
                event_data['end'] = {'date': end_time.strftime('%Y-%m-%d')}
            else:
                # S'assure que les dates ont une timezone
                if start_time.tzinfo is None:
                    start_time = self.timezone.localize(start_time)
                if end_time.tzinfo is None:
                    end_time = self.timezone.localize(end_time)
                
                event_data['start'] = {'dateTime': start_time.isoformat()}
                event_data['end'] = {'dateTime': end_time.isoformat()}
            
            # Ajoute les invités
            if attendees:
                event_data['attendees'] = [{'email': email} for email in attendees]
            
            # Ajoute les rappels
            if reminders:
                reminder_list = []
                for minutes in reminders:
                    reminder_list.append({
                        'method': 'popup',
                        'minutes': minutes
                    })
                event_data['reminders'] = {
                    'useDefault': False,
                    'overrides': reminder_list
                }
            
            # Crée l'événement
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event_data
            ).execute()
            
            logger.info(f"Événement créé : {title} (ID: {event['id']})")
            return event['id']
            
        except Exception as e:
            logger.error(f"Erreur création événement : {e}")
            return None
    
    def get_events(self,
                   calendar_id: str = None,
                   time_min: datetime = None,
                   time_max: datetime = None,
                   max_results: int = 50) -> List[CalendarEvent]:
        """Récupère les événements d'un calendrier"""
        try:
            if not self.service:
                logger.error("Service Calendar non disponible")
                return []
            
            if calendar_id is None:
                calendar_id = self.get_primary_calendar_id()
            
            # Par défaut, récupère les événements des 30 prochains jours
            if time_min is None:
                time_min = datetime.now(self.timezone)
            if time_max is None:
                time_max = time_min + timedelta(days=30)
            
            # S'assure que les dates ont une timezone
            if time_min.tzinfo is None:
                time_min = self.timezone.localize(time_min)
            if time_max.tzinfo is None:
                time_max = self.timezone.localize(time_max)
            
            # Récupère les événements
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events_data = events_result.get('items', [])
            events = []
            
            for event_data in events_data:
                event = self._parse_event_data(event_data)
                if event:
                    events.append(event)
            
            logger.info(f"{len(events)} événements récupérés")
            return events
            
        except Exception as e:
            logger.error(f"Erreur récupération événements : {e}")
            return []
    
    def _parse_event_data(self, event_data: Dict) -> Optional[CalendarEvent]:
        """Parse les données d'un événement Google Calendar"""
        try:
            event_id = event_data['id']
            title = event_data.get('summary', 'Sans titre')
            description = event_data.get('description', '')
            location = event_data.get('location', '')
            creator = event_data.get('creator', {}).get('email', '')
            status = event_data.get('status', 'confirmed')
            
            # Parse les dates
            start_data = event_data.get('start', {})
            end_data = event_data.get('end', {})
            
            is_all_day = 'date' in start_data
            
            if is_all_day:
                start_time = datetime.strptime(start_data['date'], '%Y-%m-%d')
                end_time = datetime.strptime(end_data['date'], '%Y-%m-%d')
            else:
                start_time = datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
            
            # Parse les invités
            attendees = []
            for attendee in event_data.get('attendees', []):
                attendees.append(attendee.get('email', ''))
            
            # Parse les récurrences
            recurrence = event_data.get('recurrence', [])
            
            # Parse les rappels
            reminders = event_data.get('reminders', {})
            
            return CalendarEvent(
                id=event_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                location=location,
                attendees=attendees,
                creator=creator,
                is_all_day=is_all_day,
                recurrence=recurrence,
                reminders=reminders,
                status=status
            )
            
        except Exception as e:
            logger.error(f"Erreur parsing événement : {e}")
            return None
    
    def get_today_events(self, calendar_id: str = None) -> List[CalendarEvent]:
        """Récupère les événements d'aujourd'hui"""
        today = datetime.now(self.timezone).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        return self.get_events(
            calendar_id=calendar_id,
            time_min=today,
            time_max=tomorrow
        )
    
    def get_upcoming_events(self, calendar_id: str = None, days: int = 7) -> List[CalendarEvent]:
        """Récupère les événements à venir"""
        now = datetime.now(self.timezone)
        future = now + timedelta(days=days)
        
        return self.get_events(
            calendar_id=calendar_id,
            time_min=now,
            time_max=future
        )
    
    def get_event_by_id(self, event_id: str, calendar_id: str = None) -> Optional[CalendarEvent]:
        """Récupère un événement par son ID"""
        try:
            if not self.service:
                logger.error("Service Calendar non disponible")
                return None
            
            if calendar_id is None:
                calendar_id = self.get_primary_calendar_id()
            
            event_data = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            return self._parse_event_data(event_data)
            
        except Exception as e:
            logger.error(f"Erreur récupération événement {event_id} : {e}")
            return None
    
    def update_event(self,
                    event_id: str,
                    title: str = None,
                    start_time: datetime = None,
                    end_time: datetime = None,
                    description: str = None,
                    location: str = None,
                    calendar_id: str = None) -> bool:
        """Met à jour un événement existant"""
        try:
            if not self.service:
                logger.error("Service Calendar non disponible")
                return False
            
            if calendar_id is None:
                calendar_id = self.get_primary_calendar_id()
            
            # Récupère l'événement existant
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Met à jour les champs modifiés
            if title is not None:
                event['summary'] = title
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            
            if start_time is not None and end_time is not None:
                # S'assure que les dates ont une timezone
                if start_time.tzinfo is None:
                    start_time = self.timezone.localize(start_time)
                if end_time.tzinfo is None:
                    end_time = self.timezone.localize(end_time)
                
                event['start'] = {'dateTime': start_time.isoformat()}
                event['end'] = {'dateTime': end_time.isoformat()}
            
            # Sauvegarde les modifications
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Événement mis à jour : {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise à jour événement : {e}")
            return False
    
    def delete_event(self, event_id: str, calendar_id: str = None) -> bool:
        """Supprime un événement"""
        try:
            if not self.service:
                logger.error("Service Calendar non disponible")
                return False
            
            if calendar_id is None:
                calendar_id = self.get_primary_calendar_id()
            
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Événement supprimé : {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur suppression événement : {e}")
            return False
    
    def search_events(self, query: str, calendar_id: str = None, max_results: int = 20) -> List[CalendarEvent]:
        """Recherche des événements par mots-clés"""
        try:
            if not self.service:
                logger.error("Service Calendar non disponible")
                return []
            
            if calendar_id is None:
                calendar_id = self.get_primary_calendar_id()
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                q=query,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events_data = events_result.get('items', [])
            events = []
            
            for event_data in events_data:
                event = self._parse_event_data(event_data)
                if event:
                    events.append(event)
            
            logger.info(f"{len(events)} événements trouvés pour '{query}'")
            return events
            
        except Exception as e:
            logger.error(f"Erreur recherche événements : {e}")
            return []
    
    def create_quick_event(self, text: str, calendar_id: str = None) -> Optional[str]:
        """Crée un événement rapidement à partir de texte naturel"""
        try:
            if not self.service:
                logger.error("Service Calendar non disponible")
                return None
            
            if calendar_id is None:
                calendar_id = self.get_primary_calendar_id()
            
            event = self.service.events().quickAdd(
                calendarId=calendar_id,
                text=text
            ).execute()
            
            logger.info(f"Événement rapide créé : {text} (ID: {event['id']})")
            return event['id']
            
        except Exception as e:
            logger.error(f"Erreur création événement rapide : {e}")
            return None
    
    def get_free_busy_info(self,
                          time_min: datetime,
                          time_max: datetime,
                          calendar_ids: List[str] = None) -> Dict:
        """Récupère les informations de disponibilité"""
        try:
            if not self.service:
                logger.error("Service Calendar non disponible")
                return {}
            
            if calendar_ids is None:
                calendar_ids = [self.get_primary_calendar_id()]
            
            # S'assure que les dates ont une timezone
            if time_min.tzinfo is None:
                time_min = self.timezone.localize(time_min)
            if time_max.tzinfo is None:
                time_max = self.timezone.localize(time_max)
            
            body = {
                'timeMin': time_min.isoformat(),
                'timeMax': time_max.isoformat(),
                'items': [{'id': cal_id} for cal_id in calendar_ids]
            }
            
            freebusy = self.service.freebusy().query(body=body).execute()
            
            logger.info("Informations de disponibilité récupérées")
            return freebusy
            
        except Exception as e:
            logger.error(f"Erreur récupération disponibilité : {e}")
            return {}
    
    def is_time_free(self,
                    start_time: datetime,
                    end_time: datetime,
                    calendar_id: str = None) -> bool:
        """Vérifie si une période est libre"""
        try:
            if calendar_id is None:
                calendar_id = self.get_primary_calendar_id()
            
            freebusy_info = self.get_free_busy_info(
                time_min=start_time,
                time_max=end_time,
                calendar_ids=[calendar_id]
            )
            
            busy_periods = freebusy_info.get('calendars', {}).get(calendar_id, {}).get('busy', [])
            
            return len(busy_periods) == 0
            
        except Exception as e:
            logger.error(f"Erreur vérification disponibilité : {e}")
            return False
    
    def get_next_free_slot(self,
                          duration_minutes: int,
                          start_search_time: datetime = None,
                          calendar_id: str = None) -> Optional[Tuple[datetime, datetime]]:
        """Trouve le prochain créneau libre d'une durée donnée"""
        try:
            if start_search_time is None:
                start_search_time = datetime.now(self.timezone)
            
            if calendar_id is None:
                calendar_id = self.get_primary_calendar_id()
            
            # Recherche sur les 7 prochains jours
            end_search_time = start_search_time + timedelta(days=7)
            
            # Récupère les événements existants
            events = self.get_events(
                calendar_id=calendar_id,
                time_min=start_search_time,
                time_max=end_search_time
            )
            
            # Trie les événements par heure de début
            events.sort(key=lambda x: x.start_time)
            
            # Trouve le premier créneau libre
            current_time = start_search_time
            duration = timedelta(minutes=duration_minutes)
            
            for event in events:
                if event.is_all_day:
                    continue
                
                # Vérifie si le créneau avant cet événement est libre
                if current_time + duration <= event.start_time:
                    return (current_time, current_time + duration)
                
                # Passe à la fin de cet événement
                if event.end_time > current_time:
                    current_time = event.end_time
            
            # Si aucun événement ne bloque, retourne le créneau actuel
            return (current_time, current_time + duration)
            
        except Exception as e:
            logger.error(f"Erreur recherche créneau libre : {e}")
            return None
    
    def get_calendar_stats(self) -> Dict:
        """Récupère des statistiques sur les calendriers"""
        try:
            calendars = self.get_calendars()
            today_events = self.get_today_events()
            upcoming_events = self.get_upcoming_events(days=7)
            
            return {
                'total_calendars': len(calendars),
                'today_events_count': len(today_events),
                'upcoming_events_count': len(upcoming_events),
                'calendars': [{'name': cal.name, 'id': cal.id} for cal in calendars]
            }
            
        except Exception as e:
            logger.error(f"Erreur statistiques calendrier : {e}")
            return {}

# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration de logging pour test
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Crée le gestionnaire Calendar
        calendar_mgr = CalendarManager()
        
        # Affiche les statistiques
        stats = calendar_mgr.get_calendar_stats()
        print(f"Statistiques Calendar : {stats}")
        
        # Récupère les événements d'aujourd'hui
        today_events = calendar_mgr.get_today_events()
        print(f"Événements d'aujourd'hui : {len(today_events)}")
        
        for event in today_events:
            print(f"- {event.title}")
            print(f"  Heure: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}")
            if event.location:
                print(f"  Lieu: {event.location}")
            print()
            
    except ImportError:
        print("Google APIs non installées")
    except Exception as e:
        print(f"Erreur : {e}")
