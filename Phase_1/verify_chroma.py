import os
import json
from langchain_core.documents import Document

CHROMA_DB_DIR = "chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

class SimpleChromaDB:
    """Mock ChromaDB for testing"""
    def __init__(self, persist_dir="chroma_db"):
        self.persist_dir = persist_dir
        self.data_file = os.path.join(persist_dir, "documents.json")
        self.documents = self._load_documents()
    
    def _load_documents(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {}
    
    def count(self):
        return len(self.documents)
    
    def similarity_search(self, query, k=1):
        """Simple keyword-based search"""
        query_lower = query.lower()
        results = []
        for doc_id, doc_data in self.documents.items():
            content_lower = doc_data["content"].lower()
            if any(word in content_lower for word in query_lower.split()):
                results.append(Document(
                    page_content=doc_data["content"],
                    metadata=doc_data["metadata"]
                ))
        return results[:k]
    
    def get_all_documents(self):
        """Get all documents as Document objects"""
        results = []
        for doc_id, doc_data in self.documents.items():
            results.append(Document(
                page_content=doc_data["content"],
                metadata=doc_data["metadata"]
            ))
        return results

def verify():
    print("Initializing ChromaDB...")
    vectorstore = SimpleChromaDB(persist_dir=CHROMA_DB_DIR)
    
    # 1. Get total number of chunks
    print("\n" + "=" * 70)
    print("1. TOTAL CHUNKS IN CHROMADB")
    print("=" * 70)
    total_docs = vectorstore.count()
    print(f"Total chunks stored: {total_docs}\n")
    
    if total_docs == 0:
        print("⚠️  No documents found in ChromaDB! Please run phase1_data_pipeline_simple.py first.")
        return
    
    # 2. Retrieve 2 sample chunks
    print("=" * 70)
    print("2. SAMPLE CHUNKS (First 2)")
    print("=" * 70)
    all_docs = vectorstore.get_all_documents()
    sample_docs = all_docs[:2]
    
    for idx, doc in enumerate(sample_docs, 1):
        print(f"\n--- CHUNK {idx} ---")
        print(f"\nMETADATA:")
        print(f"  Source URL: {doc.metadata.get('source_url', 'MISSING')}")
        print(f"  Scheme Name: {doc.metadata.get('scheme_name', 'MISSING')}")
        print(f"  Document Type: {doc.metadata.get('document_type', 'MISSING')}")
        print(f"  Last Updated: {doc.metadata.get('last_updated', 'MISSING')}")
        
        print(f"\nRAW TEXT CONTENT (Checking for Markdown tables):")
        print("-" * 70)
        # Limit output to first 500 chars to avoid overwhelming output
        content_preview = doc.page_content[:800] if len(doc.page_content) > 800 else doc.page_content
        print(content_preview)
        if len(doc.page_content) > 800:
            print(f"\n... [Content truncated, total length: {len(doc.page_content)} chars]")
        print("-" * 70)
    
    # 3. Test similarity search for 'What is the exit load?'
    print("\n" + "=" * 70)
    print("3. SIMILARITY SEARCH TEST: 'What is the exit load?'")
    print("=" * 70)
    search_query = "What is the exit load?"
    search_results = vectorstore.similarity_search(search_query, k=1)
    
    if search_results:
        top_result = search_results[0]
        print(f"\nQuery: '{search_query}'")
        print(f"\nTop Result Metadata:")
        print(f"  Source URL: {top_result.metadata.get('source_url', 'MISSING')}")
        print(f"  Scheme Name: {top_result.metadata.get('scheme_name', 'MISSING')}")
        print(f"  Document Type: {top_result.metadata.get('document_type', 'MISSING')}")
        print(f"  Last Updated: {top_result.metadata.get('last_updated', 'MISSING')}")
        
        print(f"\nTop Result Content (Preview):")
        print("-" * 70)
        content_preview = top_result.page_content[:600] if len(top_result.page_content) > 600 else top_result.page_content
        print(content_preview)
        if len(top_result.page_content) > 600:
            print(f"\n... [Content truncated, total length: {len(top_result.page_content)} chars]")
        print("-" * 70)
    else:
        print("⚠️  No results found for the search query.")
    
    print("\n" + "=" * 70)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    verify()
