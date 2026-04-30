#!/usr/bin/env python
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import requests
    print("✓ requests imported")
except Exception as e:
    print(f"✗ requests failed: {e}")

try:
    import bs4
    print("✓ bs4 imported")
except Exception as e:
    print(f"✗ bs4 failed: {e}")

try:
    from langchain_text_splitters import HTMLHeaderTextSplitter
    print("✓ langchain_text_splitters imported")
except Exception as e:
    print(f"✗ langchain_text_splitters failed: {e}")

try:
    from langchain_chroma import Chroma
    print("✓ langchain_chroma imported")
except Exception as e:
    print(f"✗ langchain_chroma failed: {e}")

try:
    from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
    print("✓ sentence_transformers embeddings imported")
except Exception as e:
    print(f"✗ sentence_transformers embeddings failed: {e}")

print("\n--- Running test URL fetch ---")
try:
    response = requests.get("https://www.example.com", timeout=5)
    print(f"✓ Network request successful (status: {response.status_code})")
except Exception as e:
    print(f"✗ Network request failed: {e}")

print("\nAll import tests completed!")
