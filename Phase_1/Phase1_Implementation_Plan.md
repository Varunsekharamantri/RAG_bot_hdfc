# Implementation Plan: Phase 1 (Data Ingestion Pipeline)

This plan outlines how we will implement Step 2 (Scraping) and Step 3 (Chunking & Embedding) of Phase 1 to build the Knowledge Base for the Mutual Fund FAQ Assistant.

## Design Decisions
*   **Embedding Model Selection:** We will use a free, local, open-source embedding model (`all-MiniLM-L6-v2` or `BAAI/bge-small-en-v1.5`) via `SentenceTransformers` so no API key is required.
*   **Vector DB Location:** We will set up a local `ChromaDB` instance (a folder named `chroma_db` in the workspace) to store the vectors. This is perfectly suited for a small corpus and GitHub Actions.

## Proposed Changes

We will create the following files to isolate Phase 1 into a clean, reproducible script that can be triggered by GitHub Actions.

---

### Phase 1 Python Pipeline

#### [NEW] `phase1_data_pipeline.py`
This script will be the core pipeline. It will contain the following logic:
1.  **Scraping:** Loop through the 5 HDFC Groww URLs using `requests` and `BeautifulSoup`.
2.  **HTML Cleaning:** Strip out `<script>`, `<style>`, and `<nav>` tags. Detect `<table>` elements and convert them to Markdown tables (crucial for accurate expense ratio/exit load reading).
3.  **Chunking:** Use LangChain's `HTMLHeaderTextSplitter` to structurally chunk the documents based on `<h2>` and `<h3>` tags, keeping related facts together. We'll add a fallback `RecursiveCharacterTextSplitter` for large sections.
4.  **Metadata Tagging:** Attach `source_url`, `scheme_name` (extracted from the URL or H1 tag), and a `last_updated` timestamp to every chunk.
5.  **Embedding & Upsert:** Connect to a local ChromaDB instance, delete old chunks matching the `source_url`, and upsert the new chunks.

#### [NEW] `requirements.txt`
We will add the necessary dependencies for the pipeline:
*   `requests`
*   `beautifulsoup4`
*   `langchain`
*   `langchain-text-splitters`
*   `langchain-community`
*   `langchain-chroma`
*   `sentence-transformers`
*   `chromadb`
