import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings

# Configuration
URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
]

CHROMA_DB_DIR = "chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SOURCES_CSV = "sources.csv"

def get_scheme_name(url):
    """Extracts a readable scheme name from the URL."""
    # e.g., hdfc-mid-cap-fund-direct-growth -> HDFC Mid Cap Fund Direct Growth
    slug = url.split("/")[-1]
    return " ".join([word.capitalize() for word in slug.split("-")])

def convert_table_to_markdown(table):
    """Converts a BeautifulSoup table object to a Markdown string."""
    rows = table.find_all('tr')
    if not rows:
        return ""
    
    md_table = []
    for i, row in enumerate(rows):
        cols = row.find_all(['th', 'td'])
        row_data = [col.get_text(strip=True) for col in cols]
        md_table.append("| " + " | ".join(row_data) + " |")
        
        # Add separator after header
        if i == 0:
            md_table.append("|" + "|".join(["---"] * len(row_data)) + "|")
            
    return "\n".join(md_table)

def clean_html(html_content):
    """Removes scripts, styles, and converts tables to markdown."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted tags
    for tag in soup(['script', 'style', 'nav', 'footer', 'noscript', 'iframe']):
        tag.decompose()
        
    # Convert tables to markdown and replace them in the DOM
    for table in soup.find_all('table'):
        md_table = convert_table_to_markdown(table)
        # Create a new p tag with the markdown content
        new_tag = soup.new_tag("p")
        new_tag.string = md_table
        table.replace_with(new_tag)
        
    return str(soup)

def process_url(url, last_updated):
    """Scrapes, cleans, and structurally chunks a single URL."""
    print(f"Processing {url}...")
    try:
        # User-Agent is necessary to avoid 403 Forbidden from many websites
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return []

    scheme_name = get_scheme_name(url)
    cleaned_html = clean_html(response.text)

    # 1. Structural Chunking based on HTML headers
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    html_header_splits = html_splitter.split_text(cleaned_html)

    # 2. Fallback chunking for large sections
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    
    final_chunks = text_splitter.split_documents(html_header_splits)
    
    # 3. Add Metadata
    for chunk in final_chunks:
        chunk.metadata['source_url'] = url
        chunk.metadata['scheme_name'] = scheme_name
        chunk.metadata['document_type'] = "Web Page"
        chunk.metadata['last_updated'] = last_updated
        
    return final_chunks

def maintain_sources_csv():
    """Maintains the sources.csv file with the list of URLs."""
    # Write only if doesn't exist, or overwrite to ensure correct state
    with open(SOURCES_CSV, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Document Type', 'Scheme Name'])
        for url in URLS:
            writer.writerow([url, 'Web Page', get_scheme_name(url)])

def run_pipeline():
    """Main function to run the scraping, chunking, and embedding pipeline."""
    print("Starting Phase 1 Data Pipeline...")
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Scrape and Chunk
    all_chunks = []
    for url in URLS:
        chunks = process_url(url, last_updated)
        all_chunks.extend(chunks)
        
    print(f"Total chunks generated: {len(all_chunks)}")
    
    if not all_chunks:
        print("No chunks generated. Exiting.")
        return

    # 2. Initialize Embeddings and Vector DB
    print("Initializing Embedding Model...")
    embedding_func = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    
    print("Connecting to ChromaDB...")
    vectorstore = Chroma(
        collection_name="mutual_fund_faqs",
        embedding_function=embedding_func,
        persist_directory=CHROMA_DB_DIR
    )
    
    # 3. Upsert Logic: Delete old data for these URLs before inserting new ones
    # Note: ChromaDB doesn't have a direct 'delete by metadata' in the basic API easily without fetching IDs.
    # A robust way is to fetch existing IDs by source_url and delete them.
    for url in URLS:
        try:
            # We can use the get() method with a where filter to find matching IDs
            existing_docs = vectorstore.get(where={"source_url": url})
            if existing_docs and existing_docs['ids']:
                print(f"Deleting {len(existing_docs['ids'])} old chunks for {url}")
                vectorstore.delete(ids=existing_docs['ids'])
        except Exception as e:
            # First run might throw an error or return empty, that's fine
            pass
            
    # 4. Insert new chunks
    print("Inserting new chunks into ChromaDB...")
    vectorstore.add_documents(documents=all_chunks)
    
    # 5. Save sources.csv
    maintain_sources_csv()
    
    print("Pipeline completed successfully!")

if __name__ == "__main__":
    run_pipeline()
