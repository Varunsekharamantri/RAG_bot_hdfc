# Data Processing Architecture: Chunking & Embedding

This document outlines the detailed architecture for processing the scraped Groww HTML pages into vector embeddings, ensuring the Mutual Fund FAQ assistant retrieves accurate and structured facts.

## 1. Scraping Service Output (Input to Pipeline)
*   **Format:** Raw HTML strings or parsed BeautifulSoup objects for each of the 5 Groww scheme URLs.
*   **Frequency:** Received daily at 9:15 AM IST via the GitHub Actions scheduler.

## 2. HTML Cleaning & Pre-Processing
Before chunking, the raw HTML must be cleaned to remove noise.
*   **DOM Stripping:** Remove `<script>`, `<style>`, `<nav>`, `<footer>`, and advertisement tags.
*   **Content Extraction:** Extract the main content div (usually containing scheme details, expense ratios, return tables, and fund manager details).
*   **Table Preservation:** Convert HTML tables into Markdown format. This is critical for tabular data like "Exit Load", "Expense Ratio", and "Minimum SIP" so the LLM can read the rows and columns accurately.

## 3. Chunking Strategy
Given the nature of factual mutual fund data, a hybrid or structural chunking approach is highly recommended.

*   **Method 1: Structural Chunking / HTML Header Splitter (Preferred)**
    *   Split the document based on HTML headers (`<h2>`, `<h3>`). For example, the "Pros and Cons" section becomes one chunk, "Scheme Details" becomes another.
    *   *Why?* This keeps related context together (e.g., the exit load is kept in the same chunk as the expense ratio under the "Fees and Charges" header) avoiding fragmentation.
*   **Method 2: Recursive Character Text Splitting (Fallback)**
    *   **Chunk Size:** 500 - 800 tokens.
    *   **Chunk Overlap:** 50 - 100 tokens (to ensure no sentence/fact is cut in half).
    *   **Separators:** `["\n\n", "\n", " ", ""]` (prioritize splitting by paragraphs).

## 4. Metadata Tagging (Crucial for Citations)
Every single chunk generated must be enriched with metadata. This ensures the chatbot can provide accurate citations and source links in the UI.
*   **Required Metadata Fields:**
    *   `scheme_name` (e.g., "HDFC Mid-Cap Opportunities Fund")
    *   `source_url` (e.g., "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth")
    *   `section_header` (e.g., "Expense Ratio & Exit Load" - if using structural chunking)
    *   `last_updated` (The timestamp from the 9:15 AM scheduler run)

## 5. Embedding Generation
*   **Model Selection:** Use a high-quality, lightweight embedding model capable of understanding financial/numeric data context (e.g., `text-embedding-3-small` from OpenAI, or `BAAI/bge-large-en-v1.5` for open-source).
*   **Process:** Pass the `page_content` of each chunk through the embedding model to generate dense vector representations.
*   **Batching:** Embed chunks in batches to optimize API usage and execution time during the GitHub Actions run.

## 6. Vector Database Storage & Upsertion
*   **Database:** Use a lightweight vector store like **ChromaDB** or **FAISS** (or Pinecone/Qdrant for cloud hosting).
*   **Upsert Logic (Daily Refresh):**
    *   Since the GitHub Action runs daily at 9:15 AM, the scheme data (like NAV or AUM) might change.
    *   The pipeline should delete the old documents for the specific `source_url` and insert the newly generated chunks (Upsert operation). This prevents duplicate context and ensures the assistant always provides the freshest facts.
