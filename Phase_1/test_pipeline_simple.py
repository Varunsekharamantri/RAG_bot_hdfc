import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv

print("Test 1: Basic imports successful")

# Test URL fetching
URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
]

print("Test 2: Attempting to fetch first URL...")
try:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(URLS[0], headers=headers, timeout=10)
    response.raise_for_status()
    print(f"✓ Successfully fetched URL. Status: {response.status_code}, Content length: {len(response.text)}")
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    print(f"✓ Successfully parsed HTML. Found {len(soup.find_all())} tags")
    
    # Extract title
    title = soup.find('h1')
    if title:
        print(f"✓ Found H1 title: {title.get_text()[:100]}")
    
except requests.RequestException as e:
    print(f"✗ Request failed: {e}")
except Exception as e:
    print(f"✗ Parsing failed: {e}")

print("\nTest 3: Now testing LangChain imports...")
try:
    print("  - Importing langchain_text_splitters...")
    from langchain_text_splitters import HTMLHeaderTextSplitter
    print("  ✓ HTMLHeaderTextSplitter imported")
    
    print("  - Importing langchain_chroma...")
    from langchain_chroma import Chroma
    print("  ✓ Chroma imported")
    
    print("  - Importing embeddings...")
    from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
    print("  ✓ SentenceTransformerEmbeddings imported")
    
    print("\n✓ All LangChain imports successful!")
    
except ImportError as e:
    print(f"\n✗ Import Error: {e}")
except Exception as e:
    print(f"\n✗ Unexpected Error: {e}")

print("\nTest completed!")
