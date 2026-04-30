# Phase 2: Guardrails & Query Pre-Processing

## What Was Implemented

### ✅ Local PII Filter (Regex-Based, No API Calls)
Detects and **immediately blocks** queries containing:
- **PAN**: Indian tax ID (Pattern: 5 letters + 4 digits + 1 letter)
- **Aadhaar**: 12-digit ID (Pattern: 12 consecutive digits with optional spaces/dashes)
- **Email**: Standard email addresses
- **Phone**: Indian mobile numbers (10 digits starting with 6-9)
- **OTP**: 4-6 digit codes

**Crucial**: Zero API calls for PII — blocks instantly before any data is sent to Groq.

---

### ✅ Efficient Intent Classification (Groq API)
Only called if PII check passes.

**System Prompt** (Optimized for Groq Free Plan):
```
You are a query classifier. Classify as either:
1. FACT - Factual question about mutual funds
2. ADVICE - Opinion/advice question
Respond with ONLY "FACT" or "ADVICE"
```

**Parameters**:
- `temperature=0` — Deterministic classification
- `max_tokens=10` — Very short response  
- `top_p=0.1` — Stricter sampling

**Result**:
- **FACT** → Return True, proceed to retrieval
- **ADVICE** → Return AMFI educational link refusal message

---

### ✅ Refusal Logic with AMFI Links
```python
if intent == "ADVICE":
    return "I provide **facts only** — no investment advice. 📚\n\n
            For personalized advice, consult a certified financial advisor.\n\n
            Learn more: https://www.amfiindia.com/investor-education"
```

---

### ✅ Rate Limit Error Handling
```python
try:
    # API call to Groq
    message = client.chat.completions.create(...)
    
except RateLimitError:
    return "⏱️ We're experiencing high traffic. Please try again in a moment."

except APIError:
    return "⚠️ We encountered a temporary service issue. Please try again shortly."
```

---

## File Structure Created

```
runtime/phase_2_safety/
├── guardrails.py           # Main module with PII detection + intent classification
├── __init__.py             # Package exports (apply_guardrails, PIIDetector, IntentClassifier)
└── README.md              # Detailed documentation
```

---

## How to Use

### Step 1: Import
```python
from runtime.phase_2_safety import apply_guardrails
```

### Step 2: Apply Guardrails
```python
result = apply_guardrails("What is the expense ratio?")
```

### Step 3: Check Result
```python
if result['passed_guardrails']:
    # Safe to proceed to Phase 3 (retrieval)
    retrieve_and_answer(query)
else:
    # Block query and show refusal message
    print(result['refusal_message'])
```

### Result Dictionary
```python
{
    "passed_guardrails": True/False,
    "reason": "Query is safe and factual",
    "intent": "FACT" | "ADVICE" | "PII_DETECTED" | "ERROR",
    "refusal_message": "...",
    "safe_to_process": True/False
}
```

---

## Test Results Summary

### PII Detection Tests ✅
```
[PASS] PAN Detection → Blocked "ABCDE1234F"
[PASS] Aadhaar Detection → Blocked "1234-5678-9012"
[PASS] Email Detection → Blocked "test@example.com"
[PASS] Phone Detection → Blocked "9876543210"
```
**No API calls made for any PII test** ✨

### Intent Classification Test ✅
- Successfully calls Groq API
- Classifies factual vs. advice queries
- Error handling for rate limits and API failures

---

## Efficiency Metrics

| Scenario | API Calls | Tokens Used |
|----------|-----------|-------------|
| Query with PII | 0 | 0 |
| Factual query | 1 | ~50-100 |
| Advice query | 1 | ~50-100 |

**Monthly Budget (Groq Free Plan)**:
- ~3000 queries × 100 tokens = 300K tokens ✅ (Well within free tier)

---

## Key Features

1. **Security First**: PII blocked locally, never sent to API
2. **API Efficient**: Only 1 Groq call per non-PII query
3. **Token Efficient**: Minimal prompt + deterministic classification
4. **User Friendly**: Clear refusal messages with educational links
5. **Error Resilient**: Handles rate limits and API errors gracefully
6. **AMFI Compliant**: Follows facts-only, no-advice guidelines

---

## Example Queries

| Query | Result | Reason |
|-------|--------|--------|
| "What is the exit load?" | ✅ PASS | Factual |
| "Should I buy this fund?" | ❌ BLOCK | ADVICE |
| "My PAN is..." | ❌ BLOCK | PII (no API call) |
| "Aadhaar 1234-5678-9012" | ❌ BLOCK | PII (no API call) |

---

## Integration with Other Phases

```
User Query
    ↓
Phase 1: Data Ingestion (already done - ChromaDB populated)
    ↓
Phase 2: Guardrails ← YOU ARE HERE
    ├─ PII Check (local, no API)
    └─ Intent Check (Groq API)
    ↓
Phase 3: Retrieval (ChromaDB similarity search)
    ↓
Phase 4: Generation (LLM answer with citations)
    ↓
Phase 5: UI/Deployment (Streamlit app)
```

---

## Next: Phase 3 (Retrieval)
Ready to implement similarity search using ChromaDB to retrieve relevant chunks based on user query.
