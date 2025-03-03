import os
import json
from typing import List
from pydantic import BaseModel, Field
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from tqdm import tqdm
import time
import argparse
import sys

load_dotenv()

class KeyManager:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.tried_keys = set()
        self.app = FirecrawlApp(api_key=self.current_key)
        self.tried_keys.add(self.current_key)
    
    @property
    def current_key(self):
        return self.api_keys[self.current_key_index]
    
    def rotate_key(self):
        """Rotate to the next untried key. Returns False if all keys have been tried."""
        original_index = self.current_key_index
        while True:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            if self.current_key not in self.tried_keys:
                self.app = FirecrawlApp(api_key=self.current_key)
                self.tried_keys.add(self.current_key)
                print(f"\nRotated to next API key ({self.current_key_index + 1}/{len(self.api_keys)})")
                return True
            if self.current_key_index == original_index:
                print("\nAll API keys have been tried and failed")
                return False
    
    def has_more_keys(self):
        """Check if there are any untried keys left."""
        return len(self.tried_keys) < len(self.api_keys)
    
    def reset_tried_keys(self):
        """Reset the tried keys tracking - useful for new requests."""
        self.tried_keys.clear()
        self.tried_keys.add(self.current_key)

class Section(BaseModel):
    title: str = Field(description="The title of the section")
    content: str = Field(description="The content of the section")

class CodeExample(BaseModel):
    title: str = Field(description="The title of the code example")
    snippet: str = Field(description="The code snippet")

class DocumentationPageContent(BaseModel):
    title: str = Field(description="The title of the documentation page")
    description: str = Field(description="A brief description of what the page covers")
    sections: List[Section] = Field(description="The main content sections of the page")
    codeExamples: List[CodeExample] = Field(description="Code examples, configurations, commands and command-line outputs found on the page", default_factory=list)
    tipsAndBestPractices: List[str] = Field(description="Tips and best practices mentioned in the documentation", default_factory=list)

def filter_links_by_base_url(base_url, links):
    filtered_links = []
    
    for link in links:
        if isinstance(link, str) and link.startswith(base_url):
            filtered_links.append(link)
    
    return filtered_links

# https://docs.firecrawl.dev/api-reference/endpoint/credit-usage
def scrape_url(url, key_manager, max_retries=3):
    print(f"Scraping: {url}")
    retries = 0
    last_error = None
    key_manager.reset_tried_keys()
    
    while retries < max_retries:
        try:
            data = key_manager.app.scrape_url(url, {
                'formats': ['markdown', 'json'],
                'jsonOptions': {
                    'schema': DocumentationPageContent.model_json_schema(),
                    'systemPrompt': """You are an expert in documentation analysis. Extract from this page:
                    1. The exact page title and description
                    2. All content sections with their titles and detailed content
                    3. Any code examples or logs with their context
                    4. Tips and best practices mentioned
                    Be thorough and PRESERVE ALL TECHNICAL DETAILS!"""
                } # For each of the following four items, ensure that the output for each one individually is UNDER 3.5k TOKENS, if it doesn't work out well, try to be under 4k!
            })
            if data and isinstance(data, dict):
                json_data = data.get("json")
                metadata = data.get("metadata", {})
                if json_data:
                    print(f"Successfully extracted JSON data from {url}")
                    return {"json": json_data, "metadata": metadata}
            print(f"No usable data returned for {url}")
            retries += 1
            if retries < max_retries:
                print(f"Retrying ({retries}/{max_retries})...")
                if key_manager.has_more_keys():
                    if key_manager.rotate_key():
                        retries = 0
                time.sleep(2)
        except Exception as e:
            last_error = e
            retries += 1
            if retries < max_retries:
                print(f"Error scraping {url} (attempt {retries}/{max_retries}): {e}")
                print("Retrying...")
                if ("rate limit" in str(e).lower() or "payment required" in str(e).lower() or "unexpected error" in str(e).lower()) and key_manager.has_more_keys():
                    if key_manager.rotate_key():
                        retries = 0
                time.sleep(2)
    if last_error:
        print(f"Failed to scrape {url} after {max_retries} attempts and trying {len(key_manager.tried_keys)} different API keys. Last error: {last_error}")
    return None

