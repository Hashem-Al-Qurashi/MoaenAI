#!/usr/bin/env python3

# Read the original file
with open('saudi_legal_crawler.py', 'r') as f:
    lines = f.readlines()

# Find the function to replace (around line 364)
new_function = '''    async def discover_document_urls(self, base_url: str = "https://laws.moj.gov.sa") -> List[str]:
        """Discover legal document URLs from MOJ website using real structure"""
        urls = []
        
        logger.info(f"🔍 Starting URL discovery from MOJ legislation pages (7 pages expected)")
        
        # Real MOJ structure: 7 pages of laws
        for page_num in range(1, 8):  # Pages 1-7
            discovery_url = f"{base_url}/ar/legislations-regulations?pageNumber={page_num}&pageSize=9&LegalStatue=1&sortingBy=7"
            
            try:
                logger.info(f"📄 Processing page {page_num}/7: {discovery_url}")
                
                page_urls = await self.extract_urls_from_page(discovery_url)
                urls.extend(page_urls)
                
                logger.info(f"✅ Found {len(page_urls)} law URLs from page {page_num}")
                
                # Respectful delay between pages
                await asyncio.sleep(self.config.request_delay)
                
            except Exception as e:
                logger.error(f"❌ Error discovering URLs from page {page_num}: {e}")
                # Continue with other pages even if one fails
                continue
        
        # Remove duplicates and filter
        unique_urls = list(set(urls))
        filtered_urls = self.filter_legal_urls(unique_urls)
        
        logger.info(f"🎯 Discovery complete: {len(filtered_urls)} Saudi legal documents found")
        self.stats['total_urls_found'] = len(filtered_urls)
        
        return filtered_urls

'''

# Find start and end of function to replace
start_line = None
end_line = None

for i, line in enumerate(lines):
    if 'async def discover_document_urls' in line:
        start_line = i
    elif start_line is not None and line.strip().startswith('async def ') and 'discover_document_urls' not in line:
        end_line = i
        break

if start_line is not None and end_line is not None:
    # Replace the function
    new_lines = lines[:start_line] + [new_function] + lines[end_line:]
    
    # Write the fixed file
    with open('saudi_legal_crawler.py', 'w') as f:
        f.writelines(new_lines)
    
    print(f"✅ Fixed! Replaced lines {start_line+1} to {end_line}")
else:
    print("❌ Could not find function to replace")
