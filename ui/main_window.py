"""
Interface utilisateur principale pour ARIA
GUI moderne avec tkinter et customtkinter pour interagir avec l'assistant
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import time
from datetime import datetime
from typing import Optional, Dict, List, Callable
import logging
import os
import json

# Custom tkinter pour une interface moderne
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")  # Modes: "System" "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"
    CUSTOMTKINTER_AVAILABLE = True
except ImportError:
    CUSTOMTKINTER_AVAILABLE = False

logger = logging.getLogger(__name__)

class ARIAMainWindow:
    """Interface principale d'ARIA"""
    
    def __init__(self, aria_engine=None):
        self.aria_engine = aria_engine
        self.root = None
        self.is_running = False
        
        # Queues pour la communication avec l'engine
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Historique des conversations
        self.conversation_history = []
        
        # Callbacks
        self.callbacks = {
            'on_command': None,
            'on_start_listening': None,
            'on_stop_listening': None
        }
        
        # Initialisation de la fenêtre AVANT les variables Tkinter
        self._setup_window()
        
        # Variables d'état (après création de la fenêtre racine)
        self.is_listening = tk.BooleanVar(value=False)
        self.is_processing = tk.BooleanVar(value=False)
        self.current_status = tk.StringVar(value="Prêt")
        
        self._create_widgets()
        self._setup_bindings()
        
        # Thread pour traiter les réponses
        self.response_thread = threading.Thread(target=self._process_responses, daemon=True)
        self.response_thread.start()
    
    def _setup_window(self):
        """Configure la fenêtre principale"""
        if CUSTOMTKINTER_AVAILABLE:
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
            
        self.root.title("ARIA - Assistant IA Conversationnel")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Icône (optionnel)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "data", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Centre la fenêtre
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"1000x700+{x}+{y}")
    
    def _create_widgets(self):
        """Crée tous les widgets de l'interface"""
        
        # Frame principal
        if CUSTOMTKINTER_AVAILABLE:
            main_frame = ctk.CTkFrame(self.root)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            main_frame = ttk.Frame(self.root)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header avec titre et statut
        self._create_header(main_frame)
        
        # Zone de conversation
        self._create_conversation_area(main_frame)
        
        # Zone de saisie
        self._create_input_area(main_frame)
        
        # Panneau de contrôle
        self._create_control_panel(main_frame)
        
        # Barre de statut
        self._create_status_bar(main_frame)
    
    def _create_header(self, parent):
        """Crée l'en-tête avec titre et statut"""
        if CUSTOMTKINTER_AVAILABLE:
            header_frame = ctk.CTkFrame(parent)
            header_frame.pack(fill="x", padx=5, pady=(0, 10))
            
            # Titre
            title_label = ctk.CTkLabel(
                header_frame, 
                text="ARIA", 
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(side="left", padx=20, pady=15)
            
            # Statut
            self.status_label = ctk.CTkLabel(
                header_frame,
                textvariable=self.current_status,
                font=ctk.CTkFont(size=12)
            )
            self.status_label.pack(side="right", padx=20, pady=15)
            
        else:
            header_frame = ttk.Frame(parent)
            header_frame.pack(fill="x", padx=5, pady=(0, 10))
            
            # Titre
            title_label = ttk.Label(
                header_frame, 
                text="ARIA", 
                font=("Arial", 24, "bold")
            )
            title_label.pack(side="left", padx=20, pady=15)
            
            # Statut
            self.status_label = ttk.Label(
                header_frame,
                textvariable=self.current_status
            )
            self.status_label.pack(side="right", padx=20, pady=15)
    
    def _create_conversation_area(self, parent):
        """Crée la zone d'affichage des conversations"""
        if CUSTOMTKINTER_AVAILABLE:
            conv_frame = ctk.CTkFrame(parent)
            conv_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))
            
            # Textbox pour l'historique des conversations
            self.conversation_text = ctk.CTkTextbox(
                conv_frame,
                wrap="word",
                font=ctk.CTkFont(size=11)
            )
            self.conversation_text.pack(fill="both", expand=True, padx=10, pady=10)
            
        else:
            conv_frame = ttk.LabelFrame(parent, text="Conversation")
            conv_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))
            
            # Zone de texte avec scrollbar
            text_frame = ttk.Frame(conv_frame)
            text_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            self.conversation_text = scrolledtext.ScrolledText(
                text_frame,
                wrap=tk.WORD,
                state=tk.DISABLED,
                font=("Arial", 10)
            )
            self.conversation_text.pack(fill="both", expand=True)
        
        # Configuration des tags pour le formatage
        if not CUSTOMTKINTER_AVAILABLE:
            self.conversation_text.tag_configure("user", foreground="blue", font=("Arial", 10, "bold"))
            self.conversation_text.tag_configure("aria", foreground="green", font=("Arial", 10))
            self.conversation_text.tag_configure("system", foreground="red", font=("Arial", 9, "italic"))
            self.conversation_text.tag_configure("timestamp", foreground="gray", font=("Arial", 8))
    
    def _create_input_area(self, parent):
        """Crée la zone de saisie des commandes"""
        if CUSTOMTKINTER_AVAILABLE:
            input_frame = ctk.CTkFrame(parent)
            input_frame.pack(fill="x", padx=5, pady=(0, 10))
            
            # Label
            input_label = ctk.CTkLabel(input_frame, text="Votre commande :")
            input_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            # Frame pour l'entrée et boutons
            entry_frame = ctk.CTkFrame(input_frame)
            entry_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Zone de saisie
            self.command_entry = ctk.CTkEntry(
                entry_frame,
                placeholder_text="Tapez votre commande ou cliquez sur le micro...",
                font=ctk.CTkFont(size=11)
            )
            self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            # Bouton d'envoi
            self.send_button = ctk.CTkButton(
                entry_frame,
                text="Envoyer",
                command=self._send_text_command,
                width=100
            )
            self.send_button.pack(side="right", padx=(0, 5))
            
            # Bouton microphone
            self.mic_button = ctk.CTkButton(
                entry_frame,
                text="🎤",
                command=self._toggle_listening,
                width=50,
                font=ctk.CTkFont(size=16)
            )
            self.mic_button.pack(side="right")
            
        else:
            input_frame = ttk.LabelFrame(parent, text="Commande")
            input_frame.pack(fill="x", padx=5, pady=(0, 10))
            
            # Frame pour l'entrée et boutons
            entry_frame = ttk.Frame(input_frame)
            entry_frame.pack(fill="x", padx=5, pady=5)
            
            # Zone de saisie
            self.command_entry = ttk.Entry(entry_frame, font=("Arial", 11))
            self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            # Bouton d'envoi
            self.send_button = ttk.Button(
                entry_frame,
                text="Envoyer",
                command=self._send_text_command
            )
            self.send_button.pack(side="right", padx=(0, 5))
            
            # Bouton microphone
            self.mic_button = ttk.Button(
                entry_frame,
                text="🎤",
                command=self._toggle_listening,
                width=5
            )
            self.mic_button.pack(side="right")
    
    def _create_control_panel(self, parent):
        """Crée le panneau de contrôle"""
        if CUSTOMTKINTER_AVAILABLE:
            control_frame = ctk.CTkFrame(parent)
            control_frame.pack(fill="x", padx=5, pady=(0, 10))
            
            # Titre du panneau
            control_label = ctk.CTkLabel(control_frame, text="Contrôles")
            control_label.pack(pady=(10, 5))
            
            # Frame pour les boutons
            buttons_frame = ctk.CTkFrame(control_frame)
            buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Boutons de contrôle
            self.clear_button = ctk.CTkButton(
                buttons_frame,
                text="Effacer conversation",
                command=self._clear_conversation,
                width=150
            )
            self.clear_button.pack(side="left", padx=5, pady=10)
            
            self.save_button = ctk.CTkButton(
                buttons_frame,
                text="Sauvegarder",
                command=self._save_conversation,
                width=120
            )
            self.save_button.pack(side="left", padx=5, pady=10)
            
            self.settings_button = ctk.CTkButton(
                buttons_frame,
                text="Paramètres",
                command=self._show_settings,
                width=120
            )
            self.settings_button.pack(side="left", padx=5, pady=10)
            
            # Indicateur d'écoute
            self.listening_indicator = ctk.CTkLabel(
                buttons_frame,
                text="",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            self.listening_indicator.pack(side="right", padx=10, pady=10)
            
        else:
            control_frame = ttk.LabelFrame(parent, text="Contrôles")
            control_frame.pack(fill="x", padx=5, pady=(0, 10))
            
            # Frame pour les boutons
            buttons_frame = ttk.Frame(control_frame)
            buttons_frame.pack(fill="x", padx=5, pady=5)
            
            # Boutons de contrôle
            self.clear_button = ttk.Button(
                buttons_frame,
                text="Effacer conversation",
                command=self._clear_conversation
            )
            self.clear_button.pack(side="left", padx=5)
            
            self.save_button = ttk.Button(
                buttons_frame,
                text="Sauvegarder",
                command=self._save_conversation
            )
            self.save_button.pack(side="left", padx=5)
            
            self.settings_button = ttk.Button(
                buttons_frame,
                text="Paramètres",
                command=self._show_settings
            )
            self.settings_button.pack(side="left", padx=5)
            
            # Indicateur d'écoute
            self.listening_indicator = ttk.Label(
                buttons_frame,
                text="",
                font=("Arial", 12, "bold")
            )
            self.listening_indicator.pack(side="right", padx=10)
    
    def _create_status_bar(self, parent):
        """Crée la barre de statut"""
        if CUSTOMTKINTER_AVAILABLE:
            status_frame = ctk.CTkFrame(parent)
            status_frame.pack(fill="x", padx=5, pady=(0, 5))
            
            self.status_bar = ctk.CTkLabel(
                status_frame,
                text="Prêt",
                font=ctk.CTkFont(size=10)
            )
            self.status_bar.pack(side="left", padx=10, pady=5)
            
            # Indicateur de connexion
            self.connection_indicator = ctk.CTkLabel(
                status_frame,
                text="●",
                text_color="green",
                font=ctk.CTkFont(size=12)
            )
            self.connection_indicator.pack(side="right", padx=10, pady=5)
            
        else:
            status_frame = ttk.Frame(parent)
            status_frame.pack(fill="x", padx=5, pady=(0, 5))
            
            # Barre de statut
            self.status_bar = ttk.Label(
                status_frame,
                text="Prêt",
                relief=tk.SUNKEN,
                font=("Arial", 9)
            )
            self.status_bar.pack(side="left", fill="x", expand=True)
            
            # Indicateur de connexion
            self.connection_indicator = ttk.Label(
                status_frame,
                text="●",
                foreground="green",
                font=("Arial", 12)
            )
            self.connection_indicator.pack(side="right", padx=5)
    
    def _setup_bindings(self):
        """Configure les raccourcis clavier et événements"""
        # Raccourci Entrée pour envoyer
        self.command_entry.bind("<Return>", lambda e: self._send_text_command())
        
        # Raccourcis clavier
        self.root.bind("<Control-l>", lambda e: self._toggle_listening())
        self.root.bind("<Control-q>", lambda e: self.quit())
        self.root.bind("<Control-s>", lambda e: self._save_conversation())
        self.root.bind("<Escape>", lambda e: self._stop_listening())
        
        # Événement de fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        
        # Variables d'état
        self.is_listening.trace_add("write", self._on_listening_change)
        self.is_processing.trace_add("write", self._on_processing_change)
    
    def _send_text_command(self):
        """Envoie une commande textuelle"""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        # Efface la zone de saisie
        self.command_entry.delete(0, tk.END)
        
        # Affiche la commande dans la conversation
        self._add_to_conversation("user", command)
        
        # Envoie la commande à l'engine
        if self.callbacks['on_command']:
            threading.Thread(
                target=self.callbacks['on_command'],
                args=(command,),
                daemon=True
            ).start()
        
        # Met à jour le statut
        self.is_processing.set(True)
        self._update_status("Traitement en cours...")
    
    def _toggle_listening(self):
        """Active/désactive l'écoute vocale"""
        if self.is_listening.get():
            self._stop_listening()
        else:
            self._start_listening()
    
    def _start_listening(self):
        """Démarre l'écoute vocale"""
        if self.callbacks['on_start_listening']:
            threading.Thread(
                target=self.callbacks['on_start_listening'],
                daemon=True
            ).start()
        
        self.is_listening.set(True)
        self._update_status("Écoute en cours...")
    
    def _stop_listening(self):
        """Arrête l'écoute vocale"""
        if self.callbacks['on_stop_listening']:
            self.callbacks['on_stop_listening']()
        
        self.is_listening.set(False)
        self._update_status("Prêt")
    
    def _on_listening_change(self, *args):
        """Callback appelé quand l'état d'écoute change"""
        if self.is_listening.get():
            self.listening_indicator.configure(text="🔴 Écoute")
            if CUSTOMTKINTER_AVAILABLE:
                self.mic_button.configure(text="⏹", fg_color="red")
            else:
                self.mic_button.configure(text="⏹")
                
        else:
            self.listening_indicator.configure(text="")
            if CUSTOMTKINTER_AVAILABLE:
                self.mic_button.configure(text="🎤", fg_color=None)
            else:
                self.mic_button.configure(text="🎤")
    
    def _on_processing_change(self, *args):
        """Callback appelé quand l'état de traitement change"""
        if self.is_processing.get():
            self.send_button.configure(state="disabled")
        else:
            if CUSTOMTKINTER_AVAILABLE:
                self.send_button.configure(state="normal")
            else:
                self.send_button.configure(state="normal")
    
    def _add_to_conversation(self, speaker: str, text: str):
        """Ajoute un message à la conversation"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Ajoute à l'historique
        self.conversation_history.append({
            'timestamp': timestamp,
            'speaker': speaker,
            'text': text
        })
        
        # Affiche dans la zone de texte
        if CUSTOMTKINTER_AVAILABLE:
            # Format pour customtkinter
            if speaker == "user":
                prefix = f"[{timestamp}] Vous: "
            elif speaker == "aria":
                prefix = f"[{timestamp}] ARIA: "
            else:
                prefix = f"[{timestamp}] {speaker}: "
            
            self.conversation_text.insert("end", prefix + text + "\n\n")
            self.conversation_text.see("end")
        else:
            # Format pour tkinter standard avec tags
            self.conversation_text.configure(state=tk.NORMAL)
            
            # Timestamp
            self.conversation_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            
            # Nom du speaker
            if speaker == "user":
                self.conversation_text.insert(tk.END, "Vous: ", "user")
            elif speaker == "aria":
                self.conversation_text.insert(tk.END, "ARIA: ", "aria")
            else:
                self.conversation_text.insert(tk.END, f"{speaker}: ", "system")
            
            # Message
            self.conversation_text.insert(tk.END, text + "\n\n")
            
            # Auto-scroll
            self.conversation_text.see(tk.END)
            self.conversation_text.configure(state=tk.DISABLED)
    
    def _clear_conversation(self):
        """Efface la conversation"""
        result = messagebox.askyesno("Confirmation", "Effacer toute la conversation ?")
        if result:
            if CUSTOMTKINTER_AVAILABLE:
                self.conversation_text.delete("1.0", "end")
            else:
                self.conversation_text.configure(state=tk.NORMAL)
                self.conversation_text.delete("1.0", tk.END)
                self.conversation_text.configure(state=tk.DISABLED)
            
            self.conversation_history.clear()
            self._update_status("Conversation effacée")
    
    def _save_conversation(self):
        """Sauvegarde la conversation"""
        if not self.conversation_history:
            messagebox.showinfo("Info", "Aucune conversation à sauvegarder")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        for entry in self.conversation_history:
                            f.write(f"[{entry['timestamp']}] {entry['speaker']}: {entry['text']}\n")
                
                self._update_status(f"Conversation sauvegardée: {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
    
    def _show_settings(self):
        """Affiche la fenêtre des paramètres"""
        settings_window = ARIASettingsWindow(self.root)
        settings_window.show()
    
    def _process_responses(self):
        """Thread pour traiter les réponses de l'engine"""
        while self.is_running:
            try:
                # Vérifie s'il y a des réponses à traiter
                try:
                    response = self.response_queue.get(timeout=0.1)
                    
                    # Traite la réponse
                    if response['type'] == 'text':
                        self._add_to_conversation("aria", response['text'])
                    elif response['type'] == 'status':
                        self._update_status(response['text'])
                    elif response['type'] == 'error':
                        self._add_to_conversation("system", f"Erreur: {response['text']}")
                    
                    self.response_queue.task_done()
                    
                except queue.Empty:
                    continue
                    
            except Exception as e:
                logger.error(f"Erreur traitement réponse: {e}")
                
            time.sleep(0.1)
    
    def _update_status(self, status: str):
        """Met à jour le statut"""
        self.current_status.set(status)
        if hasattr(self, 'status_bar'):
            if CUSTOMTKINTER_AVAILABLE:
                self.status_bar.configure(text=status)
            else:
                self.status_bar.configure(text=status)
    
    def add_response(self, response_type: str, text: str):
        """Ajoute une réponse à la queue (thread-safe)"""
        self.response_queue.put({
            'type': response_type,
            'text': text
        })
        
        if response_type in ['text', 'error']:
            self.is_processing.set(False)
    
    def set_callback(self, event: str, callback: Callable):
        """Définit un callback pour un événement"""
        if event in self.callbacks:
            self.callbacks[event] = callback
    
    def run(self):
        """Lance l'interface graphique"""
        self.is_running = True
        logger.info("Démarrage de l'interface ARIA")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Interruption clavier")
        finally:
            self.is_running = False
    
    def quit(self):
        """Ferme l'application"""
        self.is_running = False
        self.root.quit()
        self.root.destroy()


class ARIASettingsWindow:
    """Fenêtre des paramètres d'ARIA"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.settings = {}
        self._load_settings()
    
    def _load_settings(self):
        """Charge les paramètres sauvegardés"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), "..", "config", "ui_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement paramètres: {e}")
        
        # Paramètres par défaut
        default_settings = {
            'voice_enabled': True,
            'auto_scroll': True,
            'confirm_actions': True,
            'theme': 'dark',
            'font_size': 11
        }
        
        for key, value in default_settings.items():
            if key not in self.settings:
                self.settings[key] = value
    
    def show(self):
        """Affiche la fenêtre des paramètres"""
        if CUSTOMTKINTER_AVAILABLE:
            self.window = ctk.CTkToplevel(self.parent)
        else:
            self.window = tk.Toplevel(self.parent)
        
        self.window.title("Paramètres ARIA")
        self.window.geometry("400x300")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Centre la fenêtre
        x = self.parent.winfo_x() + 50
        y = self.parent.winfo_y() + 50
        self.window.geometry(f"400x300+{x}+{y}")
        
        self._create_settings_widgets()
    
    def _create_settings_widgets(self):
        """Crée les widgets des paramètres"""
        if CUSTOMTKINTER_AVAILABLE:
            main_frame = ctk.CTkFrame(self.window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Titre
            title_label = ctk.CTkLabel(main_frame, text="Paramètres", font=ctk.CTkFont(size=16, weight="bold"))
            title_label.pack(pady=(10, 20))
            
            # Paramètres vocaux
            voice_frame = ctk.CTkFrame(main_frame)
            voice_frame.pack(fill="x", padx=10, pady=5)
            
            voice_label = ctk.CTkLabel(voice_frame, text="Reconnaissance vocale")
            voice_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            self.voice_var = tk.BooleanVar(value=self.settings['voice_enabled'])
            voice_check = ctk.CTkCheckBox(voice_frame, text="Activer la reconnaissance vocale", variable=self.voice_var)
            voice_check.pack(anchor="w", padx=10, pady=(0, 10))
            
            # Interface
            ui_frame = ctk.CTkFrame(main_frame)
            ui_frame.pack(fill="x", padx=10, pady=5)
            
            ui_label = ctk.CTkLabel(ui_frame, text="Interface")
            ui_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            self.scroll_var = tk.BooleanVar(value=self.settings['auto_scroll'])
            scroll_check = ctk.CTkCheckBox(ui_frame, text="Défilement automatique", variable=self.scroll_var)
            scroll_check.pack(anchor="w", padx=10, pady=2)
            
            self.confirm_var = tk.BooleanVar(value=self.settings['confirm_actions'])
            confirm_check = ctk.CTkCheckBox(ui_frame, text="Confirmer les actions", variable=self.confirm_var)
            confirm_check.pack(anchor="w", padx=10, pady=(2, 10))
            
            # Boutons
            button_frame = ctk.CTkFrame(main_frame)
            button_frame.pack(fill="x", padx=10, pady=(20, 10))
            
            save_button = ctk.CTkButton(button_frame, text="Sauvegarder", command=self._save_settings)
            save_button.pack(side="left", padx=10, pady=10)
            
            cancel_button = ctk.CTkButton(button_frame, text="Annuler", command=self.window.destroy)
            cancel_button.pack(side="right", padx=10, pady=10)
            
        else:
            # Version tkinter standard
            main_frame = ttk.Frame(self.window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Titre
            title_label = ttk.Label(main_frame, text="Paramètres", font=("Arial", 14, "bold"))
            title_label.pack(pady=(0, 20))
            
            # Paramètres vocaux
            voice_frame = ttk.LabelFrame(main_frame, text="Reconnaissance vocale")
            voice_frame.pack(fill="x", pady=5)
            
            self.voice_var = tk.BooleanVar(value=self.settings['voice_enabled'])
            voice_check = ttk.Checkbutton(voice_frame, text="Activer la reconnaissance vocale", variable=self.voice_var)
            voice_check.pack(anchor="w", padx=10, pady=10)
            
            # Interface
            ui_frame = ttk.LabelFrame(main_frame, text="Interface")
            ui_frame.pack(fill="x", pady=5)
            
            self.scroll_var = tk.BooleanVar(value=self.settings['auto_scroll'])
            scroll_check = ttk.Checkbutton(ui_frame, text="Défilement automatique", variable=self.scroll_var)
            scroll_check.pack(anchor="w", padx=10, pady=5)
            
            self.confirm_var = tk.BooleanVar(value=self.settings['confirm_actions'])
            confirm_check = ttk.Checkbutton(ui_frame, text="Confirmer les actions", variable=self.confirm_var)
            confirm_check.pack(anchor="w", padx=10, pady=5)
            
            # Boutons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", pady=20)
            
            save_button = ttk.Button(button_frame, text="Sauvegarder", command=self._save_settings)
            save_button.pack(side="left", padx=5)
            
            cancel_button = ttk.Button(button_frame, text="Annuler", command=self.window.destroy)
            cancel_button.pack(side="right", padx=5)
    
    def _save_settings(self):
        """Sauvegarde les paramètres"""
        self.settings['voice_enabled'] = self.voice_var.get()
        self.settings['auto_scroll'] = self.scroll_var.get()
        self.settings['confirm_actions'] = self.confirm_var.get()
        
        try:
            settings_file = os.path.join(os.path.dirname(__file__), "..", "config", "ui_settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            
            messagebox.showinfo("Succès", "Paramètres sauvegardés")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur sauvegarde: {e}")

# Test de l'interface
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    def test_command_callback(command):
        """Callback de test pour les commandes"""
        time.sleep(1)  # Simule un traitement
        app.add_response("text", f"J'ai reçu votre commande: {command}")
    
    app = ARIAMainWindow()
    app.set_callback('on_command', test_command_callback)
    
    app.add_response("text", "Bonjour ! Je suis ARIA, votre assistant IA. Comment puis-je vous aider ?")
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("Interface fermée")