def get_documentation_links(base_url, key_manager, max_retries=3):
    print(f"Getting documentation links from {base_url}")
    retries = 0
    while retries < max_retries:
        try:
            key_manager.reset_tried_keys()
            response = key_manager.app.map_url(base_url)
            if response and response.get("links"):
                links = response.get("links", [])

                filtered_links = filter_links_by_base_url(base_url, links)

                print(f"Found {len(filtered_links)} unique documentation links")
                return filtered_links
            else:
                print("No links returned from map endpoint, using fallback method")
                return [base_url]
        except Exception as e:
            print(f"Error getting documentation links: {e}")
            if ("rate limit" in str(e).lower() or "payment required" in str(e).lower() or "unexpected error" in str(e).lower()) and key_manager.has_more_keys():
                if key_manager.rotate_key():
                    retries = 0
            retries += 1
            if retries < max_retries:
                print(f"Retrying ({retries}/{max_retries})...")
                time.sleep(2)
    print(f"Failed to get documentation links after {max_retries} attempts")
    return [base_url]

def create_conversation(product, content, url, page_metadata=None):
    if not content:
        return None
    
    qa_pairs = []
    
    # Overview with context
    if content.get("title") and content.get("description"):
        question = f"Can you explain what {content['title']} is in {product}?"
        answer = f"Sure, I'd be happy to explain {content['title']} in {product}.\n\n# {content['title']}\n\n{content['description']}"
        if content.get("sections"):
            answer += "Here's a quick rundown of what this is about:\n\n"
            for section in content["sections"]:
                answer += f"## {section['title']}\n\n{section['content']}\n\n"
            answer += "This should give you a solid starting point!"
        qa_pairs.append(("overview", question, answer))
    
    # Section-specific questions
    if content.get("sections"):
        for section in content["sections"]:
            question = f"How do I {section['title'].lower()} in {product}?"
            answer = f"To {section['title'].lower()} in {product}, here's what you do:\n{section['content']}.\nPretty straightforward, right?"
            qa_pairs.append(("section_detail", question, answer))
    
    # Code examples with explanation
    if content.get("codeExamples"):
        question = f"Can you give me some code examples for {content['title']} in {product}?"
        answer = "Absolutely! Here are some practical examples to help you out:\n\n"
        for example in content["codeExamples"]:
            answer += f"**{example['title']}**:\n\n```yaml\n{example['snippet']}\n```\n\n"
            answer += f"This snippet shows you how to {example['title'].lower()}, which is an important aspect of {content['title'].lower()}.\n\n"
        qa_pairs.append(("code_examples", question, answer))
    
    # Best practices with insight
    if content.get("tipsAndBestPractices"):
        question = f"What are some tips for using {content['title']} in {product} effectively?"
        answer = "Great question! Here are some tips to keep in mind:\n\n"
        for tip in content["tipsAndBestPractices"]:
            answer += f"{tip}\n\n"
        answer += "Stick to these, and you'll avoid a lot of headaches!"
        qa_pairs.append(("best_practices", question, answer))
    
    # Format JSONL entries
    jsonl_entries = []
    for qa_type, question, answer in qa_pairs:
        entry = {
            "text": f"System: You are a helpful {product} expert.\n\nUser: {question}\n\nAssistant: {answer}",
            "metadata": {
                "source_url": url,
                "title": content.get("title", ""),
                "description": content.get("description", ""),
                "has_code_examples": bool(content.get("codeExamples")),
                "has_best_practices": bool(content.get("tipsAndBestPractices")),
                "section_count": len(content.get("sections", [])),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": qa_type,
                "page_metadata": page_metadata or {}
            }
        }
        jsonl_entries.append(entry)
    
    return jsonl_entries

