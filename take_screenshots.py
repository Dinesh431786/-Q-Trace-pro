import asyncio
from playwright.async_api import async_playwright
import os

async def take_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # Navigate to the app
        url = "https://8000-im3ym1a120q52e0lmqyzv-18e660f9.sandbox.novita.ai"
        print(f"Loading {url}...")
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Take main dashboard screenshot
        print("Taking dashboard screenshot...")
        await page.screenshot(path='screenshots/dashboard.png', full_page=False)
        
        # Click analyze button to show analysis
        print("Running analysis...")
        await page.click('#analyzeBtn')
        await asyncio.sleep(3)
        
        # Take screenshot with results
        print("Taking results screenshot...")
        await page.screenshot(path='screenshots/analysis_results.png', full_page=False)
        
        # Scroll to features section
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)
        
        # Take features screenshot  
        print("Taking features screenshot...")
        await page.screenshot(path='screenshots/features.png', full_page=False)
        
        # Take full page screenshot
        print("Taking full page screenshot...")
        await page.screenshot(path='screenshots/full_page.png', full_page=True)
        
        await browser.close()
        print("Screenshots saved in screenshots/ directory")

# Create screenshots directory
os.makedirs('screenshots', exist_ok=True)

# Run the screenshot capture
asyncio.run(take_screenshots())