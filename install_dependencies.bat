@echo off
echo ========================================
echo     ARIA - Installation des dependances
echo ========================================
echo.

echo Installation des packages Python requis...
echo.

REM Mise a jour de pip
python -m pip install --upgrade pip

REM Packages de base
echo [1/6] Installation des packages de base...
pip install pyautogui pygetwindow psutil keyboard mouse

REM Packages web et automation
echo [2/6] Installation des packages d'automation web...
pip install selenium beautifulsoup4 requests

REM Packages IA et NLP
echo [3/6] Installation des packages IA...
pip install openai transformers torch spacy nltk

REM Packages API et services
echo [4/6] Installation des packages APIs...
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

REM Packages interface utilisateur
echo [5/6] Installation des packages UI...
pip install customtkinter pillow

REM Packages utilitaires
echo [6/6] Installation des packages utilitaires...
pip install schedule python-dotenv pydantic loguru rich typer

echo.
echo ========================================
echo     Installation terminee !
echo ========================================
echo.

echo Telechargement du modele spaCy francais...
python -m spacy download fr_core_news_sm

echo.
echo Pour demarrer ARIA, executez: python main.py
echo.
pause
