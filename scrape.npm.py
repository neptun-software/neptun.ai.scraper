import os
import json
import asyncio
import time
from datetime import datetime, timezone
import re
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Ensure it is set in the .env file.")

# Set the OpenAI API key for ChatGPT
client = OpenAI(api_key=api_key)

# Define data directories
DATA_DIR = "data"
RAW_HTML_DIR = os.path.join(DATA_DIR, "raw_html/docs.npmjs.com")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed/docs.npmjs.com")
STATS_FILE = os.path.join(DATA_DIR, "processed/docs.npmjs.com/stats.json")

# Create necessary directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RAW_HTML_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def save_raw_html(url, html_content):
    """Save raw HTML content to file."""
    filename = re.sub(r'[^\w\-_.]', '_', url.split('//')[1]) + '.html'
    filepath = os.path.join(RAW_HTML_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return filepath

def update_stats(url, fetch_time, store_time, success, error=None, jsonl_entries=0):
    """Update the statistics file with new data."""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
                
                # Skip if it's the first run with example data
                if len(stats["scraping_stats"]["pages"]) == 1 and stats["scraping_stats"]["pages"][0]["url"] == "https://example.com/package/test":
                    stats["scraping_stats"]["pages"] = []
                    stats["scraping_stats"]["total_pages_processed"] = 0
                    stats["scraping_stats"]["total_success"] = 0
                    stats["scraping_stats"]["total_failures"] = 0
                    stats["scraping_stats"]["average_fetch_time_ms"] = 0
                    stats["scraping_stats"]["average_store_time_ms"] = 0
                    stats["scraping_stats"]["total_jsonl_entries"] = 0
                    stats["scraping_stats"]["average_entries_per_page"] = 0
        else:
            stats = {
                "scraping_stats": {
                    "total_pages_processed": 0,
                    "total_success": 0,
                    "total_failures": 0,
                    "average_fetch_time_ms": 0,
                    "average_store_time_ms": 0,
                    "total_jsonl_entries": 0,
                    "average_entries_per_page": 0,
                    "pages": []
                }
            }
        
        # Update counters
        stats["scraping_stats"]["total_pages_processed"] += 1
        if success:
            stats["scraping_stats"]["total_success"] += 1
            stats["scraping_stats"]["total_jsonl_entries"] += jsonl_entries
        else:
            stats["scraping_stats"]["total_failures"] += 1
        
        # Calculate new averages
        total_pages = len(stats["scraping_stats"]["pages"])
        if total_pages > 0:
            current_fetch_avg = stats["scraping_stats"]["average_fetch_time_ms"]
            current_store_avg = stats["scraping_stats"]["average_store_time_ms"]
            stats["scraping_stats"]["average_fetch_time_ms"] = (current_fetch_avg * total_pages + fetch_time) / (total_pages + 1)
            stats["scraping_stats"]["average_store_time_ms"] = (current_store_avg * total_pages + store_time) / (total_pages + 1)
            if success:
                stats["scraping_stats"]["average_entries_per_page"] = stats["scraping_stats"]["total_jsonl_entries"] / stats["scraping_stats"]["total_success"]
        else:
            stats["scraping_stats"]["average_fetch_time_ms"] = fetch_time
            stats["scraping_stats"]["average_store_time_ms"] = store_time
            if success:
                stats["scraping_stats"]["average_entries_per_page"] = jsonl_entries
        
        # Add new page entry
        page_entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            "url": url,
            "fetch_time_ms": fetch_time,
            "store_time_ms": store_time,
            "total_time_ms": fetch_time + store_time,
            "success": success,
            "error": str(error) if error else None,
            "jsonl_entries": jsonl_entries
        }
        stats["scraping_stats"]["pages"].append(page_entry)
        
        # Save updated stats
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Updated stats for {url} - Total pages: {stats['scraping_stats']['total_pages_processed']}, "
              f"Success: {stats['scraping_stats']['total_success']}, "
              f"Failures: {stats['scraping_stats']['total_failures']}, "
              f"Total JSONL entries: {stats['scraping_stats']['total_jsonl_entries']}, "
              f"Avg entries/page: {stats['scraping_stats']['average_entries_per_page']:.1f}")
    
    except Exception as e:
        print(f"Error updating stats: {e}")

def filter_relevant_links(links, base_url="https://docs.npmjs.com"):
    """Filter links to include only those that belong to the given base URL."""
    relevant_links = [link for link in links if link.startswith(base_url)]
    return relevant_links

