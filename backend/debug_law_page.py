import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def debug_law_page():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)  # Show browser
    page = await browser.new_page()
    
    # Load one of the failing URLs
    url = "https://laws.moj.gov.sa/ar/legislation/3PpcH7Pox63dH0Jw82s-UA"
    print(f"Loading: {url}")
    
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(3000)  # Wait 3 seconds
    
    # Get the page content
    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove scripts and styles
    for element in soup(['script', 'style']):
        element.decompose()
    
    # Get all text and see what we have
    all_text = soup.get_text(strip=True)
    print(f"Total text length: {len(all_text)}")
    print(f"First 500 chars: {all_text[:500]}")
    
    # Look for any divs with substantial text
    print("\n--- Checking divs with text ---")
    for div in soup.find_all('div'):
        text = div.get_text(strip=True)
        if len(text) > 100:
            print(f"Div with {len(text)} chars: {text[:100]}...")
            break
    
    # Check for common content containers
    print("\n--- Checking common selectors ---")
    selectors = ['main', 'article', '.content', '.main-content', '#content', '.law-content']
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            print(f"{selector}: {len(text)} chars")
            if len(text) > 50:
                print(f"  Sample: {text[:100]}...")
    
    await browser.close()
    await pw.stop()

asyncio.run(debug_law_page())
