# BeanImporter – Entwicklungsplan

## Ziel

Lokale Web-App auf Windows, die aus einer Kaffeeshop-Produkt-URL automatisch Bohnendaten extrahiert und das Beanconqueror-Formular unter `https://beanconqueror.com/create/` vollautomatisch ausfüllt. User prüft die extrahierten Daten vor dem Eintragen und speichert das Formular am Ende selbst.

## Kontext

- **Plattform**: Windows-Rechner, lokal (kein Deployment)
- **Projektpfad**: `C:\Users\country\Projekte\bean-importer\`
- **Beispiel-URL**: `https://danastassio-aachen.de/product/cemorrado-chocolate/`
- **Ziel-Formular**: `https://beanconqueror.com/create/` (Angular-PWA von github.com/graphefruit/Beanconqueror)
- **Sprache**: Python 3.12

## Stack

| Komponente | Technologie | Begründung |
|---|---|---|
| Backend | Python + FastAPI | Leichtgewichtig, asynchron |
| Scraping (primär) | `httpx` + `BeautifulSoup` | Schnell, kein JS |
| Scraping (Fallback) | Playwright (headless) | Wenn Fetch blockiert oder leer |
| KI-Extraktion | Anthropic API, Modell `claude-sonnet-4-20250514` | Strukturiertes JSON aus rohem HTML |
| Formular-Automation | Playwright (Python, headed Mode) | Angular braucht echten Browser |
| Frontend | Statisches HTML/JS, single file | Kein Build-Step |
| Auth | API-Key via `.env` | `python-dotenv` |

## Projektstruktur

```
C:\Users\country\Projekte\bean-importer\
├── main.py              # FastAPI-Server + Endpunkte
├── scraper.py           # Fetch + Playwright-Fallback
├── extractor.py         # Claude API → strukturiertes JSON
├── form_filler.py       # Playwright → Beanconqueror ausfüllen
├── models.py            # Pydantic-Schema: BeanData, VarietyData
├── index.html           # Frontend
├── requirements.txt
├── .env                 # ANTHROPIC_API_KEY (NICHT committen)
├── .gitignore
└── README.md
```

## Datenmodell

```python
# models.py
from pydantic import BaseModel
from typing import Optional

class VarietyData(BaseModel):
    percentage: Optional[int] = None
    country: Optional[str] = None
    region: Optional[str] = None
    variety: Optional[str] = None       # z.B. "Catuai"
    processing: Optional[str] = None    # "Natural", "Washed", ...
    altitude: Optional[str] = None      # z.B. "1250 m"

class BeanData(BaseModel):
    # Tab 1 – General
    name: str
    roaster: Optional[str] = None
    roast_date: Optional[str] = None         # ISO-Date oder None
    roast_type: Optional[str] = None         # "Espresso", "Filter"
    degree_of_roast: Optional[int] = None    # 0–100
    roast_style: Optional[str] = None
    is_blend: bool = False
    weight: Optional[int] = None             # Gramm
    price: Optional[float] = None
    flavour_profile: Optional[str] = None
    notes: Optional[str] = None
    website: Optional[str] = None
    # Tab 2
    varieties: list[VarietyData] = []
```

## Workflow (Laufzeit)

```
User gibt URL ein (Frontend)
    │
    ▼
1. POST /extract  → scraper.py
   httpx-GET mit realistischem User-Agent
   ├─ HTML enthält Produkttext? → weiter zu (3)
   └─ leer/blockiert/<200 Status? → (2)
    │
    ▼
2. Playwright-Fallback
   chromium headless, page.goto(url),
   wait_for_load_state('networkidle'),
   page.content()
    │
    ▼
3. extractor.py
   HTML auf <main>/<article>/<body> reduzieren,
   Skripte/Styles/Nav entfernen → ca. 5–15k Tokens
   Anthropic API-Call mit System-Prompt:
   "Extrahiere Kaffeebohnen-Daten gemäß Schema.
    Felder ohne Angabe: null. Antworte ausschließlich
    mit JSON, ohne Markdown-Fences."
   → Pydantic-Validierung
    │
    ▼
4. Frontend zeigt JSON in editierbaren Feldern
   User korrigiert/ergänzt manuell
    │  Klick: "In Beanconqueror eintragen"
    ▼
5. POST /fill → form_filler.py
   Playwright (headed!) öffnet beanconqueror.com/create/
   füllt Tab 1, wechselt Tab 2, fügt Varietäten dynamisch
   submitted NICHT — User prüft + speichert selbst
```

## Phasenplan für Claude Code

