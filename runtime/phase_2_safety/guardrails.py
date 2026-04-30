"""
Phase 2: Guardrails & Query Pre-Processing
Efficient safety layer that checks for PII locally (no API calls)
and only calls Groq for intent classification when needed.
"""

import re
import os
import logging
from typing import Dict, Tuple
from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables - try multiple paths
import pathlib
env_paths = [
    # Try relative to current working directory
    pathlib.Path(".env"),
    # Try relative to script location (up 3 levels)
    pathlib.Path(__file__).parent.parent.parent / ".env",
]

env_path = None
for path in env_paths:
    if path.exists():
        env_path = path
        break

if env_path:
    # Load with error handling for BOM
    try:
        load_dotenv(dotenv_path=env_path)
    except Exception as e:
        logger.debug(f"load_dotenv had issue: {e}")
    
    # Also manually parse to ensure we get the value
    with open(env_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and line.startswith('API_KEY'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                os.environ[key] = value
    
    logger.info(f"Loaded .env from: {env_path.resolve()}")
else:
    logger.warning("No .env file found. Trying to use environment variables directly...")

# Initialize Groq client
GROQ_API_KEY = os.getenv("API_KEY")
if not GROQ_API_KEY:
    raise ValueError(
        f"API_KEY not found in environment. Tried paths: {[str(p) for p in env_paths]}\n"
        "Please ensure .env file exists with API_KEY=your_groq_api_key"
    )

client = Groq(api_key=GROQ_API_KEY)

# ============================================================================
# PART 1: LOCAL PII DETECTION (NO API CALLS)
# ============================================================================

class PIIDetector:
    """Detects PII in user queries without making any API calls."""
    
    # PAN pattern: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)
    PAN_PATTERN = re.compile(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', re.IGNORECASE)
    
    # Aadhaar pattern: 12 consecutive digits (can be with or without spaces/dashes)
    AADHAAR_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b|\b\d{12}\b')
    
    # Email pattern: standard email regex
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    # Phone pattern: Indian phone (10 digits)
    PHONE_PATTERN = re.compile(r'\b[6-9]\d{9}\b')
    
    # OTP pattern: 4-6 digit codes
    OTP_PATTERN = re.compile(r'\b\d{4,6}\b')
    
    @staticmethod
    def detect_pii(query: str) -> Tuple[bool, str]:
        """
        Detect PII in the query.
        
        Returns:
            (has_pii: bool, pii_type: str)
        """
        if not query or not isinstance(query, str):
            return False, ""
        
        # Check for PAN
        if PIIDetector.PAN_PATTERN.search(query):
            return True, "PAN"
        
        # Check for Aadhaar
        if PIIDetector.AADHAAR_PATTERN.search(query):
            return True, "Aadhaar"
        
        # Check for Email
        if PIIDetector.EMAIL_PATTERN.search(query):
            return True, "Email"
        
        # Check for Phone
        if PIIDetector.PHONE_PATTERN.search(query):
            return True, "Phone"
        
        return False, ""


# ============================================================================
# PART 2: INTENT CLASSIFICATION (USES GROQ API)
# ============================================================================

class IntentClassifier:
    """Classifies user intent as FACT or ADVICE using Groq."""
    
    # AMFI Educational Links (for refusals)
    AMFI_LINKS = {
        "investor_education": "https://www.amfiindia.com/investor-education",
        "mf_basics": "https://www.amfiindia.com/learn-investing/articles",
        "scheme_selection": "https://www.amfiindia.com/investor-education/know-your-schemes"
    }
    
    # System prompt optimized for Groq (short to save tokens)
    CLASSIFICATION_SYSTEM_PROMPT = """You are a query classifier. Classify the user's query as either:
1. FACT - A factual question about mutual fund schemes (e.g., "What is the expense ratio?", "What is the exit load?")
2. ADVICE - An opinion/advice question (e.g., "Should I buy this fund?", "Is this a good investment?")

Respond with ONLY "FACT" or "ADVICE", nothing else."""
    
    @staticmethod
    def classify_intent(query: str) -> Tuple[str, str]:
        """
        Classify query intent using Groq.
        Uses gemma-7b-it (available on Groq Free Plan)
        
        Returns:
            (intent: str, response: str)
            - intent: "FACT", "ADVICE", or "ERROR"
            - response: Educational message if ADVICE, empty if FACT, error msg if ERROR
        """
        try:
            logger.info(f"Classifying query intent via Groq (llama-3.1-8b-instant)...")
            
            message = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": IntentClassifier.CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                temperature=0,  # Deterministic classification
                max_tokens=10,  # Very short response
                top_p=0.1  # Stricter sampling for consistency
            )
            
            # Extract the classification
            intent = message.choices[0].message.content.strip().upper()
            
            # Validate response
            if intent not in ["FACT", "ADVICE"]:
                logger.warning(f"Unexpected intent response: {intent}. Defaulting to FACT.")
                intent = "FACT"
            
            if intent == "ADVICE":
                refusal_message = (
                    "I provide **facts only** — no investment advice. 📚\n\n"
                    "I cannot tell you whether to buy, sell, or hold a fund. "
                    "For personalized advice, please consult a certified financial advisor.\n\n"
                    "**Learn more:**\n"
                    f"[AMFI Investor Education](https://www.amfiindia.com/investor-education)"
                )
                return "ADVICE", refusal_message
            
            return "FACT", ""
            
        except RateLimitError as e:
            logger.error(f"Groq Rate Limit Error: {e}")
            error_msg = (
                "⏱️ We're experiencing high traffic. Please try again in a moment.\n"
                "This is a temporary rate limit — not an issue with your query."
            )
            return "ERROR", error_msg
        
        except APIError as e:
            logger.error(f"Groq API Error: {e}")
            error_msg = (
                "⚠️ We encountered a temporary service issue. Please try again shortly."
            )
            return "ERROR", error_msg
        
        except Exception as e:
            logger.error(f"Unexpected error during intent classification: {e}")
            error_msg = f"An unexpected error occurred: {str(e)}"
            return "ERROR", error_msg


# ============================================================================
# PART 3: MAIN GUARDRAILS FUNCTION
# ============================================================================

def apply_guardrails(user_query: str) -> Dict[str, any]:
    """
    Apply all safety checks to the user query.
    
    Args:
        user_query (str): The user's input query
    
    Returns:
        {
            "passed_guardrails": bool,
            "reason": str (reason if it failed),
            "intent": str ("FACT", "ADVICE", "PII_DETECTED", "ERROR"),
            "refusal_message": str (message to return to user if blocked),
            "safe_to_process": bool (whether to proceed to retrieval)
        }
    """
    result = {
        "passed_guardrails": True,
        "reason": "",
        "intent": "",
        "refusal_message": "",
        "safe_to_process": False
    }
    
    # Step 1: Check for PII (NO API CALL)
    has_pii, pii_type = PIIDetector.detect_pii(user_query)
    if has_pii:
        result["passed_guardrails"] = False
        result["reason"] = f"PII Detected: {pii_type}"
        result["intent"] = "PII_DETECTED"
        result["refusal_message"] = (
            f"🔒 **For your security**, I cannot process queries containing {pii_type.lower()} data.\n\n"
            "Please remove any sensitive information and ask again.\n\n"
            "**What I cannot accept:**\n"
            "• PAN numbers\n"
            "• Aadhaar numbers\n"
            "• Phone numbers\n"
            "• Email addresses\n"
            "• OTPs or account numbers"
        )
        logger.warning(f"PII detected in query. Type: {pii_type}")
        return result
    
    # Step 2: Classify intent (CALLS GROQ API ONLY IF NO PII)
    intent, refusal_msg = IntentClassifier.classify_intent(user_query)
    result["intent"] = intent
    
    if intent == "ERROR":
        result["passed_guardrails"] = False
        result["reason"] = "Groq API Error"
        result["refusal_message"] = refusal_msg
        return result
    
    if intent == "ADVICE":
        result["passed_guardrails"] = False
        result["reason"] = "Query is advice-seeking, not factual"
        result["refusal_message"] = refusal_msg
        logger.info("Query classified as ADVICE (opinion question)")
        return result
    
    # Step 3: Query passed all checks
    result["passed_guardrails"] = True
    result["reason"] = "Query is safe and factual"
    result["intent"] = "FACT"
    result["safe_to_process"] = True
    logger.info("Query passed all guardrails checks")
    
    return result


# ============================================================================
# TESTING / DEMO
# ============================================================================

if __name__ == "__main__":
    # Test cases
    test_queries = [
        # Safe factual queries
        ("What is the expense ratio of HDFC Mid Cap Fund?", "[PASS] Factual question"),
        ("What is the minimum SIP amount for ELSS funds?", "[PASS] Factual question"),
        ("How do I download my mutual fund statement?", "[PASS] Factual question"),
        
        # PII Detection (should not call API)
        ("My PAN is ABCDE1234F, can you help?", "[BLOCK] PII (PAN)"),
        ("My Aadhaar is 1234-5678-9012", "[BLOCK] PII (Aadhaar)"),
        ("Email me at test@example.com", "[BLOCK] PII (Email)"),
        ("Call me at 9876543210", "[BLOCK] PII (Phone)"),
        
        # Advice queries (should call API, but be blocked)
        ("Should I buy HDFC Mid Cap Fund?", "[BLOCK] ADVICE"),
        ("Is this a good investment?", "[BLOCK] ADVICE"),
        ("Which fund should I invest in?", "[BLOCK] ADVICE"),
    ]
    
    print("=" * 70)
    print("PHASE 2 GUARDRAILS - TESTING")
    print("=" * 70)
    
    for query, expected in test_queries:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        
        result = apply_guardrails(query)
        
        print(f"Result:")
        print(f"  Passed: {result['passed_guardrails']}")
        print(f"  Intent: {result['intent']}")
        print(f"  Reason: {result['reason']}")
        
        if result['refusal_message']:
            print(f"  Response:\n{result['refusal_message']}")
        
        print("-" * 70)
    
    print("\n✅ Guardrails testing completed!")
