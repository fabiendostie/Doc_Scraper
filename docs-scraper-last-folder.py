import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
from urllib.parse import urljoin, urlparse
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Set, Dict, List, Optional
import logging
from pathlib import Path
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DocScraper:
    def __init__(self, start_url: str, max_workers: int = 5):
        self.start_url = start_url
        self.base_url = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"
        self.start_path = urlparse(start_url).path
        self.visited_links: Set[str] = set()
        self.text_content: List[Dict[str, str]] = []
        self.session = requests.Session()
        self.max_workers = max_workers
        self.failed_urls: Set[str] = set()

    def get_page_content(self, url: str) -> Optional[str]:
        """Fetch page content with retry logic and timeout."""
        retries = 3
        timeout = 10
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == retries - 1:
                    logging.error(f"Failed to fetch {url} after {retries} attempts: {e}")
                    self.failed_urls.add(url)
                    return None
                time.sleep(1)  # Wait before retry
        return None

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace and normalize line endings
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text.strip())
        # Remove special characters but keep basic punctuation and common symbols
        text = re.sub(r'[^\w\s.,!?;:()\-–—\'"\[\]{}]', ' ', text)
        return text

    def extract_text(self, soup: BeautifulSoup) -> str:
        """Extract and clean text content from BeautifulSoup object."""
        # Remove unwanted elements
        unwanted_tags = [
            "script", "style", "header", "footer", "nav",
            "meta", "link", "noscript", "iframe"
        ]
        for tag in soup.find_all(unwanted_tags):
            tag.decompose()

        # Extract text from specific content areas
        content_areas = soup.find_all(["article", "main", "div.content", "section"])
        if content_areas:
            text = "\n\n".join(area.get_text(separator='\n', strip=True) 
                              for area in content_areas)
        else:
            text = soup.get_text(separator='\n', strip=True)
            
        return self.clean_text(text)

    def get_links(self, url: str) -> Set[str]:
        """Extract relevant links from the page."""
        html_content = self.get_page_content(url)
        if not html_content:
            return set()
        
        soup = BeautifulSoup(html_content, "html.parser")
        links = set()
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            
            # Skip irrelevant links
            if (href.startswith(('#', 'mailto:')) or 
                any(ext in href for ext in ['.pdf', '.zip', '.png', '.jpg'])):
                continue
                
            full_url = urljoin(url, href)
            parsed_url = urlparse(full_url)
            
            # Only include links from the same directory as the starting URL
            if (parsed_url.netloc == urlparse(self.base_url).netloc and 
                parsed_url.path.startswith(self.start_path.rsplit('/', 1)[0])):
                links.add(full_url)
                
        return links

    def process_url(self, url: str) -> Optional[Dict[str, str]]:
        """Process a single URL and return its content."""
        if url in self.visited_links:
            return None
            
        html_content = self.get_page_content(url)
        if not html_content:
            return None
            
        soup = BeautifulSoup(html_content, "html.parser")
        text = self.extract_text(soup)
        
        if not text:
            return None
            
        title = soup.title.string if soup.title else url
        self.visited_links.add(url)
        
        return {
            'title': title,
            'url': url,
            'content': text
        }

    def scrape(self):
        """Scrape content using thread pool for parallel processing."""
        queue = {self.start_url}
        processed_urls = set()

        with tqdm(desc="Scraping pages") as pbar:
            while queue:
                current_batch = list(queue)
                queue.clear()

                # Process URLs in parallel
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_url = {
                        executor.submit(self.process_url, url): url 
                        for url in current_batch 
                        if url not in processed_urls
                    }
                    
                    for future in future_to_url:
                        url = future_to_url[future]
                        try:
                            result = future.result()
                            if result:
                                self.text_content.append(result)
                                # Get new links
                                new_links = self.get_links(url)
                                queue.update(new_links - self.visited_links)
                            processed_urls.add(url)
                            pbar.update(1)
                        except Exception as e:
                            logging.error(f"Error processing {url}: {e}")
                            self.failed_urls.add(url)

    def save_to_txt(self, output_file: str):
        """Save scraped content to a text file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in self.text_content:
                    f.write(f"Title: {item['title']}\n")
                    f.write(f"URL: {item['url']}\n\n")
                    f.write(item['content'])
                    f.write("\n\n" + "=" * 80 + "\n\n")
        except Exception as e:
            logging.error(f"Error saving text file: {e}")

def main():
    # Create output directory if it doesn't exist
    Path("output").mkdir(exist_ok=True)
    
    start_url = "https://beets.readthedocs.io/en/stable/guides/index.html"
    scraper = DocScraper(start_url)
    
    start_time = time.time()
    scraper.scrape()
    
    # Generate file names based on the scraped URL
    base_name = urlparse(start_url).path.strip("/").replace("/", "_")
    txt_file = f"output/{base_name}_documentation.txt"
    json_file = f"output/{base_name}_raw_content.json"
    
    # Save content
    scraper.save_to_txt(txt_file)
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(scraper.text_content, f, ensure_ascii=False, indent=2)
        
    # Log summary
    elapsed_time = time.time() - start_time
    logging.info(f"Scraping completed in {elapsed_time:.2f} seconds")
    logging.info(f"Total pages scraped: {len(scraper.text_content)}")
    logging.info(f"Failed URLs: {len(scraper.failed_urls)}")
    
    if scraper.failed_urls:
        with open('output/failed_urls.txt', 'w') as f:
            f.write('\n'.join(scraper.failed_urls))

if __name__ == "__main__":
    main()
