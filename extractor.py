import json
import logging
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from models import BeanData
from researcher import research_coffee

load_dotenv(Path(__file__).parent / ".env", override=True)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """\
Du bist ein Kaffee-Experte und Datenextraktions-Spezialist. \
Deine Aufgabe: Aus einer Kaffeeshop-Produktseite UND Web-Recherche-Ergebnissen \
Daten für das Beanconqueror-Formular extrahieren.

Du erhältst:
1. Das HTML der Produktseite
2. Zusätzliche Web-Recherche-Ergebnisse

Antworte ausschließlich mit einem JSON-Objekt gemäß folgendem Schema:

{
  "coffee_name": "string (Produktname, Pflichtfeld)",
  "roaster": "string | null (wer die Bohnen röstet)",
  "roasting_date": "string | null (ISO-Datum YYYY-MM-DD)",
  "website": "string | null (URL der Produktseite)",

  "bean_roasting_type": "string | null (exakt einer: 'FILTER', 'ESPRESSO', 'OMNI')",
  "roast": "string | null (exakt einer der Enum-Werte, siehe Liste unten)",
  "roast_custom": "string | null (Freitext, NUR wenn roast = 'CUSTOM_ROAST')",
  "degree_of_roast": "float | null (Skala 0.0 bis 5.0, Schritte 0.1)",
  "bean_mix": "string | null (exakt: 'SINGLE_ORIGIN' oder 'BLEND')",

  "weight": "int | null (Gramm)",
  "cost": "float | null (Preis in Euro)",
  "ean_article": "string | null (EAN/Artikelnummer)",
  "flavour_profile": "string | null (Geschmacksnoten, kommasepariert)",
  "cupping_points": "string | null (z.B. '87.5')",
  "decaffeinated": "bool (default: false)",

  "varieties": [
    {
      "country": "string | null (Herkunftsland)",
      "region": "string | null (Anbauregion)",
      "farm": "string | null (Farm/Finca)",
      "farmer": "string | null (Produzent/Farmer)",
      "variety": "string | null (botanische Varietät, z.B. 'Catuai', mehrere kommasepariert)",
      "processing": "string | null (Natural, Washed, Honey, etc.)",
      "elevation": "string | null (z.B. '1.250 m')",
      "harvest_time": "string | null (Erntezeit)",
      "certification": "string | null (Bio, Fairtrade, etc.)",
      "percentage": "int | null (Anteil in %, bei Single Origin: 100)"
    }
  ],

  "notes": "string | null (Brührezept + weitere Infos)"
}

ERLAUBTE WERTE für "roast" (Röstgrad):
  CINNAMON_ROAST (Light), AMERICAN_ROAST (Light), NEW_ENGLAND_ROAST (Light),
  HALF_CITY_ROAST (Light), MODERATE_LIGHT_ROAST,
  CITY_ROAST (Medium), CITY_PLUS_ROAST (Medium), FULL_CITY_ROAST (Medium),
  FULL_CITY_PLUS_ROAST (Dark), ITALIAN_ROAST (Dark), VIEANNA_ROAST (Dark),
  FRENCH_ROAST (Dark), CUSTOM_ROAST (+ roast_custom Freitext)

REGELN:

1. GESCHMACKSPROFIL: Extrahiere ALLE genannten Aromen und Geschmacksnoten ausführlich. \
   Wenn auf der Seite nur ein Oberbegriff steht (z.B. "Schokolade"), ergänze aus deinem \
   Kaffeewissen passende Unternoten basierend auf Herkunft, Varietät und Aufbereitung \
   (z.B. "Zartbitterschokolade, Kakao, Nougat, schwere Süße").

2. NOTES: Formuliere ein Espresso-Baseline-Rezept im Format:
   "Baseline: [X]g In / [Y]g Out. Temp: [Z]°C. Target: [T]s. [Zusätzliche Infos]"
   - Nutze Rezeptdaten vom Röster falls in der Web-Recherche gefunden.
   - Falls KEINE spezifischen Brühdaten verfügbar, wähle Defaults nach Röstprofil:
     * Espresso/dunkle Röstung: 18g In / 36g Out, 91°C, 28s
     * Filter/helle Röstung: 18g In / 40g Out, 94°C, 30s
     * Medium: 18g In / 36g Out, 93°C, 27s
   - Hänge weitere relevante Infos an: Eignung (Flat White, Cappuccino, Pur), \
     Auszeichnungen, Besonderheiten.

3. RÖSTGRAD: degree_of_roast ist 0.0–5.0 (NICHT 0–100!). Orientierung:
   - Light (Cinnamon–Half City): 0.5–1.5
   - Medium (City–Full City): 2.0–3.0
   - Dark (Full City+–French): 3.5–5.0

4. VARIETÄTEN: Alle verfügbaren Felder befüllen. \
   farm = Name der Farm/Finca, farmer = Produzent (z.B. "Volcafe"). \
   Bei Single Origin: percentage = 100. \
   Region so spezifisch wie möglich (aus Weltwissen ergänzen, wenn der Bohnenname \
   oder die Beschreibung Hinweise gibt).

5. bean_mix: "BLEND" wenn als Blend, Mischung oder Regional Blend beschrieben. \
   Auch Kategorie "Regional" = BLEND.

6. Felder ohne Angabe: null setzen.
7. Keine Markdown-Fences, nur pures JSON.
8. Gewicht immer in Gramm (250g → 250, 1kg → 1000).
9. cost als float in Euro.
"""


