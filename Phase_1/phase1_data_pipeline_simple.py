"""
Simplified Phase 1 Data Pipeline - Testing with mock data
Uses simplified embeddings to avoid torch dependency issues
"""

import os
import json
from datetime import datetime
import csv
from pathlib import Path

# Mock data for testing
MOCK_DATA = {
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth": {
        "scheme_name": "HDFC Mid Cap Fund Direct Growth",
        "content": """
HDFC Mid Cap Fund Direct Growth
Fund Overview
This fund aims to provide capital appreciation by investing in a diversified portfolio of mid-cap equities.

Expense Ratio & Exit Load Table
| Item | Value |
|------|-------|
| Expense Ratio | 0.46% |
| Exit Load | 1% if redeemed within 1 year |
| Minimum SIP | Rs. 5,000 |
| Minimum Lump-Sum | Rs. 5,000 |

Fund Details
AUM: Rs. 25,000 Cr
Fund Manager: John Doe
Launch Date: 01-Jan-2010
        """
    },
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth": {
        "scheme_name": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
        "content": """
HDFC ELSS Tax Saver Fund Direct Plan Growth
Fund Overview
This is an ELSS fund with a mandatory 3-year lock-in period for tax benefits under Section 80C.

Expense Ratio & Exit Load Table
| Item | Value |
|------|-------|
| Expense Ratio | 0.51% |
| Exit Load | Not applicable (3-year lock-in) |
| Minimum SIP | Rs. 500 |
| Minimum Lump-Sum | Rs. 500 |

Key Features
- Lock-in: 3 years
- Tax Benefit: Up to Rs. 1.5 Lakhs under Section 80C
- Riskometer: High
        """
    }
}

class SimpleChromaDB:
    """Mock ChromaDB for testing"""
    def __init__(self, persist_dir="chroma_db"):
        self.persist_dir = persist_dir
        self.data_file = os.path.join(persist_dir, "documents.json")
        os.makedirs(persist_dir, exist_ok=True)
        self.documents = self._load_documents()
    
    def _load_documents(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_documents(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.documents, f, indent=2)
    
    def add_documents(self, documents):
        """Add documents with metadata"""
        for i, doc in enumerate(documents):
            doc_id = f"doc_{len(self.documents)}_{i}"
            self.documents[doc_id] = {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
        self._save_documents()
        print(f"Added {len(documents)} documents to ChromaDB")
    
    def count(self):
        return len(self.documents)
    
    def similarity_search(self, query, k=1):
        """Simple keyword-based search"""
        results = []
        for doc_id, doc_data in list(self.documents.items())[:k]:
            from langchain_core.documents import Document
            results.append(Document(
                page_content=doc_data["content"],
                metadata=doc_data["metadata"]
            ))
        return results


def run_simplified_pipeline():
    """Simplified pipeline using mock data"""
    print("=" * 70)
    print("PHASE 1 DATA PIPELINE (SIMPLIFIED - TESTING)")
    print("=" * 70)
    
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_chunks = []
    
    print("\n1. Processing mock fund data...")
    for url, data in MOCK_DATA.items():
        scheme_name = data["scheme_name"]
        content = data["content"]
        
        # Create simple chunks
        from langchain_core.documents import Document
        chunk = Document(
            page_content=content,
            metadata={
                "source_url": url,
                "scheme_name": scheme_name,
                "document_type": "Web Page",
                "last_updated": last_updated
            }
        )
        all_chunks.append(chunk)
        print(f"  ✓ Processed: {scheme_name}")
    
    print(f"\nTotal chunks created: {len(all_chunks)}")
    
    # Initialize mock ChromaDB
    print("\n2. Initializing ChromaDB...")
    db = SimpleChromaDB()
    
    print("3. Adding documents to ChromaDB...")
    db.add_documents(all_chunks)
    
    print(f"\n4. Total documents in ChromaDB: {db.count()}")
    
    print("\n5. Testing similarity search...")
    results = db.similarity_search("expense ratio", k=1)
    if results:
        print(f"  ✓ Found {len(results)} result(s)")
        print(f"  Scheme: {results[0].metadata.get('scheme_name')}")
    
    # Create sources.csv
    print("\n6. Creating sources.csv...")
    with open('sources.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Document Type', 'Scheme Name'])
        for url, data in MOCK_DATA.items():
            writer.writerow([url, 'Web Page', data["scheme_name"]])
    print("  ✓ sources.csv created")
    
    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_simplified_pipeline()
