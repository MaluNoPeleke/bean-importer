# BeanImporter

Lokale Web-App, die aus Kaffeeshop-URLs automatisch Bohnendaten extrahiert und das Beanconqueror-Formular ausfüllt.

## Setup

1. Python 3.12 installieren
2. `.env` anlegen (siehe `.env.example`) und `ANTHROPIC_API_KEY` eintragen
3. Dependencies installieren:
   ```
   pip install -r requirements.txt
   playwright install chromium
   ```
4. Server starten:
   ```
   uvicorn main:app --reload --port 8000
   ```
5. Browser öffnen: http://localhost:8000
