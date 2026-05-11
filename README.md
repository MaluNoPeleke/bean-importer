# BeanImporter

Lokale Web-App für Windows, die aus Kaffeeshop-URLs automatisch Bohnendaten extrahiert
und sie als Beanconqueror-Import-Link aufbereitet (QR-Code zum Abscannen mit der
Beanconqueror-App auf dem Handy).

- **LLM-gestützt** (Anthropic / OpenAI / Gemini — wählbar im Browser, BYOK)
- **Läuft komplett lokal** als FastAPI-Server auf `127.0.0.1:8000`
- **Autostart** via Windows Scheduled Task, launchd (macOS) oder systemd (Linux) — kein Terminal nötig
- **Schneller Beanconqueror-Export**: Payload wird direkt als Protobuf erzeugt (kein Browser-Roundtrip)

## Voraussetzungen

- Windows 10/11
- [Python ≥ 3.12](https://www.python.org/downloads/) — beim Installieren **„Add Python to PATH"** aktivieren
- Ein API-Key für einen LLM-Provider:
  - [Anthropic](https://console.anthropic.com/settings/keys) (empfohlen)
  - [OpenAI](https://platform.openai.com/api-keys)
  - [Google Gemini](https://aistudio.google.com/apikey)

## Installation

1. Repo klonen oder ZIP herunterladen und entpacken.
2. PowerShell im Projektordner öffnen.
3. Installer ausführen:

   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```

   Der Installer prüft Python, installiert die Pakete, registriert den
   Scheduled Task und öffnet den Browser.

4. Im Browser im Onboarding-Dialog **Provider wählen** und **API-Key** eingeben →
   *Testen* → *Speichern*. Fertig.

Ab jetzt läuft der Server bei jedem Login automatisch im Hintergrund. Erreichbar
unter <http://127.0.0.1:8000/>.

## Benutzung

1. URL einer Produktseite (Kaffeeröster) eingeben → **Extrahieren**.
2. Daten prüfen / korrigieren.
3. **In Beanconqueror eintragen** → QR-Code wird angezeigt.
4. Mit der Beanconqueror-App auf dem Handy scannen — der Import startet automatisch.

## Verwaltung

| Aktion | Befehl |
| --- | --- |
| Server neustarten | `Start-ScheduledTask -TaskName BeanImporter` |
| Server stoppen | `Stop-ScheduledTask -TaskName BeanImporter` |
| Provider/Key ändern | ⚙-Icon oben rechts in der Web-UI |
| Deinstallieren (Task entfernen) | `powershell -ExecutionPolicy Bypass -File scripts\uninstall_task.ps1` |
| Logs ansehen | `logs\server.log` (vorherige Version: `logs\server.log.1`) |

## Troubleshooting

- **„Server nicht erreichbar"** im Browser → Task wurde noch nicht gestartet:
  `Start-ScheduledTask -TaskName BeanImporter`.
- **Port 8000 belegt** → alten Prozess killen:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 -State Listen |
      Select-Object -First 1 -ExpandProperty OwningProcess |
      ForEach-Object { Stop-Process -Id $_ -Force }
  Start-ScheduledTask -TaskName BeanImporter
  ```
- **Fehlerbanner „Einstellungen öffnen"** → Key ungültig oder abgelaufen, im Modal neuen Key hinterlegen.
- **Cache-Probleme nach Code-Änderungen** → `__pycache__\` löschen und Server neu starten.

## Architektur (kurz)

```
Browser ──HTTP── FastAPI (uvicorn, lokal) ─┬── scraper.py     (HTML laden)
                                           ├── researcher.py  (Web-Suche)
                                           ├── extractor.py   (LiteLLM → JSON)
                                           └── share_link.py  (Protobuf-Encoder)
```

`share_link.py` erzeugt eine `https://beanconqueror.com/?shareUserBean0=…`-URL
byte-für-byte identisch zum offiziellen JS-Encoder. **Wichtig:** der Beanconqueror-Import-Handler
verwirft Payloads stillschweigend, wenn nicht *alle* Felder gesetzt sind — Defaults daher
explizit (siehe Kommentare in `share_link.py`).

## Lizenz

[MIT](LICENSE)
