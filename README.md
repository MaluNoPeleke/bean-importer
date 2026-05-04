# BeanImporter

Lokale Web-App, die aus Kaffeeshop-URLs automatisch Bohnendaten extrahiert und das Beanconqueror-Formular ausfüllt.

## Setup

1. Python 3.12 installieren
2. `.env` anlegen (siehe `.env.example`): `LLM_MODEL` setzen und den passenden Provider-Key eintragen (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY` oder `GEMINI_API_KEY`)
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

## Autostart bei Anmeldung (Windows)

Damit der Server nach jedem Login automatisch im Hintergrund läuft, gibt es ein PowerShell-Script, das einen Scheduled Task registriert:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_task.ps1
```

- Trigger: bei Benutzer-Anmeldung
- Aktion: `python -m uvicorn main:app --host 127.0.0.1 --port 8000` ohne Konsolenfenster
- Logs: `logs\server.log` (vorherige Version wird beim Start zu `logs\server.log.1` rotiert)
- Sofort starten ohne Reboot: `Start-ScheduledTask -TaskName BeanImporter`
- Wieder entfernen: `powershell -ExecutionPolicy Bypass -File scripts\uninstall_task.ps1`
