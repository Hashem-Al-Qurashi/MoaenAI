import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from smart_legal_chunker import SmartLegalChunker

async def test_massive_document():
    # Let's test with نظام المعاملات المدنية (Civil Transactions Law)
    # This was the biggest one with 140,345 tokens!
    
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    page = await browser.new_page()
    
    # Find the URL for نظام المعاملات المدنية from our discovered URLs
    # We need to search through the 62 URLs we found
    
    # Let's use one we know failed with large tokens
    test_urls = [
        "https://laws.moj.gov.sa/ar/legislation/aAfeitJIgUcjbCD_KwTSSw",  # Try this one
        "https://laws.moj.gov.sa/ar/legislation/myVO-TMtIwgPSdkK_pOfJw",  # Or this one
        "https://laws.moj.gov.sa/ar/legislation/HhAP0DcfNk8sKHJPtNg1dQ"   # Or this one
    ]
    
    for url in test_urls:
        print(f"\n🔍 Testing URL: {url}")
        
        try:
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(5000)
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Get title
            title_element = soup.find('title')
            title = title_element.get_text(strip=True) if title_element else "Test Document"
            title = title.replace(' - وزارة العدل', '').strip()
            
            # Get main content
            main = soup.select_one('main')
            if main:
                content = main.get_text(strip=True)
                
                print(f"📋 Title: {title}")
                print(f"📏 Content length: {len(content):,} characters")
                print(f"🔢 Estimated tokens: {len(content) // 2:,}")
                
                if len(content) > 20000:  # If it's a big document
                    print(f"\n🧪 Testing smart chunker...")
                    
                    # Test the chunker
                    chunker = SmartLegalChunker(max_tokens_per_chunk=6000)
                    chunks = chunker.chunk_legal_document(content, title)
                    
                    print(f"✂️ Created {len(chunks)} chunks:")
                    for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
                        print(f"   {i+1}. {chunk.title}")
                        print(f"      📏 {len(chunk.content):,} chars (~{chunker.estimate_tokens(chunk.content):,} tokens)")
                        print(f"      📝 Level: {chunk.hierarchy_level}")
                        print(f"      🔗 Metadata: {chunk.metadata}")
                        print(f"      📖 Preview: {chunk.content[:100]}...")
                        print()
                    
                    if len(chunks) > 5:
                        print(f"   ... and {len(chunks) - 5} more chunks")
                    
                    # Test if all chunks are under token limit
                    oversized = [c for c in chunks if chunker.estimate_tokens(c.content) > 6000]
                    if oversized:
                        print(f"⚠️ {len(oversized)} chunks still too large!")
                    else:
                        print(f"✅ All chunks are under 6000 token limit!")
                    
                    break  # Found a good test document
                else:
                    print(f"📏 Document too small for chunking test")
            else:
                print("❌ No main content found")
                
        except Exception as e:
            print(f"❌ Error testing {url}: {e}")
    
    await browser.close()
    await pw.stop()

asyncio.run(test_massive_document())
