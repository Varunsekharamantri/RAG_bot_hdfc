import os
import logging
from typing import List
from dotenv import load_dotenv
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
import pathlib
env_paths = [
    pathlib.Path(".env"),
    pathlib.Path(__file__).parent.parent / ".env",
]

for path in env_paths:
    if path.exists():
        load_dotenv(dotenv_path=path)
        logger.info(f"Loaded .env from: {path.resolve()}")
        break

GROQ_API_KEY = os.getenv("API_KEY")
if not GROQ_API_KEY:
    logger.warning("API_KEY not found in environment. Please ensure .env file exists.")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class Generator:
    """Handles the Generation phase (Phase 4) using the Groq API."""
    
    SYSTEM_PROMPT = (
        "You are a factual Mutual Fund assistant. Answer the user's question using ONLY the provided context. "
        "DO NOT mention the 'context', 'chunks', or 'the provided information' in your response. Answer naturally as if you simply know the facts. "
        "If the answer is not in the context, say 'I cannot find this information in the official documents.' "
        "Do NOT provide investment advice. Keep your answer to 3 sentences or less."
    )
    
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        """
        Initializes the Generator.
        
        Args:
            model_name: The Groq model to use.
        """
        self.model_name = model_name
        
    def generate_answer(self, query: str, context: str, sources: List[str], last_updated: str) -> str:
        """
        Generates an answer based on the context and appends a formatted citation.
        
        Args:
            query: The user's query.
            context: The assembled context from Phase 3.
            sources: List of source URLs.
            last_updated: The most recent update date.
            
        Returns:
            A formatted string containing the generated answer and citation footer.
        """
        if not client:
            return "Error: Groq API client is not initialized. Please check your API key."
            
        logger.info(f"Generating answer for query: '{query}'")
        
        if not context.strip():
            logger.warning("Context is empty. Falling back to default missing information response.")
            answer = "I cannot find this information in the official documents."
            return self._format_response(answer, sources, last_updated)
            
        try:
            prompt_content = f"Context:\n{context}\n\nUser Question: {query}"
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0.1,  # Low temperature for factual consistency
                max_tokens=150,   # Keep it short (3 sentences limit)
                top_p=0.9
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # Format the final response
            final_response = self._format_response(generated_text, sources, last_updated)
            return final_response
            
        except Exception as e:
            logger.error(f"Error during LLM generation: {e}")
            return f"An error occurred while generating the response: {str(e)}"
            
    def _format_response(self, answer: str, sources: List[str], last_updated: str) -> str:
        """
        Formats the final output with the citation footer.
        """
        if answer == "I cannot find this information in the official documents.":
            # No need to append sources if we didn't use them
            return answer
            
        footer_parts = []
        if sources:
            source_links = "\n".join([f"- {url}" for url in sources])
            footer_parts.append(f"Source(s):\n{source_links}")
        if last_updated:
            footer_parts.append(f"Last updated from sources: {last_updated}")
            
        footer = "\n".join(footer_parts)
        
        if footer:
            return f"{answer}\n\n{footer}"
        return answer

if __name__ == "__main__":
    # Simple test
    print("Testing Phase 4 Generator...")
    gen = Generator()
    test_query = "What is the exit load?"
    test_context = "--- Chunk 1 ---\nExpense Ratio & Exit Load Table\n| Item | Value |\n| Exit Load | 1% if redeemed within 1 year |"
    test_sources = ["https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"]
    
    print("\nResult:\n")
    print(gen.generate_answer(test_query, test_context, test_sources, "2026-04-28 10:00:00"))