def extract_links(html_content):
    """Extract all relevant links from the provided HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        # Only keep relevant links (absolute or relative URLs starting with "/")
        if href.startswith("http") or href.startswith("/"):
            links.append(href if href.startswith("http") else f"https://docs.npmjs.com{href}")
    return list(set(links))  # Remove duplicates

async def fetch_content(url):
    """Fetch content from the given URL using AsyncWebCrawler."""
    fetch_start = time.time()
    try:
        print(f"\nStarting fetch for URL: {url}")
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=url,
                extraction_strategy=LLMExtractionStrategy(
                    provider="openai/gpt-4o",
                    api_token=api_key,
                    instruction="Extract the most relevant content about npm commands, features, and documentation.",
                ),
                bypass_cache=True,
            )
        fetch_time = (time.time() - fetch_start) * 1000  # Convert to milliseconds
        print(f"Fetch completed in {fetch_time:.2f}ms - URL: {url}")
        
        # Start measuring store time for all storage operations
        store_start = time.time()
        
        # Save raw HTML
        html_filepath = save_raw_html(url, result.html)
        print(f"Saved raw HTML to: {html_filepath}")
        
        # Process and save JSON content
        extracted_content = json.loads(result.extracted_content)
        print(f"Successfully extracted content with {len(extracted_content)} sections")
        
        content_filename = re.sub(r'[^\w\-_.]', '_', url.split('//')[1]) + '.json'
        content_filepath = os.path.join(PROCESSED_DIR, content_filename)
        with open(content_filepath, 'w', encoding='utf-8') as f:
            json.dump(extracted_content, f, indent=2)
        print(f"Saved processed content to: {content_filepath}")
        
        # Process and save JSONL content
        jsonl_path = os.path.join(PROCESSED_DIR, "npm_documentation.jsonl")
        print(f"Processing content for JSONL generation...")
        formatted_entries = process_content_for_jsonl(extracted_content, url)
        
        num_entries = 0
        if formatted_entries:
            try:
                with open(jsonl_path, 'a', encoding='utf-8') as f:
                    for entry in formatted_entries:
                        json_line = json.dumps(entry, ensure_ascii=False)
                        f.write(json_line + "\n")
                        num_entries += 1
                print(f"Successfully appended {num_entries} entries to JSONL file: {jsonl_path}")
            except Exception as e:
                print(f"Error writing to JSONL file: {e}")
        else:
            print(f"No entries generated for JSONL file from URL: {url}")
        
        # Calculate total store time for all operations
        store_time = (time.time() - store_start) * 1000  # Convert to milliseconds
        print(f"Content processing and storage completed in {store_time:.2f}ms")
        
        # Update statistics with both fetch and store times
        update_stats(url, fetch_time, store_time, True, jsonl_entries=num_entries)
        return extracted_content
    except Exception as e:
        total_time = (time.time() - fetch_start) * 1000
        print(f"Error processing {url}: {str(e)}")
        update_stats(url, total_time, 0, False, error=str(e), jsonl_entries=0)
        raise

def process_content_for_jsonl(content, url):
    """Process a single page's content into JSONL format."""
    print(f"\nProcessing content for JSONL - URL: {url}")
    
    combined_content = "\n\n".join(
        f"Section {section.get('index')}:\n{' '.join(section.get('content', [])).strip()}"
        for section in content
        if section.get('content')
    )

    if not combined_content:
        print(f"No valid content to process for {url}")
        return []

    print(f"Sending content to ChatGPT for processing - URL: {url}")
    prompt = (
        f"Based on the following npm documentation content, create questions a user might ask and answer them in detail. "
        f"Focus on practical npm usage, package management, and common workflows.\n\n"
        f"Content:\n{combined_content}\n\n"
        f"Format the output as a single valid JSON array where each entry matches:\n"
        f'{{"text": "System: You are an AI assistant specialized in npm package management. Provide detailed, practical answers about npm usage.\\n\\nUser: [Generated question]\\n\\nAssistant: [Generated answer]"}}'
    )

    try:
        print(f"Making API call to ChatGPT...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant specialized in npm package management."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
            temperature=0.7,
        )

        gpt_output = response.choices[0].message.content.strip()
        print(f"Received response from ChatGPT - Length: {len(gpt_output)} chars")
        print(f"First 200 chars of response: {gpt_output[:200]}")
        
        try:
            entries = json.loads(gpt_output)
            print(f"Successfully parsed JSON with {len(entries)} Q&A pairs for {url}")
            if len(entries) > 0:
                print(f"Sample entry: {json.dumps(entries[0], indent=2)}")
            return entries
        except json.JSONDecodeError as e:
            print(f"JSON decode error for {url}: {e}")
            print("Raw GPT output:", gpt_output)
            return []
    except Exception as e:
        print(f"Error processing content with ChatGPT for {url}: {e}")
        return []

async def main():
    base_url = "https://docs.npmjs.com"
    
    print(f"Fetching content from base URL: {base_url}")
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=base_url,
            extraction_strategy=LLMExtractionStrategy(
                provider="openai/gpt-4o",
                api_token=api_key,
                instruction="Extract the HTML structure to identify all relevant npm documentation links.",
            ),
            bypass_cache=True,
        )

    print("Raw HTML content fetched!")
    links = filter_relevant_links(extract_links(result.html))
    print(f"Found {len(links)} links.")
    print("Links:", links)

    if not links:
        print("No links found. Exiting...")
        return

    for idx, link in enumerate(links):
        print(f"Processing link {idx + 1}/{len(links)}: {link}")
        try:
            await fetch_content(link)
        except Exception as e:
            print(f"Error processing link {link}: {e}")
            continue

    print("Scraping completed!")

if __name__ == "__main__":
    asyncio.run(main())