async def extract_bean_data(html: str, url: str) -> BeanData:
    product_hint = _extract_product_hint(html, url)
    research_context = await research_coffee(
        product_hint["name"], product_hint.get("shop_domain")
    )

    user_prompt = (
        f"Produktseite URL: {url}\n\n"
        f"=== PRODUKTSEITE HTML ===\n{html}\n\n"
        f"=== WEB-RECHERCHE ERGEBNISSE ===\n{research_context}\n"
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    logger.info("Claude raw response length: %d chars", len(raw))

    try:
        data = json.loads(raw)
        return BeanData(**data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("First attempt failed (%s), retrying with feedback", e)
        return await _retry_with_feedback(user_prompt, raw, str(e))


def _extract_product_hint(html: str, url: str) -> dict:
    import re
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse, unquote

    soup = BeautifulSoup(html, "lxml")

    name = ""
    for selector in ["h1.product_title", "h1", ".product-title", "[itemprop='name']"]:
        el = soup.select_one(selector)
        if el and el.get_text(strip=True):
            name = el.get_text(strip=True)
            break

    if not name:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            name = og["content"].strip()

    if not name:
        title = soup.find("title")
        if title and title.get_text(strip=True):
            name = title.get_text(strip=True).split("|")[0].split("–")[0].split("-")[0].strip()

    if not name:
        path = urlparse(url).path
        segments = [s for s in path.split("/") if s and s not in ("product", "products", "collections", "shop")]
        if segments:
            slug = segments[-1]
            slug = re.split(r"\?", slug)[0]
            name = unquote(slug).replace("-", " ").replace("_", " ").strip().title()

    shop_domain = urlparse(url).hostname or ""
    shop_domain = shop_domain.replace("www.", "")

    logger.info("Product hint: name='%s', shop='%s'", name, shop_domain)
    return {"name": name, "shop_domain": shop_domain}


async def _retry_with_feedback(original_prompt: str, previous_response: str, error: str) -> BeanData:
    retry_prompt = (
        f"Dein vorheriger Versuch hat einen Fehler verursacht:\n"
        f"Response: {previous_response[:500]}\n"
        f"Fehler: {error}\n\n"
        f"Bitte korrigiere und antworte erneut mit validem JSON.\n\n"
        f"{original_prompt}"
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": retry_prompt}],
    )

    raw = response.content[0].text.strip()
    data = json.loads(raw)
    return BeanData(**data)
