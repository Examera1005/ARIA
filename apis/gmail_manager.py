"""
Module de gestion Gmail pour ARIA
Gère l'envoi, la réception et la gestion des emails via l'API Gmail
"""

import os
import pickle
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import re

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
class EmailInfo:
    """Informations sur un email"""
    id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    snippet: str
    body: str
    date: datetime
    is_unread: bool
    labels: List[str]
    attachments: List[Dict]
    importance: str = "normal"

@dataclass
class EmailAttachment:
    """Informations sur une pièce jointe"""
    filename: str
    mimetype: str
    size: int
    attachment_id: str

class GmailManager:
    """Gestionnaire pour l'API Gmail"""
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        if not GOOGLE_APIS_AVAILABLE:
            logger.error("Les APIs Google ne sont pas disponibles. Installez google-api-python-client")
            raise ImportError("google-api-python-client requis")
        
        self.credentials_file = credentials_file or "credentials.json"
        self.token_file = token_file or "gmail_token.pickle"
        
        # Scopes nécessaires pour Gmail
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.labels'
        ]
        
        self.service = None
        self.user_email = None
        self._authenticate()
    
    def _authenticate(self):
        """Authentification avec Google Gmail API"""
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
            
            # Crée le service Gmail
            self.service = build('gmail', 'v1', credentials=creds)
            
            # Récupère l'email de l'utilisateur
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile.get('emailAddress')
            
            logger.info(f"Authentifié avec Gmail : {self.user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur authentification Gmail : {e}")
            return False
    
    def send_email(self, 
                   to: str, 
                   subject: str, 
                   body: str, 
                   cc: List[str] = None,
                   bcc: List[str] = None,
                   attachments: List[str] = None,
                   is_html: bool = False) -> bool:
        """Envoie un email"""
        try:
            if not self.service:
                logger.error("Service Gmail non disponible")
                return False
            
            # Crée le message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            # Corps du message
            if is_html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Ajoute les pièces jointes
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(message, file_path)
                    else:
                        logger.warning(f"Fichier introuvable : {file_path}")
            
            # Encode le message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Envoie le message
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email envoyé avec succès : {send_message['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email : {e}")
            return False
    
    def _add_attachment(self, message: MIMEMultipart, file_path: str):
        """Ajoute une pièce jointe au message"""
        try:
            # Détecte le type MIME
            content_type, encoding = mimetypes.guess_type(file_path)
            
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            
            main_type, sub_type = content_type.split('/', 1)
            
            with open(file_path, 'rb') as fp:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(fp.read())
            
            encoders.encode_base64(attachment)
            
            filename = os.path.basename(file_path)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            
            message.attach(attachment)
            logger.debug(f"Pièce jointe ajoutée : {filename}")
            
        except Exception as e:
            logger.error(f"Erreur ajout pièce jointe {file_path} : {e}")
    
    def get_messages(self, 
                     query: str = None,
                     max_results: int = 10,
                     include_spam_trash: bool = False) -> List[EmailInfo]:
        """Récupère les messages selon les critères"""
        try:
            if not self.service:
                logger.error("Service Gmail non disponible")
                return []
            
            # Récupère la liste des messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                includeSpamTrash=include_spam_trash
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info("Aucun message trouvé")
                return []
            
            # Récupère les détails de chaque message
            email_list = []
            for message in messages:
                email_info = self._get_message_details(message['id'])
                if email_info:
                    email_list.append(email_info)
            
            logger.info(f"{len(email_list)} messages récupérés")
            return email_list
            
        except Exception as e:
            logger.error(f"Erreur récupération messages : {e}")
            return []
    
    def _get_message_details(self, message_id: str) -> Optional[EmailInfo]:
        """Récupère les détails d'un message spécifique"""
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            payload = message['payload']
            headers = payload.get('headers', [])
            
            # Extrait les headers importants
            sender = ""
            recipient = ""
            subject = ""
            date_str = ""
            
            for header in headers:
                name = header['name'].lower()
                if name == 'from':
                    sender = header['value']
                elif name == 'to':
                    recipient = header['value']
                elif name == 'subject':
                    subject = header['value']
                elif name == 'date':
                    date_str = header['value']
            
            # Parse la date
            try:
                from email.utils import parsedate_to_datetime
                date = parsedate_to_datetime(date_str)
            except:
                date = datetime.now()
            
            # Extrait le corps du message
            body = self._extract_body(payload)
            
            # Vérifie si non lu
            is_unread = 'UNREAD' in message.get('labelIds', [])
            
            # Extrait les pièces jointes
            attachments = self._extract_attachments(payload)
            
            return EmailInfo(
                id=message_id,
                thread_id=message['threadId'],
                sender=sender,
                recipient=recipient,
                subject=subject,
                snippet=message.get('snippet', ''),
                body=body,
                date=date,
                is_unread=is_unread,
                labels=message.get('labelIds', []),
                attachments=attachments
            )
            
        except Exception as e:
            logger.error(f"Erreur détails message {message_id} : {e}")
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extrait le corps du message"""
        body = ""
        
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            body_data = part['body']['data']
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            break
            elif payload['mimeType'] == 'text/plain':
                if 'data' in payload['body']:
                    body_data = payload['body']['data']
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Erreur extraction corps : {e}")
            body = "Erreur lecture du message"
        
        return body
    
    def _extract_attachments(self, payload: Dict) -> List[Dict]:
        """Extrait les informations des pièces jointes"""
        attachments = []
        
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('filename'):
                        attachment = {
                            'filename': part['filename'],
                            'mimetype': part['mimeType'],
                            'size': part['body'].get('size', 0),
                            'attachment_id': part['body'].get('attachmentId')
                        }
                        attachments.append(attachment)
        except Exception as e:
            logger.error(f"Erreur extraction pièces jointes : {e}")
        
        return attachments
    
    def download_attachment(self, message_id: str, attachment_id: str, save_path: str) -> bool:
        """Télécharge une pièce jointe"""
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me', messageId=message_id, id=attachment_id
            ).execute()
            
            data = attachment['data']
            file_data = base64.urlsafe_b64decode(data)
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Pièce jointe téléchargée : {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur téléchargement pièce jointe : {e}")
            return False
    
    def mark_as_read(self, message_id: str) -> bool:
        """Marque un message comme lu"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"Message marqué comme lu : {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur marquage lu : {e}")
            return False
    
    def mark_as_unread(self, message_id: str) -> bool:
        """Marque un message comme non lu"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"Message marqué comme non lu : {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur marquage non lu : {e}")
            return False
    
    def delete_message(self, message_id: str) -> bool:
        """Supprime un message"""
        try:
            self.service.users().messages().delete(
                userId='me', id=message_id
            ).execute()
            
            logger.info(f"Message supprimé : {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur suppression message : {e}")
            return False
    
    def archive_message(self, message_id: str) -> bool:
        """Archive un message"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            
            logger.info(f"Message archivé : {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur archivage message : {e}")
            return False
    
    def search_emails(self, query: str, max_results: int = 50) -> List[EmailInfo]:
        """Recherche des emails avec une query spécifique"""
        return self.get_messages(query=query, max_results=max_results)
    
    def get_unread_emails(self, max_results: int = 20) -> List[EmailInfo]:
        """Récupère les emails non lus"""
        return self.get_messages(query="is:unread", max_results=max_results)
    
    def get_emails_from_sender(self, sender_email: str, max_results: int = 20) -> List[EmailInfo]:
        """Récupère les emails d'un expéditeur spécifique"""
        query = f"from:{sender_email}"
        return self.get_messages(query=query, max_results=max_results)
    
    def get_emails_with_subject(self, subject_keyword: str, max_results: int = 20) -> List[EmailInfo]:
        """Récupère les emails avec un mot-clé dans le sujet"""
        query = f"subject:{subject_keyword}"
        return self.get_messages(query=query, max_results=max_results)
    
    def get_recent_emails(self, days: int = 7, max_results: int = 50) -> List[EmailInfo]:
        """Récupère les emails récents"""
        from datetime import date
        after_date = (date.today() - timedelta(days=days)).strftime('%Y/%m/%d')
        query = f"after:{after_date}"
        return self.get_messages(query=query, max_results=max_results)
    
    def get_labels(self) -> List[Dict]:
        """Récupère la liste des labels Gmail"""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            logger.info(f"{len(labels)} labels récupérés")
            return labels
            
        except Exception as e:
            logger.error(f"Erreur récupération labels : {e}")
            return []
    
    def create_label(self, name: str, visible: bool = True) -> Optional[str]:
        """Crée un nouveau label"""
        try:
            label_object = {
                'name': name,
                'labelListVisibility': 'labelShow' if visible else 'labelHide',
                'messageListVisibility': 'show'
            }
            
            result = self.service.users().labels().create(
                userId='me', body=label_object
            ).execute()
            
            logger.info(f"Label créé : {name}")
            return result['id']
            
        except Exception as e:
            logger.error(f"Erreur création label : {e}")
            return None
    
    def add_label_to_message(self, message_id: str, label_id: str) -> bool:
        """Ajoute un label à un message"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            
            logger.info(f"Label ajouté au message : {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur ajout label : {e}")
            return False
    
    def get_email_stats(self) -> Dict:
        """Récupère des statistiques sur les emails"""
        try:
            # Emails non lus
            unread = len(self.get_unread_emails(max_results=500))
            
            # Emails récents (7 derniers jours)
            recent = len(self.get_recent_emails(days=7, max_results=500))
            
            # Labels
            labels = self.get_labels()
            
            return {
                'unread_count': unread,
                'recent_count': recent,
                'total_labels': len(labels),
                'user_email': self.user_email
            }
            
        except Exception as e:
            logger.error(f"Erreur statistiques : {e}")
            return {}

# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration de logging pour test
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Crée le gestionnaire Gmail
        gmail = GmailManager()
        
        # Affiche les statistiques
        stats = gmail.get_email_stats()
        print(f"Statistiques Gmail : {stats}")
        
        # Récupère les emails non lus
        unread_emails = gmail.get_unread_emails(max_results=5)
        print(f"Emails non lus : {len(unread_emails)}")
        
        for email in unread_emails:
            print(f"- De: {email.sender}")
            print(f"  Sujet: {email.subject}")
            print(f"  Date: {email.date}")
            print()
            
    except ImportError:
        print("Google APIs non installées")
    except Exception as e:
        print(f"Erreur : {e}")
