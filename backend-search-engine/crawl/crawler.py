import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import os
from datetime import datetime
import hashlib

class WebCrawler:
    def __init__(self, config_path='../config/config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.setup_logging()
        self.visited_urls = set()
        self.robots_cache = {}
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('../logs/crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def can_fetch(self, url):
        """Check if URL can be fetched according to robots.txt"""
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if base_url not in self.robots_cache:
            robots_url = urljoin(base_url, '/robots.txt')
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                self.robots_cache[base_url] = rp
            except:
                self.robots_cache[base_url] = None
        
        robots_parser = self.robots_cache[base_url]
        if robots_parser:
            return robots_parser.can_fetch(self.config['user_agent'], url)
        return True
    
    def extract_content(self, html, url):
        """Extract relevant content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ''
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc.get('content', '') if meta_desc else ''
        
        # Extract headings
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            headings.append(h.get_text().strip())
        
        # Extract body text
        body = soup.find('body')
        if body:
            body_text = body.get_text()
        else:
            body_text = soup.get_text()
        
        # Clean up body text
        lines = (line.strip() for line in body_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        body_text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(url, link['href'])
            links.append(absolute_url)
        
        return {
            'url': url,
            'title': title_text,
            'body': body_text[:5000],  # Limit body text
            'headings': headings,
            'meta_description': meta_description,
            'links': links,
            'crawl_date': datetime.now().isoformat(),
            'id': hashlib.md5(url.encode()).hexdigest()
        }
    
    def crawl_url(self, url):
        """Crawl a single URL"""
        if url in self.visited_urls:
            return None
        
        if not self.can_fetch(url):
            self.logger.info(f"Robots.txt disallows crawling: {url}")
            return None
        
        try:
            headers = {
                'User-Agent': self.config['user_agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            if 'text/html' not in response.headers.get('content-type', ''):
                return None
            
            self.visited_urls.add(url)
            content = self.extract_content(response.text, url)
            
            self.logger.info(f"Successfully crawled: {url}")
            return content
            
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")
            return None
    
    def crawl_site(self, start_urls, max_pages=100):
        """Crawl multiple URLs"""
        crawled_data = []
        urls_to_crawl = list(start_urls)
        crawled_count = 0
        
        while urls_to_crawl and crawled_count < max_pages:
            url = urls_to_crawl.pop(0)
            
            content = self.crawl_url(url)
            if content:
                crawled_data.append(content)
                crawled_count += 1
                
                # Add internal links to crawl queue
                if self.config.get('follow_internal_links', False):
                    for link in content['links']:
                        parsed_link = urlparse(link)
                        parsed_start = urlparse(url)
                        
                        if (parsed_link.netloc == parsed_start.netloc and 
                            link not in self.visited_urls and 
                            link not in urls_to_crawl):
                            urls_to_crawl.append(link)
            
            # Respect crawl delay
            time.sleep(self.config.get('crawl_delay', 1))
        
        return crawled_data
    
    def save_data(self, data, filename=None):
        """Save crawled data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../data/crawled_data_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(data)} documents to {filename}")
        return filename

if __name__ == "__main__":
    crawler = WebCrawler()
    
    # Example usage
    start_urls = [
        "https://www.bbc.com/news/world",
        "https://www.theguardian.com/world"
    ]
    
    crawled_data = crawler.crawl_site(start_urls, max_pages=150)
    crawler.save_data(crawled_data)




