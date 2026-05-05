import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from models import BeanData
from scraper import scrape
from extractor import extract_bean_data
from share_link import build_share_link

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
