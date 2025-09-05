"""
🌐 Module d'Automation Web Avancé pour ARIA
===========================================

Système d'automation web intelligent capable de :
- Contrôler n'importe quel navigateur (Chrome, Firefox, Edge)
- Navigation web intelligente avec recherche et clic automatiques
- Extraction de contenu et interaction avec les pages web
- Gestion des formulaires et authentification
- Screenshot et monitoring des pages
"""

import time
import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import asyncio
import requests
from urllib.parse import urljoin, urlparse

# Selenium pour automation navigateur
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import *

# BeautifulSoup pour parsing HTML
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@dataclass
class WebElement:
    """Représente un élément web trouvé"""
    tag: str
    text: str
    attributes: Dict[str, str]
    position: Tuple[int, int]
    size: Tuple[int, int]
    is_clickable: bool
    is_visible: bool
    xpath: str
    css_selector: str

@dataclass
class SearchResult:
    """Résultat de recherche web"""
    title: str
    url: str
    description: str
    position: int
    element: WebElement

class WebAutomation:
    """Contrôleur d'automation web intelligent"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.driver = None
        self.current_url = ""
        self.current_page_source = ""
        self.wait_timeout = self.config.get('wait_timeout', 10)
        self.implicit_wait = self.config.get('implicit_wait', 5)
        
        # Préférences de navigateur
        self.preferred_browser = self.config.get('browser', 'chrome')
        self.headless = self.config.get('headless', False)
        
        # Cache des éléments trouvés
        self.elements_cache = {}
        self.last_search_results = []
        
        logger.info("🌐 Module d'automation web initialisé")
    
    def start_browser(self, browser_name: str = None, url: str = None) -> bool:
        """Démarre le navigateur spécifié"""
        try:
            browser = browser_name or self.preferred_browser
            
            if browser.lower() == 'chrome':
                self.driver = self._setup_chrome()
            elif browser.lower() == 'firefox':
                self.driver = self._setup_firefox()
            elif browser.lower() == 'edge':
                self.driver = self._setup_edge()
            else:
                raise ValueError(f"Navigateur non supporté: {browser}")
            
            if self.driver:
                self.driver.implicitly_wait(self.implicit_wait)
                logger.info(f"Navigateur {browser} démarré")
                
                if url:
                    return self.navigate_to(url)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur démarrage navigateur : {e}")
            return False
    
    def _setup_chrome(self) -> webdriver.Chrome:
        """Configure Chrome WebDriver"""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Options pour éviter la détection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent plus naturel
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _setup_firefox(self) -> webdriver.Firefox:
        """Configure Firefox WebDriver"""
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Profile personnalisé
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", 
                             "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0")
        
        return webdriver.Firefox(firefox_profile=profile, options=options)
    
    def _setup_edge(self) -> webdriver.Edge:
        """Configure Edge WebDriver"""
        options = EdgeOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        return webdriver.Edge(options=options)
    
    def navigate_to(self, url: str) -> bool:
        """Navigue vers une URL"""
        try:
            if not self.driver:
                if not self.start_browser():
                    return False
            
            # Ajoute http:// si nécessaire
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.driver.get(url)
            self.current_url = self.driver.current_url
            self.current_page_source = self.driver.page_source
            
            logger.info(f"Navigation vers : {url}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur navigation : {e}")
            return False
    
    def search_google(self, query: str, result_number: int = 1) -> Optional[str]:
        """Effectue une recherche Google et retourne l'URL du résultat spécifié"""
        try:
            # Va sur Google
            if not self.navigate_to("https://www.google.com"):
                return None
            
            # Accepte les cookies si nécessaire
            self._handle_google_cookies()
            
            # Trouve la barre de recherche
            search_box = self.find_element_smart("input[name='q']", "search box")
            if not search_box:
                return None
            
            # Tape la requête
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            # Attend les résultats
            self.wait_for_page_load()
            
            # Trouve les résultats de recherche
            results = self.driver.find_elements(By.CSS_SELECTOR, "h3")
            
            if results and len(results) >= result_number:
                target_result = results[result_number - 1]
                # Trouve le lien parent
                link_element = target_result.find_element(By.XPATH, "./ancestor::a")
                url = link_element.get_attribute("href")
                
                logger.info(f"Résultat #{result_number} trouvé : {url}")
                return url
            
            logger.warning(f"Pas assez de résultats (trouvés: {len(results)}, demandé: #{result_number})")
            return None
            
        except Exception as e:
            logger.error(f"Erreur recherche Google : {e}")
            return None
    
    def search_youtube_videos(self, query: str, result_number: int = 1) -> Optional[str]:
        """Recherche des vidéos YouTube et retourne l'URL du résultat spécifié"""
        try:
            # Va sur YouTube
            if not self.navigate_to("https://www.youtube.com"):
                return None
            
            # Trouve la barre de recherche
            search_box = self.find_element_smart("input[name='search_query']", "YouTube search")
            if not search_box:
                return None
            
            # Tape la requête
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            # Attend les résultats
            self.wait_for_page_load()
            time.sleep(2)  # YouTube charge dynamiquement
            
            # Trouve les vidéos (évite les publicités et suggestions)
            video_links = self.driver.find_elements(By.CSS_SELECTOR, "a#video-title")
            
            if video_links and len(video_links) >= result_number:
                target_video = video_links[result_number - 1]
                url = target_video.get_attribute("href")
                title = target_video.get_attribute("title")
                
                logger.info(f"Vidéo #{result_number} trouvée : {title} - {url}")
                return url
            
            logger.warning(f"Pas assez de vidéos (trouvées: {len(video_links)}, demandé: #{result_number})")
            return None
            
        except Exception as e:
            logger.error(f"Erreur recherche YouTube : {e}")
            return None
    
    def click_element(self, element_or_selector: Union[str, WebElement], wait_time: float = 2) -> bool:
        """Clique sur un élément de manière intelligente"""
        try:
            element = None
            
            if isinstance(element_or_selector, str):
                element = self.find_element_smart(element_or_selector)
            else:
                # Assume que c'est déjà un WebElement Selenium
                element = element_or_selector
            
            if not element:
                logger.error("Élément à cliquer non trouvé")
                return False
            
            # Scroll vers l'élément si nécessaire
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Essaie plusieurs méthodes de clic
            try:
                # Méthode 1: Clic normal
                element.click()
            except ElementClickInterceptedException:
                # Méthode 2: ActionChains
                ActionChains(self.driver).move_to_element(element).click().perform()
            except:
                # Méthode 3: JavaScript
                self.driver.execute_script("arguments[0].click();", element)
            
            time.sleep(wait_time)
            logger.info("Élément cliqué avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur clic élément : {e}")
            return False
    
    def find_element_smart(self, selector_or_text: str, description: str = "") -> Optional[Any]:
        """Trouve un élément de manière intelligente (CSS, XPath, texte)"""
        try:
            element = None
            
            # Essaie CSS selector
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector_or_text)
                if element.is_displayed():
                    return element
            except:
                pass
            
            # Essaie XPath
            try:
                element = self.driver.find_element(By.XPATH, selector_or_text)
                if element.is_displayed():
                    return element
            except:
                pass
            
            # Essaie par texte (liens et boutons)
            try:
                element = self.driver.find_element(By.PARTIAL_LINK_TEXT, selector_or_text)
                if element.is_displayed():
                    return element
            except:
                pass
            
            # Essaie XPath avec texte contenant
            try:
                xpath = f"//*[contains(text(), '{selector_or_text}')]"
                element = self.driver.find_element(By.XPATH, xpath)
                if element.is_displayed():
                    return element
            except:
                pass
            
            # Essaie par attributs communs
            common_attributes = ['name', 'id', 'class', 'placeholder', 'aria-label']
            for attr in common_attributes:
                try:
                    xpath = f"//*[@{attr}='{selector_or_text}']"
                    element = self.driver.find_element(By.XPATH, xpath)
                    if element.is_displayed():
                        return element
                except:
                    continue
            
            logger.warning(f"Élément non trouvé : {selector_or_text} ({description})")
            return None
            
        except Exception as e:
            logger.error(f"Erreur recherche élément : {e}")
            return None
    
    def type_text(self, selector_or_element: Union[str, Any], text: str, clear_first: bool = True) -> bool:
        """Tape du texte dans un champ"""
        try:
            element = None
            
            if isinstance(selector_or_element, str):
                element = self.find_element_smart(selector_or_element)
            else:
                element = selector_or_element
            
            if not element:
                return False
            
            if clear_first:
                element.clear()
            
            element.send_keys(text)
            logger.info(f"Texte tapé : {text}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur saisie texte : {e}")
            return False
    
    def wait_for_page_load(self, timeout: int = None) -> bool:
        """Attend que la page soit complètement chargée"""
        try:
            timeout = timeout or self.wait_timeout
            
            # Attend que document.readyState soit complete
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Attend un peu plus pour les contenus dynamiques
            time.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Timeout chargement page : {e}")
            return False
    
    def _handle_google_cookies(self):
        """Gère les popups de cookies Google"""
        try:
            # Cherche les boutons d'acceptation communs
            accept_buttons = [
                "button[id*='accept']",
                "button[id*='agree']", 
                "button:contains('Accept')",
                "button:contains('Accepter')",
                "button:contains('J\\'accepte')"
            ]
            
            for selector in accept_buttons:
                try:
                    button = self.find_element_smart(selector)
                    if button:
                        button.click()
                        time.sleep(1)
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Gestion cookies : {e}")
    
    def take_screenshot(self, save_path: str = None) -> bool:
        """Prend une capture d'écran de la page"""
        try:
            if not self.driver:
                return False
            
            if save_path:
                self.driver.save_screenshot(save_path)
                logger.info(f"Screenshot sauvé : {save_path}")
            else:
                # Sauvegarde avec timestamp
                timestamp = int(time.time())
                save_path = f"screenshot_{timestamp}.png"
                self.driver.save_screenshot(save_path)
                logger.info(f"Screenshot sauvé : {save_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur screenshot : {e}")
            return False
    
    def get_page_text(self) -> str:
        """Récupère tout le texte de la page"""
        try:
            if not self.driver:
                return ""
            
            return self.driver.find_element(By.TAG_NAME, "body").text
            
        except Exception as e:
            logger.error(f"Erreur récupération texte : {e}")
            return ""
    
    def scroll_page(self, direction: str = "down", amount: int = 3) -> bool:
        """Scroll la page"""
        try:
            if direction.lower() == "down":
                for _ in range(amount):
                    self.driver.execute_script("window.scrollBy(0, 300);")
                    time.sleep(0.5)
            elif direction.lower() == "up":
                for _ in range(amount):
                    self.driver.execute_script("window.scrollBy(0, -300);")
                    time.sleep(0.5)
            elif direction.lower() == "top":
                self.driver.execute_script("window.scrollTo(0, 0);")
            elif direction.lower() == "bottom":
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur scroll : {e}")
            return False
    
    def close_browser(self):
        """Ferme le navigateur"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Navigateur fermé")
                
        except Exception as e:
            logger.error(f"Erreur fermeture navigateur : {e}")
    
    def __del__(self):
        """Destructeur - ferme le navigateur automatiquement"""
        self.close_browser()

# Exemple d'utilisation
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test de l'automation web
    web = WebAutomation({'headless': False})
    
    # Ouvre Firefox
    if web.start_browser('firefox'):
        # Recherche une vidéo de chat sur Google
        url = web.search_google("cat video youtube")
        if url:
            web.navigate_to(url)
            time.sleep(3)
        
        # Prend une capture d'écran
        web.take_screenshot("test_screenshot.png")
        
        time.sleep(5)
        web.close_browser()
