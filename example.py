import os
import json
import asyncio
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

def filter_relevant_links(links, base_url="https://docs.docker.com"):
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
            links.append(href if href.startswith("http") else f"https://docs.docker.com{href}")
    return list(set(links))  # Remove duplicates


async def fetch_content(url):
    """Fetch content from the given URL using AsyncWebCrawler."""
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            extraction_strategy=LLMExtractionStrategy(
                provider="openai/gpt-4o",
                api_token=api_key,
                instruction="Extract the most relevant content from this page for generating questions and answers.",
            ),
            bypass_cache=True,
        )
    extracted_content = json.loads(result.extracted_content)
    return extracted_content


def process_all_with_chatgpt(content):
    """Send all extracted content to ChatGPT for processing into a single JSONL output."""
    combined_content = "\n\n".join(
        f"Section {section.get('index')}:\n{' '.join(section.get('content', [])).strip()}"
        for section in content
        if section.get('content')
    )

    if not combined_content:
        print("No valid content to process.")
        return []

    prompt = (
        f"Based on the following content, create questions a user might ask and answer them in detail. "
        f"Ensure the format matches strictly:\n\n"
        f"Content:\n{combined_content}\n\n"
        f"Format the output as a single valid JSON array where each entry matches:\n"
        f'{{"text": "System: You are an AI assistant. Provide a detailed answer so the user doesn’t need to search outside to understand the answer.\\n\\nUser: [Generated question]\\n\\nAssistant: [Generated answer]"}}'
    )

    print("Sending combined content to ChatGPT...")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
            temperature=0.7,
        )

        gpt_output = response.choices[0].message.content.strip()
        print("Raw GPT response:", gpt_output)  # Debugging line

        # Attempt to parse the response as JSON
        try:
            gpt_entries = json.loads(gpt_output)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print("Raw GPT output:", gpt_output)  # Log raw output for debugging
            return []

        return gpt_entries
    except Exception as e:
        print(f"Error processing combined content: {e}")
        return []


async def main():
    base_url = "https://docs.docker.com/get-started"
    output_path = ".data/generated_content.jsonl"

    print(f"Fetching content from base URL: {base_url}")
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=base_url,
            extraction_strategy=LLMExtractionStrategy(
                provider="openai/gpt-4o",
                api_token=api_key,
                instruction="Extract the HTML structure to identify all relevant links.",
            ),
            bypass_cache=True,
        )

    # Extract links from the HTML content
    html_content = result.html
    print("Raw HTML content fetched:")
    print(html_content[:1000])

    links = filter_relevant_links(extract_links(html_content))
    print(f"Found {len(links)} links.")
    print("Links:", links)

    if not links:
        print("No links found. Exiting...")
        return

    all_extracted_content = []

    # Fetch and process each link
    for idx, link in enumerate(links):
        print(f"Processing link {idx + 1}/{len(links)}: {link}")
        try:
            content = await fetch_content(link)
            all_extracted_content.extend(content)
        except Exception as e:
            print(f"Error processing link {link}: {e}")
            continue

    if not all_extracted_content:
        print("No content extracted from links.")
        return

    print("Processing extracted content with ChatGPT...")
    formatted_entries = process_all_with_chatgpt(all_extracted_content)

    if not formatted_entries:
        print("No formatted entries generated.")
        return

    # Save results to a JSONL file
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in formatted_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Generated content saved to {output_path}")
# Run the script
asyncio.run(main())