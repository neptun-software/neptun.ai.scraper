# AI Documentation Scraper

A tool for scraping and generating Q&A pairs for RNN training using GPT-4.

## Prerequisites

- Python 3.9 or higher
- Poetry (package manager)
- OpenAI API Key

## Installation

1. Install Poetry (if not already installed):

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:

   ```bash
   poetry install
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API Key to the `.env` file

## Usage

Start the scraper in the Poetry environment:

```bash
poetry run python scrape.\*.py
```

Generated Q&A pairs will be saved to `data/\*.jsonl
