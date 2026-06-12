import urllib.request   
import urllib.parse
import time
import queue
import threading
import os
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

# --- CONFIGURATION & INPUT ---
# Checks for GitHub Action environment variables first, falls back to manual input/defaults locally
start_url = os.environ.get("START_URL") or input("Enter the starting URL to crawl: ")
start_url = start_url.strip()

# Automatically prepends https:// if you forget to type it
if not start_url.startswith(('http://', 'https://')):
    start_url = 'https://' + start_url

# Configurable via environment variables for GitHub Actions flexibility, with local fallbacks
DELAY = int(os.environ.get("CRAWL_DELAY", 5))        # Delay (in seconds) per thread after completing a page
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 2))  # Number of pages to scan simultaneously

# Extract base domain to keep the crawler from wandering off-site
base_domain = urllib.parse.urlparse(start_url).netloc

# Clean up domain name for a safe filename (e.g., removing port colons if testing locally)
safe_filename = base_domain.replace(':', '_') if base_domain else "crawled_links"
filename = f"{safe_filename}.txt"

# Thread-safe Trackers
urls_to_crawl = queue.Queue()
urls_to_crawl.put(start_url)

visited_urls = set()
recorded_links = set()
queued_urls = {start_url}  # Prevents workers from adding duplicates to the queue

# Synchronizing primitives for thread safety
lock = threading.Lock()
shutdown_event = threading.Event()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

print(f"\n🚀 Starting multi-threaded web crawl on: {start_url}")
print(f"⚙️ Configured Delay: {DELAY}s | Max Workers: {MAX_WORKERS}")
print(f"📁 Writing clean links to '{filename}'...")
print("🛑 Press Ctrl+C in your command prompt at any time to stop manually.\n")

def worker(file_handle):
    while not shutdown_event.is_set():
        try:
            # Grab a URL from the queue (times out after 1 second if queue is temporarily empty)
            current_url = urls_to_crawl.get(timeout=1)
        except queue.Empty:
            continue
            
        # Safely check and mark URL as visited
        with lock:
            if current_url in visited_urls:
                urls_to_crawl.task_done()
                continue
            visited_urls.add(current_url)
            
        print(f"--- SCANNING: {current_url} ---")
        
        try:
            req = urllib.request.Request(current_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                content_type = resp.info().get_content_type()
                
                # Only parse HTML pages (prevents BeautifulSoup from crashing on images/videos)
                if 'text/html' not in content_type:
                    urls_to_crawl.task_done()
                    continue
                    
                charset = resp.info().get_param('charset') or 'utf-8'
                soup = BeautifulSoup(resp, 'html.parser', from_encoding=charset)
                
                # Gather everything with an href or src attribute
                raw_links = []
                for tag in soup.find_all(href=True):
                    raw_links.append(tag.get('href'))
                for tag in soup.find_all(src=True):
                    raw_links.append(tag.get('src'))
                
                for link in raw_links:
                    if not link:
                        continue
                    
                    # Clean up link structure
                    absolute_link = urllib.parse.urljoin(current_url, link)
                    absolute_link, _ = urllib.parse.urldefrag(absolute_link)
                    
                    # Log and write unique links safely using the thread lock
                    with lock:
                        if absolute_link not in recorded_links:
                            recorded_links.add(absolute_link)
                            print(absolute_link)
                            file_handle.write(absolute_link + "\n")
                            file_handle.flush()
                    
                    # Queue all internal links safely without filtering extensions
                    link_domain = urllib.parse.urlparse(absolute_link).netloc
                    if link_domain == base_domain:
                        with lock:
                            if absolute_link not in visited_urls and absolute_link not in queued_urls:
                                queued_urls.add(absolute_link)
                                urls_to_crawl.put(absolute_link)
                                
        except Exception as e:
            print(f"⚠️ Error reading {current_url}: {e}")
        
        urls_to_crawl.task_done()
        time.sleep(DELAY)

try:
    with open(filename, "w", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Dispatch the worker threads
            for _ in range(MAX_WORKERS):
                executor.submit(worker, f)
            
            # Wait until everything in the queue has been fully processed
            urls_to_crawl.join()
            
            # Signal threads to exit
            shutdown_event.set()

    print(f"\n🏁 Crawl complete! Check '{filename}' for your results.")

except KeyboardInterrupt:
    print("\n👋 Crawl interrupted by user. Wrapping up threads and saving progress.")
    shutdown_event.set()