def log_url_attempt(index, url, output_file, status, entries_created=None, error=None):
    """Log every URL processing attempt to a file."""
    log_file = f"data/log/url_attempts_{os.path.basename(output_file)}"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    entry = {
        "index": index,
        "url": url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
    }
    if status == "success":
        entry["entries_created"] = entries_created
    elif status == "failure":
        entry["error"] = error
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def main(product, base_url, output_file, api_keys, start_index=0):
    if api_keys is None:
        api_keys = [key for key in os.getenv("FIRECRAWL_API_KEY", "").split(";") if key]
    else:
        api_keys = [key for key in api_keys if key]
    
    if not api_keys:
        raise ValueError("No valid API keys provided. Set FIRECRAWL_API_KEY environment variable or provide --api_key arguments.")
    
    print(f"Using {len(api_keys)} API keys")
    key_manager = KeyManager(api_keys)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    links = get_documentation_links(base_url, key_manager)
    total_links = len(links)
    print(f"\nStarting to process {total_links} pages...")

    if start_index < 0 or start_index >= total_links:
        print(f"Error: --start_index {start_index} is out of bounds. Must be between 0 and {total_links - 1}.")
        sys.exit(1)

    links_to_process = links[start_index:]
    print(f"Processing {len(links_to_process)} pages starting from index {start_index}")

    total_entries = 0
    failed_urls = []
    max_retries = 25
    
    with tqdm(total=total_links, initial=start_index, desc="Processing documentation pages") as pbar:
        for idx, link in enumerate(links_to_process, start=start_index):
            try:
                result = scrape_url(link, key_manager)
                if result and result.get("json"):
                    jsonl_entries = create_conversation(product, result["json"], link, result.get("metadata"))
                    entries_created = len(jsonl_entries) if jsonl_entries else 0
                    if jsonl_entries:
                        with open(output_file, "a", encoding="utf-8") as f:
                            for entry in jsonl_entries:
                                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                                total_entries += 1
                    print(f"\nProcessed {link} with {entries_created} entries")
                    log_url_attempt(idx, link, output_file, "success", entries_created=entries_created)
                else:
                    failed_urls.append((idx, link))
                    log_url_attempt(idx, link, output_file, "failure", error="No usable data returned from scrape_url")
            except Exception as e:
                print(f"\nError processing {link}: {e}")
                failed_urls.append((idx, link))
                log_url_attempt(idx, link, output_file, "failure", error=str(e))
            pbar.update(1)
            print(f"\nCompleted page {pbar.n}/{total_links}")
    
    if failed_urls:
        print(f"\nRetrying {len(failed_urls)} failed URLs...")
        retry_count = 0

        while failed_urls and retry_count < max_retries:
            retry_count += 1
            print(f"\nRetry attempt {retry_count}/{max_retries}")
            still_failed = []

            for idx, link in failed_urls:
                try:
                    result = scrape_url(link, key_manager)
                    if result and result.get("json"):
                        jsonl_entries = create_conversation(product, result["json"], link, result.get("metadata"))
                        entries_created = len(jsonl_entries) if jsonl_entries else 0
                        if jsonl_entries:
                            with open(output_file, "a", encoding="utf-8") as f:
                                for entry in jsonl_entries:
                                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                                    total_entries += 1
                        print(f"\nProcessed {link} with {entries_created} entries on retry {retry_count}")
                        log_url_attempt(idx, link, output_file, "success", entries_created=entries_created)
                    else:
                        still_failed.append((idx, link))
                        log_url_attempt(idx, link, output_file, "failure", error=f"No usable data returned on retry {retry_count}")
                except Exception as e:
                    print(f"\nError processing {link} on retry {retry_count}: {e}")
                    still_failed.append((idx, link))
                    log_url_attempt(idx, link, output_file, "failure", error=f"Error on retry {retry_count}: {str(e)}")

            failed_urls = still_failed
            if failed_urls:
                print(f"\n{len(failed_urls)} URLs still failing. Waiting before next retry...")
                time.sleep(5)
    
    print(f"\nFinished processing from index {start_index}. Created {total_entries} new entries in {output_file}")
    if failed_urls:
        print(f"Failed to process {len(failed_urls)} URLs after {max_retries} retries:")
        for idx, url in failed_urls:
            print(f"- Index {idx}: {url}")
    log_file = f"data/url_attempts_{os.path.basename(output_file)}"
    print(f"\nAll URL attempts have been logged to {log_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape documentation")
    parser.add_argument("--product", required=True, help="Product name (example: GitHub)")
    parser.add_argument("--base_url", required=True, help="Base URL for documentation (example: https://docs.github.com/en)")
    parser.add_argument("--output_file", required=True, help="Output file for the JSONL data (example: data/github_docs.jsonl)")
    parser.add_argument("--api_key", action="append", help="API key for Firecrawl. Can be specified multiple times.")
    parser.add_argument("--start_index", type=int, default=0, help="Index to start processing from (0-based; e.g., 1489 to resume after page 1488)")
    args = parser.parse_args()

    main(args.product, args.base_url, args.output_file, args.api_key, args.start_index)
