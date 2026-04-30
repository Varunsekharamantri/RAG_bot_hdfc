from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
import logging
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from runtime.phase_2_safety.guardrails import apply_guardrails
from Phase_3.retriever import Retriever
from Phase_4.generator import Generator

app = FastAPI(title="HDFC Mutual Fund Assistant API")

# Add CORS to allow the frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Backend Components
try:
    retriever = Retriever(persist_directory=os.path.join(project_root, "Phase_1", "chroma_db"))
    generator = Generator()
    logger.info("Backend components initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    # We will raise an error if someone calls the endpoint while it's broken
    retriever, generator = None, None

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    type: str # 'factual', 'refusal', 'error'
    text: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    query = request.query
    
    if not retriever or not generator:
        raise HTTPException(status_code=500, detail="Backend components not initialized properly.")
        
    logger.info(f"Received query: {query}")
    
    # PHASE 2: Guardrails
    try:
        guardrail_result = apply_guardrails(query)
    except Exception as e:
        logger.error(f"Guardrail error: {e}")
        return ChatResponse(type="error", text="An error occurred while processing guardrails.")

    if not guardrail_result['safe_to_process']:
        return ChatResponse(type="refusal", text=guardrail_result['refusal_message'])
        
    # PHASE 3: Retrieval
    try:
        context, sources, last_updated = retriever.retrieve_context(query)
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return ChatResponse(type="error", text="An error occurred while retrieving data.")

    # PHASE 4: Generation
    try:
        final_answer = generator.generate_answer(query, context, sources, last_updated)
        return ChatResponse(type="factual", text=final_answer)
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return ChatResponse(type="error", text="An error occurred while generating the answer.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
