import os
import json
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleChromaDB:
    """Mock ChromaDB for testing without torch dependencies."""
    def __init__(self, persist_dir="chroma_db"):
        self.persist_dir = persist_dir
        self.data_file = os.path.join(persist_dir, "documents.json")
        self.documents = self._load_documents()
    
    def _load_documents(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        logger.warning(f"No mock DB found at {self.data_file}")
        return {}
    
    def similarity_search(self, query, k=1):
        """Simple keyword-based search simulation"""
        results = []
        # Fallback to simple sub-string matching or just return the first k for the demo
        query_lower = query.lower()
        
        # Simple scoring: count keyword matches
        scored_docs = []
        for doc_id, doc_data in self.documents.items():
            content = doc_data["content"].lower()
            score = sum(1 for word in query_lower.split() if word in content and len(word) >= 3)
            scored_docs.append((score, doc_data))
            
        # Sort by score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        from langchain_core.documents import Document
        # Return top k (even if score is 0, just to return *something* like a vector DB might)
        for score, doc_data in scored_docs[:k]:
            results.append(Document(
                page_content=doc_data["content"],
                metadata=doc_data["metadata"]
            ))
        return results

class Retriever:
    """Handles vector search and context assembly for Phase 3 (Simplified to bypass Torch)."""
    
    def __init__(self, persist_directory: str = "../Phase_1/chroma_db", collection_name: str = "mutual_fund_faqs"):
        """
        Initializes the retriever with the simple mock ChromaDB.
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        try:
            self.vectorstore = SimpleChromaDB(persist_dir=self.persist_directory)
            logger.info(f"Successfully connected to SimpleChromaDB at {persist_directory}")
        except Exception as e:
            logger.error(f"Failed to connect to SimpleChromaDB: {e}")
            raise

    def retrieve_context(self, query: str, k: int = 3) -> Tuple[str, List[str], str]:
        """
        Performs a simulated similarity search to retrieve the most relevant chunks.
        """
        logger.info(f"Retrieving top {k} chunks for query: '{query}'")
        
        results = self.vectorstore.similarity_search(query, k=k)
        
        if not results:
            logger.warning("No relevant context found in Vector DB.")
            return "", [], ""
            
        context_parts = []
        sources = set()
        last_updated_dates = []
        
        for i, doc in enumerate(results):
            content = doc.page_content.strip()
            source_url = doc.metadata.get("source_url", "Unknown Source")
            last_updated = doc.metadata.get("last_updated", "")
            
            context_parts.append(f"--- Chunk {i+1} ---\n{content}\n")
            sources.add(source_url)
            if last_updated:
                last_updated_dates.append(last_updated)
                
        assembled_context = "\n".join(context_parts)
        unique_sources = list(sources)
        most_recent_date = max(last_updated_dates) if last_updated_dates else "Unknown Date"
        
        logger.info(f"Assembled context from {len(results)} chunks. Sources: {unique_sources}")
        
        return assembled_context, unique_sources, most_recent_date

if __name__ == "__main__":
    print("Testing Phase 3 Retriever (Simplified)...")
    retriever = Retriever(persist_directory="../Phase_1/chroma_db")
    context, sources, last_updated = retriever.retrieve_context("exit load")
    print(f"\nContext:\n{context}")
    print(f"\nSources: {sources}")
    print(f"Last Updated: {last_updated}")
