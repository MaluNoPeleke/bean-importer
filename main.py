import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from models import BeanData
from scraper import scrape
from extractor import extract_bean_data, probe_llm
from share_link import build_share_link
from settings import PROVIDERS, read_settings, write_settings

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="BeanImporter")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


class ExtractRequest(BaseModel):
    url: str


class SettingsRequest(BaseModel):
    provider: str
    model: str
    api_key: str | None = None


@app.get("/")
async def index():
    return FileResponse("index.html")


@app.post("/extract")
async def extract(req: ExtractRequest):
    html = await scrape(req.url)
    bean = await extract_bean_data(html, req.url)
    return bean.model_dump()


@app.post("/fill")
async def fill(bean: BeanData):
    link = build_share_link(bean)
    return {"status": "done", "name": bean.coffee_name, "link": link}


@app.get("/settings")
async def get_settings():
    return read_settings()


@app.post("/settings")
async def update_settings(req: SettingsRequest):
    from fastapi import HTTPException
    try:
        # Reject the .env.example placeholder — /settings/test rejects it too,
        # so they must agree to avoid storing a key that probes will then refuse.
        if req.api_key and "YOUR_KEY_HERE" in req.api_key:
            raise HTTPException(status_code=400, detail="Platzhalter-Key ist nicht gültig. Bitte echten API-Key eingeben.")
        # Allow saving without a key (model-only change) only if a key already exists.
        current = read_settings()
        if not req.api_key and not (current["provider"] == req.provider and current["has_key"]):
            raise HTTPException(status_code=400, detail="API-Key erforderlich beim ersten Speichern dieses Providers.")
        write_settings(req.provider, req.model, req.api_key or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, **read_settings()}


@app.post("/settings/test")
async def test_settings(req: SettingsRequest):
    from fastapi import HTTPException
    if req.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unbekannter Provider: {req.provider}")
    if req.model not in PROVIDERS[req.provider]["models"]:
        raise HTTPException(status_code=400, detail="Modell passt nicht zum Provider.")

    key = req.api_key
    if not key:
        # Fall back to the stored key, so the user can re-test without re-entering it.
        import os
        key = os.environ.get(PROVIDERS[req.provider]["key_env"], "")
    if not key or "YOUR_KEY_HERE" in key:
        raise HTTPException(status_code=400, detail="Kein API-Key vorhanden zum Testen.")

    ok, message = await probe_llm(req.model, key, PROVIDERS[req.provider]["key_env"])
    return {"ok": ok, "message": message}