### Phase 1 – Setup
1. Verzeichnis `C:\Users\country\Projekte\bean-importer\` anlegen
2. `requirements.txt`:
   ```
   fastapi
   uvicorn[standard]
   httpx
   beautifulsoup4
   lxml
   playwright
   anthropic
   pydantic
   python-dotenv
   ```
3. `.gitignore`: `.env`, `__pycache__/`, `.venv/`, `*.pyc`
4. FastAPI-Grundgerüst in `main.py` mit:
   - `GET /` → liefert `index.html`
   - `POST /extract` (Body: `{url: str}`) → Stub
   - `POST /fill` (Body: `BeanData`) → Stub
   - CORS für `localhost`
5. `.env.example` mit `ANTHROPIC_API_KEY=`
6. Minimales `index.html` mit URL-Input + leerem Formular-Bereich
7. README mit Setup-Anweisungen

**STOPP — auf User-OK warten**

### Phase 2 – Scraping
8. `scraper.py`:
   - `async fetch_html(url) -> str | None`: httpx mit User-Agent eines aktuellen Chrome
   - `async fetch_with_playwright(url) -> str`: Fallback
   - `clean_html(html) -> str`: entfernt `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`; reduziert auf `<main>` oder `<article>`, ansonsten `<body>`
   - Heuristik: Fallback wenn HTML kürzer als 500 Zeichen ODER Status ≠ 200 ODER kein `<body>`-Inhalt
9. Test mit Beispiel-URL und Logging

**STOPP**

### Phase 3 – Extraktion
10. `extractor.py`:
    - System-Prompt mit eingebettetem Pydantic-Schema (JSON Schema)
    - User-Prompt: das bereinigte HTML
    - Modell: `claude-sonnet-4-20250514`, `max_tokens: 2000`
    - JSON aus Response parsen, gegen `BeanData` validieren
    - Bei Validierungsfehler: zweiter Versuch mit Fehler-Feedback
11. `/extract`-Endpunkt verkabeln
12. Test mit Beispiel-URL → JSON in Konsole prüfen

**STOPP**

### Phase 4 – Formular-Analyse + Automation
13. **Erst analysieren, dann coden**:
    - Manuell mit Playwright `page.content()` von `beanconqueror.com/create/` dumpen
    - Selektoren für jedes Feld dokumentieren (`name`, `id`, `formControlName`)
    - Tab-Struktur erfassen (wie wechselt man zwischen Tab 1 und 2?)
    - "+"-Button für Varietäten finden
14. `form_filler.py`:
    - Playwright **headed** (`headless=False`), damit User sieht was passiert
    - Helper `set_input(page, selector, value)` der `fill()` + `dispatchEvent('input')` + `dispatchEvent('change')` macht
    - Felder in der Reihenfolge des Formulars ausfüllen
    - Tab-Wechsel
    - Pro Varietät: "+" klicken, dann Felder befüllen
    - **Kein submit** — Browser bleibt offen
15. `/fill`-Endpunkt verkabeln

**STOPP**

### Phase 5 – Frontend-Polish
16. `index.html`:
    - URL-Input + "Extrahieren"-Button
    - Loading-State während `/extract`
    - Editierbare Formularfelder mit JSON-Vorbefüllung
    - Varietäten-Liste mit Add/Remove
    - "In Beanconqueror eintragen"-Button → `/fill`
    - Fehler-Banner bei API-Problemen
17. End-to-End-Test mit `https://danastassio-aachen.de/product/cemorrado-chocolate/`

## Kritische Hinweise

- **Beanconqueror ist Angular**: `page.fill()` allein reicht nicht — Events müssen explizit getriggert werden, sonst übernimmt Angular den Wert nicht ins Model.
- **Playwright headed**: Für `form_filler.py` zwingend `headless=False`, damit User das Ergebnis sieht und manuell speichert.
- **API-Key**: Niemals in Code, niemals in Git. Nur `.env`. `.env` in `.gitignore`.
- **Rate Limits**: Anthropic API hat tier-abhängige Limits. Bei lokalem Single-User-Betrieb irrelevant.
- **Robustheit**: Shops haben unterschiedliche HTML-Strukturen. Die KI-Extraktion ist genau deshalb der richtige Ansatz — kein Shop-spezifischer Parser nötig.
- **Kein Submit**: `form_filler.py` füllt nur aus. Das finale Speichern macht der User. Schützt vor versehentlichen Duplikaten beim Testen.

## Setup-Checkliste (vor erstem Start)

- [ ] Python 3.12 verfügbar (`python --version`)
- [ ] Anthropic API-Key in `.env`
- [ ] `pip install -r requirements.txt`
- [ ] `playwright install chromium`
- [ ] Server: `uvicorn main:app --reload --port 8000`
- [ ] Browser: `http://localhost:8000`

## Definition of Done

Eine Eingabe der Beispiel-URL führt nach Klick auf "Extrahieren" zu vorausgefüllten Feldern im Frontend. Nach Klick auf "In Beanconqueror eintragen" öffnet sich ein Browser-Fenster mit dem Beanconqueror-Formular, in dem alle extrahierten Felder korrekt befüllt sind — bereit zum manuellen Speichern.
