# Phase 2: Guardrails & Query Pre-Processing Implementation

## Overview
Successfully implemented a two-layer safety system that:
1. **Local PII Detection** (No API calls) - Blocks sensitive data immediately
2. **Intent Classification** (Groq API) - Classifies queries as FACT or ADVICE

---

## Architecture

### Layer 1: Local PII Detection (No Groq Calls)
Detects and immediately blocks queries containing:
- **PAN**: Indian Tax ID (5 letters + 4 digits + 1 letter)
- **Aadhaar**: 12-digit ID (supports spaces/dashes)
- **Email**: Standard email patterns
- **Phone**: Indian mobile numbers (10 digits starting with 6-9)
- **OTP**: 4-6 digit codes

**Key Benefit**: Blocks PII instantly without consuming Groq API quota.

### Layer 2: Intent Classification (Groq API Call)
Only called if PII check passes. Classifies query as:
- **FACT**: Factual question about mutual funds → Proceed to retrieval
- **ADVICE**: Opinion/recommendation question → Return AMFI educational link

**Efficiency**: Very short system prompt (saves tokens), `max_tokens=10`, `temperature=0`.

---

## Test Results

### PII Detection Tests (All Passed - No API Calls Made)
✅ **PAN Detection**: "My PAN is ABCDE1234F" → BLOCKED immediately  
✅ **Aadhaar Detection**: "My Aadhaar is 1234-5678-9012" → BLOCKED immediately  
✅ **Email Detection**: "Email me at test@example.com" → BLOCKED immediately  
✅ **Phone Detection**: "Call me at 9876543210" → BLOCKED immediately  

### Intent Classification Test
- Uses Groq API for classification
- Current Groq Free Plan models available may vary
- Fallback error handling for rate limits

---

## Key Implementation Features

### 1. Efficient API Usage
```python
# System prompt is minimal to save tokens
CLASSIFICATION_SYSTEM_PROMPT = """You are a query classifier. Classify as 'FACT' or 'ADVICE'..."""

# Call parameters optimized for speed
temperature=0         # Deterministic
max_tokens=10         # Very short response
top_p=0.1            # Stricter sampling
```

### 2. Error Handling
- **RateLimitError**: Graceful message when Groq rate limit hit
- **APIError**: Generic service error message
- **Model Fallback**: Error handling mentions checking console.groq.com for available models

### 3. Environment Configuration
- Reads `.env` file with UTF-8-BOM handling
- Fallback to manual environment variable parsing if needed
- Secure API key loading from `API_KEY` environment variable

### 4. Refusal Messages
When PII or ADVICE is detected, users receive clear, friendly messages:
- 🔒 PII Refusal: "For your security, I cannot process..."
- 📚 Advice Refusal: "I provide facts only — no investment advice" + AMFI education link

---

## File Structure
```
RAG Chatbot/
├── runtime/
│   └── phase_2_safety/
│       ├── guardrails.py         # Main safety module
│       ├── __init__.py           # Package exports
│       └── README.md             # This file
├── requirements.txt               # Includes groq, python-dotenv
└── .env                          # API_KEY=your_groq_api_key
```

---

## Usage

### Import and Use
```python
from runtime.phase_2_safety import apply_guardrails

result = apply_guardrails("What is the expense ratio?")
print(result['passed_guardrails'])  # True/False
print(result['intent'])             # "FACT", "ADVICE", "PII_DETECTED", "ERROR"
print(result['refusal_message'])    # Message to show user if blocked
print(result['safe_to_process'])    # True if should proceed to retrieval
```

### Result Dictionary
```python
{
    "passed_guardrails": bool,
    "reason": str,
    "intent": str,
    "refusal_message": str,
    "safe_to_process": bool
}
```

---

## API Efficiency

### Token Usage Breakdown
- **PII Check**: 0 tokens (local regex)
- **Intent Classification**: ~50-100 tokens (short prompt + short response)
- **Per Query Cost**: ~50-100 tokens (minimal)

### Groq Free Plan Compatibility
- Minimal API calls (only for intent classification)
- Short prompts save tokens
- Deterministic classification reduces retries
- Recommended for <100 queries/day on free plan

---

## Next Steps (Phase 3: Retrieval)
- Vector similarity search using ChromaDB
- Retrieve top K chunks based on user query
- Extract source URLs for citations

---

## Notes
- Both PII detection and intent classification use UTF-8 compatible encoding
- Regex patterns are optimized for Indian financial documents
- All refusal messages follow AMFI guidelines (facts-only, no advice)
- Error handling includes rate-limit backoff messages
