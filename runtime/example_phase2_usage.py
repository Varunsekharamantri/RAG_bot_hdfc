"""
Example: How to use Phase 2 Guardrails in your RAG pipeline

This shows how to integrate the safety module with the data retrieval layer.
"""

from runtime.phase_2_safety import apply_guardrails

def process_user_query(user_input: str):
    """
    Main function to process user queries through all phases.
    
    Flow:
    1. Apply guardrails (Phase 2)
    2. If passed, retrieve relevant chunks from ChromaDB (Phase 3)
    3. Generate answer using LLM (Phase 4)
    4. Return to user
    """
    
    print(f"\nUser Query: {user_input}")
    print("-" * 70)
    
    # PHASE 2: Apply guardrails
    guardrails_result = apply_guardrails(user_input)
    
    if not guardrails_result['passed_guardrails']:
        # Query was blocked by guardrails
        print(f"Status: BLOCKED")
        print(f"Reason: {guardrails_result['reason']}")
        print(f"\nResponse to user:")
        print(guardrails_result['refusal_message'])
        return None  # Don't proceed to retrieval
    
    # Query passed guardrails
    print(f"Status: PASSED")
    print(f"Intent: {guardrails_result['intent']}")
    
    # PHASE 3: Retrieve relevant chunks (placeholder)
    print("\n[PHASE 3] Retrieving relevant chunks from ChromaDB...")
    # retrieved_chunks = vectorstore.similarity_search(user_input, k=3)
    
    # PHASE 4: Generate answer using LLM (placeholder)
    print("[PHASE 4] Generating answer using LLM...")
    # answer = llm.generate(user_input, retrieved_chunks)
    
    # Return result
    return {
        "query": user_input,
        "passed_safety": True,
        "intent": guardrails_result['intent'],
        # "answer": answer,
        # "sources": [chunk.metadata['source_url'] for chunk in retrieved_chunks]
    }


if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 2 GUARDRAILS - EXAMPLE USAGE")
    print("=" * 70)
    
    # Test scenarios
    test_queries = [
        # ✓ Factual queries that should pass
        ("What is the expense ratio of HDFC Mid Cap Fund?", "SHOULD PASS"),
        ("How do I download my mutual fund statement?", "SHOULD PASS"),
        
        # ✗ PII queries that should be blocked (no API calls)
        ("My Aadhaar is 1234-5678-9012. Can you help?", "SHOULD BLOCK - PII"),
        
        # ✗ Advice queries that should be blocked (API call)
        ("Should I buy HDFC Mid Cap Fund?", "SHOULD BLOCK - ADVICE"),
    ]
    
    for query, description in test_queries:
        print(f"\n\n{'='*70}")
        print(f"Test: {description}")
        print(f"{'='*70}")
        
        result = process_user_query(query)
        
        if result:
            print(f"\nResult: Query passed all checks, ready for Phase 3-4")
        else:
            print(f"\nResult: Query was blocked by guardrails")
    
    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)
