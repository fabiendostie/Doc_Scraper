import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from PyQt6.QtCore import QObject, pyqtSignal

class DocScraper(QObject):
    progress_updated = pyqtSignal(int, int)
    status_updated = pyqtSignal(str)
    scraping_completed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    links_discovered = pyqtSignal(list)

    def __init__(self, start_url: str, max_workers: int = 5):
        super().__init__()
        self.start_url = start_url
        self.max_workers = max_workers
        self.base_domain = urlparse(start_url).netloc
        self.visited_links = set()
        self.failed_urls = set()
        self.text_content = []
        self.is_wordpress = False

    def detect_wordpress(self, soup):
        """Detect if the site is WordPress"""
        # Check meta generator tag
        meta = soup.find('meta', {'name': 'generator'})
        if meta and 'wordpress' in meta.get('content', '').lower():
            return True
        
        # Check for wp-content directory in links
        if soup.find('link', href=lambda x: x and 'wp-content' in x.lower()):
            return True
            
        # Check for common WordPress classes
        wp_classes = ['wp-content', 'wordpress', 'wp-block']
        for class_name in wp_classes:
            if soup.find(class_=class_name):
                return True
        
        return False

    def get_wordpress_content(self, soup):
        """Extract content from WordPress pages"""
        content = []
        
        # Get the main content container
        content_area = soup.select_one('div.post-content')
        if not content_area:
            content_area = soup.select_one('.entry-content, article, .wp-block-post-content')
            
        if content_area:
            # Extract and clean up tables
            for table in content_area.find_all('table'):
                # Get headers
                headers = []
                for th in table.find_all('th'):
                    headers.append(th.get_text(strip=True))
                
                # Get rows
                rows = []
                for tr in table.find_all('tr'):
                    cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                    if cells:  # Only add rows with actual data
                        rows.append(cells)
                
                if headers and rows:
                    content.append("\n".join([
                        " | ".join(headers),
                        "-" * (sum(len(h) for h in headers) + (3 * (len(headers) - 1))),
                        *[" | ".join(row) for row in rows]
                    ]))
            
            # Extract headings and paragraphs
            for element in content_area.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                text = element.get_text(strip=True)
                if text:
                    # Add proper formatting for headings
                    if element.name.startswith('h'):
                        level = int(element.name[1])
                        text = f"{'#' * level} {text}"
                    content.append(text)
            
            # Extract lists
            for list_elem in content_area.find_all(['ul', 'ol']):
                for item in list_elem.find_all('li'):
                    text = item.get_text(strip=True)
                    if text:
                        content.append(f"- {text}")
        
        return "\n\n".join(content)

    def discover_links(self):
        """First step: just get all available links"""
        try:
            self.status_updated.emit("Discovering available links...")
            response = requests.get(self.start_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Detect if it's a WordPress site
            self.is_wordpress = self.detect_wordpress(soup)
            self.status_updated.emit(
                f"{'WordPress' if self.is_wordpress else 'Generic'} site detected"
            )
            
            links = self.get_links(self.start_url)
            self.links_discovered.emit(list(links))
            
        except Exception as e:
            self.error_occurred.emit(f"Error discovering links: {str(e)}")

    def get_links(self, url: str) -> set:
        """Extract all valid links from a page"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = set()
            
            # Get all links from the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                parsed_url = urlparse(absolute_url)
                
                # Only include links from the same domain and filter out unwanted paths
                if parsed_url.netloc == self.base_domain:
                    if not any(x in absolute_url.lower() for x in [
                        'wp-admin', 'wp-json', 'wp-includes', 'xmlrpc',
                        'wp-login', 'feed', '?', '#comment', 'replytocom'
                    ]):
                        links.add(absolute_url)
            
            return links
            
        except Exception as e:
            self.error_occurred.emit(f"Error getting links from {url}: {str(e)}")
            return set()

    def process_url(self, url: str) -> dict:
        """Process a single URL and extract its content"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get the title
            title = soup.title.string if soup.title else url
            
            # Get the main content based on site type
            if self.is_wordpress:
                content = self.get_wordpress_content(soup)
            else:
                # Generic content extraction
                main_content = soup.find('main') or soup.find('article') or soup.find('body')
                content = ' '.join(main_content.stripped_strings) if main_content else ''
            
            return {
                'url': url,
                'title': title,
                'content': content
            }
        except Exception as e:
            self.error_occurred.emit(f"Error processing {url}: {str(e)}")
            return None

    def scrape_selected(self, selected_urls):
        """Scrape only the selected URLs"""
        processed_urls = set()
        total_urls = len(selected_urls)

        self.status_updated.emit("Starting scraping process...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.process_url, url): url 
                for url in selected_urls
            }
            
            for future in future_to_url:
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result:
                        self.text_content.append(result)
                    processed_urls.add(url)
                    self.progress_updated.emit(len(processed_urls), total_urls)
                    self.status_updated.emit(f"Processing: {url}")
                except Exception as e:
                    self.error_occurred.emit(f"Error processing {url}: {str(e)}")
                    self.failed_urls.add(url)

        self.scraping_completed.emit(self.text_content)