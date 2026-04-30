import sys
import os
import logging

# Add current directory to path to allow importing from runtime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from runtime.phase_2_safety.guardrails import apply_guardrails
from Phase_3.retriever import Retriever
from Phase_4.generator import Generator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_test():
    print("=" * 60)
    print("MUTUAL FUND RAG BOT - END-TO-END TEST")
    print("=" * 60)
    
    try:
        # Initialize Phase 3 and 4 components
        print("\n[System] Initializing Retriever (Phase 3)...")
        retriever = Retriever(persist_directory="Phase_1/chroma_db")
        
        print("[System] Initializing Generator (Phase 4)...")
        generator = Generator()
    except Exception as e:
        print(f"\n[System] Error during initialization: {e}")
        return

    test_queries = [
        "What is the exit load for HDFC Mid Cap fund?",  # Factual - should pass
        "Should I invest my money in HDFC ELSS?",       # Advice - should be blocked
        "My PAN is ABCDE1234F. What is the minimum SIP?", # PII - should be blocked
        "Who is the CEO of Google?"                      # Out of domain - should say "cannot find"
    ]

    for query in test_queries:
        print("\n" + "-" * 60)
        print(f"User Query: '{query}'")
        
        # Phase 2: Guardrails
        print("\n--- PHASE 2: Guardrails ---")
        guardrail_result = apply_guardrails(query)
        print(f"Passed: {guardrail_result['passed_guardrails']}")
        print(f"Intent/Status: {guardrail_result['intent']}")
        
        if not guardrail_result['safe_to_process']:
            print(f"\nResponse (Refusal):\n{guardrail_result['refusal_message']}")
            continue
            
        # Phase 3: Retrieval
        print("\n--- PHASE 3: Retrieval ---")
        context, sources, last_updated = retriever.retrieve_context(query)
        print(f"Sources Found: {len(sources)}")
        
        # Phase 4: Generation
        print("\n--- PHASE 4: Generation ---")
        final_answer = generator.generate_answer(query, context, sources, last_updated)
        
        print("\n*** FINAL LLM RESPONSE ***")
        print(final_answer)

if __name__ == "__main__":
    run_test()
