import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def find_massive_document():
    # Test multiple URLs to find the massive ones
    test_urls = [
        "https://laws.moj.gov.sa/ar/legislation/3PpcH7Pox63dH0Jw82s-UA",  # We know this one had 97K chars
        "https://laws.moj.gov.sa/ar/legislation/GE-StIXcjF_Wfc2MFGx8ww",
        "https://laws.moj.gov.sa/ar/legislation/XxHJGQ-J8UHQHL_lpdKCVw",
        "https://laws.moj.gov.sa/ar/legislation/ZNMI0PpA1fSRgK60lVLGEw",
        "https://laws.moj.gov.sa/ar/legislation/zhNDy4NzpQqEM5bW2AEjLg"
    ]
    
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    page = await browser.new_page()
    
    for url in test_urls:
        print(f"\n🔍 Testing: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(5000)
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Get title
            title_element = soup.find('title')
            title = title_element.get_text(strip=True) if title_element else "Unknown"
            title = title.replace(' - وزارة العدل', '').strip()
            
            # Check raw content before removing elements
            raw_content = soup.get_text(strip=True)
            print(f"📋 Title: {title}")
            print(f"📏 Raw content: {len(raw_content):,} characters")
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Get main content
            main = soup.select_one('main')
            if main:
                main_content = main.get_text(strip=True)
                print(f"📏 Main content: {len(main_content):,} characters")
                print(f"🔢 Estimated tokens: {len(main_content) // 2:,}")
                
                if len(main_content) > 50000:  # If we find a massive one
                    print(f"🎯 FOUND MASSIVE DOCUMENT!")
                    print(f"📖 Preview: {main_content[:200]}...")
                    break
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await browser.close()
    await pw.stop()

asyncio.run(find_massive_document())
