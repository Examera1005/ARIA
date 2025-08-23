"""
Module APIs pour ARIA
Intégration des APIs externes : Gmail, Calendar, réseaux sociaux, etc.
"""

try:
    from .gmail_manager import GmailManager, EmailInfo, EmailAttachment
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

try:
    from .calendar_manager import CalendarManager, CalendarEvent, CalendarInfo
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

__all__ = []

if GMAIL_AVAILABLE:
    __all__.extend(['GmailManager', 'EmailInfo', 'EmailAttachment'])

if CALENDAR_AVAILABLE:
    __all__.extend(['CalendarManager', 'CalendarEvent', 'CalendarInfo'])
