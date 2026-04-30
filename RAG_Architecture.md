# Phase-Wise RAG Architecture: Mutual Fund FAQ Assistant

Based on the provided problem statement, here is a detailed, phase-wise architecture for the facts-only Mutual Fund FAQ assistant. The architecture strictly adheres to the constraints (public sources only, no advice, no PII, exact citations).

---

## Phase 1: Data Curation & Ingestion (The Knowledge Base)
This phase focuses on building a small, highly curated corpus of official mutual fund documents.

*   **Step 1: Scoping & URL Collection**
    *   **AMC:** HDFC Mutual Fund.
    *   **Schemes (Groww URLs):**
        *   https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
        *   https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
        *   https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth
        *   https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
        *   https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth
    *   *Deliverable Output:* Maintain a `sources.csv` containing `URL`, `Document Type`, and `Scheme Name`.
*   **Step 2: Automated Scraping Service & Scheduler**
    *   **Scheduler (GitHub Actions):** A cron job configured to run every day at **9:15 AM IST** (`cron: '45 3 * * *'`). This ensures the knowledge base is updated daily with the latest scheme data.
    *   **Scraping Service:** A Python script triggered by the scheduler that fetches the latest HTML content directly from the defined Groww URLs. No PDFs will be used.
*   **Step 3: Chunking & Embedding Pipeline**
    *   *(See the separate `Data_Processing_Architecture.md` document for detailed architecture on chunking, metadata tagging, and embedding).*
    *   The scraped data is passed to the chunking module, embedded, and upserted into the Vector Database (e.g., ChromaDB, FAISS), overwriting or updating the previous day's data.

---

## Phase 2: Guardrails & Query Pre-Processing (Safety Layer)
Before a query even reaches the retrieval phase, it must pass strict safety checks.

*   **Step 1: PII Detection**
    *   Implement a regex/presidio-based filter to detect and block PAN, Aadhaar, account numbers, emails, phone numbers, and OTPs.
    *   *Action:* If PII is found, return an immediate refusal message.
*   **Step 2: Intent Classification (Advice vs. Fact)**
    *   Use a lightweight classifier or an LLM call to classify the query intent.
    *   *Advice/Opinion (e.g., "Should I buy?", "Is this good?"):* Block the query and return a polite, facts-only refusal message with an educational link (e.g., AMFI Investor Education).
    *   *Performance/Returns (e.g., "What will be my return?"):* Block calculation. Direct the user to the official factsheet link.
    *   *Fact (e.g., "What is the exit load?"):* Proceed to Phase 3.

---

## Phase 3: Retrieval Strategy
This phase focuses on accurately fetching the right information from the vector database.

*   **Step 1: Vector Search**
    *   Convert the user's query into an embedding.
    *   Perform a similarity search (Cosine Similarity) to retrieve the top *k* (e.g., k=3 to 5) most relevant chunks from the Vector DB.
*   **Step 2: Context Assembly**
    *   Extract the `text` and `source_url` from the retrieved chunks to build the context for the LLM.

---

## Phase 4: Generation & Formatting (LLM Processing)
This phase relies on strict prompting to ensure the LLM outputs concise, factual answers with citations.

*   **Step 1: The System Prompt**
    *   Design a strict prompt template:
        > *"You are a factual Mutual Fund assistant. Answer the user's question using ONLY the provided context. If the answer is not in the context, say 'I cannot find this information in the official documents.' Do NOT provide investment advice. Keep your answer to 3 sentences or less."*
*   **Step 2: Output Generation**
    *   Pass the System Prompt, Retrieved Context, and User Query to the LLM (e.g., GPT-4o-mini, Claude 3 Haiku).
*   **Step 3: Citation & Formatting Append**
    *   Extract the `source_url` from the chunk that the LLM used to generate the answer.
    *   Append the required footer to the generated answer:
        > *"[Answer text...]*
        > *Source: [Link]*
        > *Last updated from sources: [Date/Timestamp]"*

---

## Phase 5: Application UI & Deployment
Building the "Tiny UI" and ensuring all deliverables are met.

*   **Step 1: Frontend Development**
    *   Build a simple UI using **Streamlit** or **Gradio** (or basic HTML/JS if preferred).
    *   Include a prominent welcome line: *"Facts-only. No investment advice."*
    *   Provide 3 clickable example questions (e.g., "What is the exit load of [Scheme]?", "What is the minimum SIP?", "How do I download my capital gains statement?").
*   **Step 2: Deliverable Packaging**
    *   **Codebase:** Assemble app logic, vector DB creation script, and requirements.txt.
    *   **README.md:** Include setup steps, the scope (AMC + schemes), and known limitations.
    *   **Sample Q&A:** Generate a `sample_qa.md` file with 5-10 tested queries showing answers, links, and how the assistant handles refusal.
    *   **Recording/Hosting:** Deploy to Streamlit Community Cloud/HuggingFace Spaces OR record a ≤3-min demo video showing the UI, factual Q&A, and a refusal scenario.
