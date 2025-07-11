import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def test_actual_url():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    page = await browser.new_page()
    
    # Test the URL that's actually failing
    url = "https://laws.moj.gov.sa/ar/legislation/Lw717agoWszH5smTAcoEBg"
    print(f"Testing actual failing URL: {url}")
    
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(5000)  # Wait 5 seconds
    
    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove scripts and styles
    for element in soup(['script', 'style']):
        element.decompose()
    
    all_text = soup.get_text(strip=True)
    print(f"Total text: {len(all_text)} chars")
    print(f"Content preview: {all_text[:200]}")
    
    # Check what's in the main element
    main = soup.select_one('main')
    if main:
        main_text = main.get_text(strip=True)
        print(f"Main element: {len(main_text)} chars")
        print(f"Main preview: {main_text[:100]}")
    
    await browser.close()
    await pw.stop()

asyncio.run(test_actual_url())
