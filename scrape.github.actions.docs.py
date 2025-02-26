import os
import json
from typing import List
from pydantic import BaseModel, Field
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
if not FIRECRAWL_API_KEY:
    raise ValueError("FIRECRAWL_API_KEY not found. Ensure it is set in the .env file.")

app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

BASE_URL = "https://docs.github.com/en/actions"
OUTPUT_FILE = "data/github_actions_docs.jsonl"

class Section(BaseModel):
    title: str = Field(description="The title of the section")
    content: str = Field(description="The content of the section")

class CodeExample(BaseModel):
    title: str = Field(description="The title of the code example")
    snippet: str = Field(description="The code snippet")

class GitHubActionsContent(BaseModel):
    title: str = Field(description="The title of the documentation page")
    description: str = Field(description="A brief description of what the page covers")
    sections: List[Section] = Field(description="The main content sections of the page")
    codeExamples: List[CodeExample] = Field(description="Code examples and workflows found on the page", default_factory=list)
    tipsAndBestPractices: List[str] = Field(description="Tips and best practices mentioned in the documentation", default_factory=list)

def scrape_url(url):
    print(f"Scraping: {url}")
    try:
        data = app.scrape_url(url, {
            'formats': ['markdown', 'json'],
            'jsonOptions': {
                'schema': GitHubActionsContent.model_json_schema(),
                'systemPrompt': """You are an expert in GitHub Actions documentation analysis. Extract from this page:
                1. The exact page title and description
                2. All content sections with their titles and detailed content
                3. Any code examples or workflow snippets with their context
                4. Tips and best practices mentioned
                Be thorough and preserve all technical details."""
            }
        })

        json_data = data.get("json")
        if json_data:
            print(f"Successfully extracted JSON data from {url}")
            return json_data

        print(f"No usable data returned for {url}")
        return None

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def get_documentation_links():
    try:
        response = app.map_url(BASE_URL, {
            "search": "action"
        })
        
        if not response or not response.get("links"):
            print("No links returned from map endpoint, using fallback method")
            return [BASE_URL]
            
        links = response.get("links", [])
        
        print(f"Found {len(links)} unique documentation links")
        return links
    except Exception as e:
        print(f"Error getting documentation links: {e}")
        return [BASE_URL]

def create_conversation(content):
    if not content:
        return None
    
    # Create question-answer pairs based on the content
    qa_pairs = []
    
    # Main overview question
    if content.get("title") and content.get("description"):
        question = f"What is {content['title']}?"
        answer = content["description"]
        if content.get("sections"):
            # Add section content to the answer
            answer += "\n\nHere's a detailed explanation:\n\n"
            for section in content["sections"]:
                answer += f"\n## {section['title']}\n{section['content']}\n"
        qa_pairs.append((question, answer))
    
    # Code examples question
    if content.get("codeExamples"):
        question = f"Can you show me some code examples for {content['title']}?"
        answer = "Here are some code examples:\n\n"
        for example in content["codeExamples"]:
            answer += f"### {example['title']}\n```yaml\n{example['snippet']}\n```\n\n"
        qa_pairs.append((question, answer))
    
    # Best practices question
    if content.get("tipsAndBestPractices"):
        question = f"What are the best practices for {content['title']}?"
        answer = "Here are the recommended best practices:\n\n"
        for tip in content["tipsAndBestPractices"]:
            answer += f"• {tip}\n"
        qa_pairs.append((question, answer))
    
    # Create JSONL entries from the QA pairs
    jsonl_entries = []
    for question, answer in qa_pairs:
        entry = {
            "text": f"System: You are a helpful GitHub Actions expert.\n\nUser: {question}\n\nAssistant: {answer}"
        }
        jsonl_entries.append(entry)
    
    return jsonl_entries

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    links = get_documentation_links()
    print(f"\nStarting to process {len(links)} pages...")
    
    total_entries = 0
    processed_pages = 0
    
    for link in tqdm(links, desc="Processing documentation pages"):
        try:
            content = scrape_url(link)
            if content:
                jsonl_entries = create_conversation(content)
                if jsonl_entries:
                    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                        for entry in jsonl_entries:
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                            total_entries += 1
                    print(f"\nCreated {len(jsonl_entries)} entries from {link}")
            
            processed_pages += 1
            print(f"\nCompleted page {processed_pages}/{len(links)}")
                
        except Exception as e:
            print(f"\nError processing {link}: {e}")
            continue

    print(f"\nFinished processing {processed_pages} pages. Created {total_entries} entries in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
