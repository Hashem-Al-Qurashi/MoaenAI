import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from smart_legal_chunker import SmartLegalChunker

async def test_real_massive():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    page = await browser.new_page()
    
    # Test with the real massive document we found
    url = "https://laws.moj.gov.sa/ar/legislation/3PpcH7Pox63dH0Jw82s-UA"
    title = "اللوائح التنفيذية لنظام المرافعات الشرعية"
    
    print(f"🔍 Testing massive document: {title}")
    print(f"🌐 URL: {url}")
    
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(5000)
    
    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        element.decompose()
    
    # Get main content
    main = soup.select_one('main')
    content = main.get_text(strip=True)
    
    print(f"📏 Content: {len(content):,} characters")
    print(f"🔢 Estimated tokens: {len(content) // 2:,}")
    print(f"📖 Preview: {content[:200]}...")
    print()
    
    # Test the smart chunker
    print("🧪 Testing Smart Legal Chunker...")
    chunker = SmartLegalChunker(max_tokens_per_chunk=6000)
    chunks = chunker.chunk_legal_document(content, title)
    
    print(f"✂️ Created {len(chunks)} chunks:")
    print()
    
    total_chars = 0
    for i, chunk in enumerate(chunks):
        total_chars += len(chunk.content)
        tokens = chunker.estimate_tokens(chunk.content)
        status = "✅" if tokens <= 6000 else "❌"
        
        print(f"{status} Chunk {i+1}: {chunk.title}")
        print(f"   📏 {len(chunk.content):,} chars (~{tokens:,} tokens)")
        print(f"   📝 Level: {chunk.hierarchy_level}")
        print(f"   🔗 Metadata: {chunk.metadata}")
        print(f"   📖 Preview: {chunk.content[:100].replace(chr(10), ' ')}...")
        print()
    
    # Summary
    oversized = [c for c in chunks if chunker.estimate_tokens(c.content) > 6000]
    print("📊 SUMMARY:")
    print(f"   📄 Original: {len(content):,} chars (~{len(content)//2:,} tokens)")
    print(f"   ✂️ Chunks: {len(chunks)}")
    print(f"   📏 Total chunked: {total_chars:,} chars")
    print(f"   ✅ Under limit: {len(chunks) - len(oversized)}")
    print(f"   ❌ Still too big: {len(oversized)}")
    
    if len(oversized) == 0:
        print(f"🎉 SUCCESS! All chunks are under 6000 token limit!")
        print(f"🚀 Ready to store in database!")
    else:
        print(f"⚠️ Need to improve chunking for {len(oversized)} chunks")
    
    await browser.close()
    await pw.stop()

asyncio.run(test_real_massive())
