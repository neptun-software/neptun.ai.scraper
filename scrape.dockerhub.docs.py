import os
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import ast
import re

# use https://docs.docker.com/{example}/ as baseurl
BASE_URL = "https://docs.docker.com/manuals"
OUTPUT_PATH = "generated_content.jsonl"
OPENAI_MODEL = "gpt-3.5-turbo-0125"
TEMPERATURE = 0.7
MAX_TOKENS = 700
API_INSTRUCTION = (
    "Extract the most relevant content from this page for generating questions and answers."
)
HTML_EXTRACTION_INSTRUCTION = (
    "Extract the HTML structure to identify all relevant links."
)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Ensure it is set in the .env file.")

client = OpenAI(api_key=api_key)


def filter_relevant_links(links, base_url="https://docs.docker.com"):
    relevant_links = [link for link in links if link.startswith(base_url)]
    return relevant_links


def extract_links(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("http") or href.startswith("/"):
            links.append(href)
    return list(set(links))


async def fetch_content(url):
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            extraction_strategy=LLMExtractionStrategy(
                provider=f"openai/{OPENAI_MODEL}",
                api_token=api_key,
                instruction=API_INSTRUCTION,
            ),
            disable_cache=True
        )
    return json.loads(result.extracted_content)


def fix_json_format(gpt_output):
    try:
        gpt_output_fixed = re.sub(r"(?<!\\)'", '"', gpt_output)
        return json.loads(gpt_output_fixed)
    except Exception as e:
        print(f"Failed to fix JSON: {e}")
        return None


def process_content_with_chatgpt(content, output_path):
    combined_content = "\n\n".join(
        f"Section {section.get('index')}:\n{' '.join(section.get('content', [])).strip()}"
        for section in content
        if section.get('content')
    )

    if not combined_content:
        print("No valid content to process for this link.")
        return

    prompt = (
        f"Based on the following content, create questions a user might ask and answer them in detail. "
        f"Ensure the format matches strictly:\n\n"
        f"Content:\n{combined_content}\n\n"
        f"Format the output as individual JSON objects, one per line, without commas separating them. "
        f'Each JSON object should be in the format:\n'
        f'{"{"}"text": "System: You are an AI assistant. Provide a detailed answer so the user doesn’t need to search outside to understand the answer.\\n\\nUser: [Generated question]\\n\\nAssistant: [Generated answer]"{"}"}\n'
    )

    print("Sending content to ChatGPT...")
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an AI assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )

        gpt_output = response.choices[0].message.content.strip()
        print("GPT response received.")

        with open(output_path, "a", encoding="utf-8") as f:
            json_objects = gpt_output.strip().split("\n")
            for obj in json_objects:
                f.write(obj.strip() + "\n")

        print("Output successfully appended to the JSONL file.")

    except Exception as e:
        print(f"Error processing content with ChatGPT: {e}")


async def main():
    print(f"Fetching content from base URL: {BASE_URL}")
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=BASE_URL,
            extraction_strategy=LLMExtractionStrategy(
                provider=f"openai/{OPENAI_MODEL}",
                api_token=api_key,
                instruction=HTML_EXTRACTION_INSTRUCTION,
            ),
            disable_cache=True,
        )

    html_content = result.html
    links = filter_relevant_links(extract_links(html_content))
    print(f"Found {len(links)} links.")
    print("Links:", links)

    if not links:
        print("No links found. Exiting...")
        return

    for idx, link in enumerate(links):
        print(f"Processing link {idx + 1}/{len(links)}: {link}")
        try:
            content = await fetch_content(link)
            process_content_with_chatgpt(content, OUTPUT_PATH)
        except Exception as e:
            print(f"Error processing link {link}: {e}")
            continue

    print(f"Content processing complete. Results saved to {OUTPUT_PATH}")

asyncio.run(main())
