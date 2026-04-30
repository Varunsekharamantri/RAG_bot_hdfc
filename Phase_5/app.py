import sys
import os
import streamlit as st

# Add the project root to the sys.path so we can import from other phases
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from runtime.phase_2_safety.guardrails import apply_guardrails
from Phase_3.retriever import Retriever
from Phase_4.generator import Generator

# Page Config
st.set_page_config(
    page_title="HDFC Mutual Fund Assistant",
    page_icon="📈",
    layout="centered"
)

# Initialize Backend Components in Session State to avoid reloading
@st.cache_resource
def load_components():
    retriever = Retriever(persist_directory=os.path.join(project_root, "Phase_1", "chroma_db"))
    generator = Generator()
    return retriever, generator

try:
    retriever, generator = load_components()
except Exception as e:
    st.error(f"Failed to load backend components: {e}")
    st.stop()

# Header & Welcome Line
st.title("📈 HDFC Mutual Fund FAQ Assistant")
st.markdown("### *Facts-only. No investment advice.*")
st.markdown("Ask factual questions about selected HDFC mutual fund schemes.")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Quick example questions
st.markdown("#### Try asking:")
cols = st.columns(3)
example_questions = [
    "What is the exit load of HDFC Mid Cap Fund?",
    "What is the minimum SIP amount?",
    "How do I download my capital gains statement?"
]

# When an example is clicked, it becomes the query
for i, col in enumerate(cols):
    if col.button(example_questions[i], key=f"ex_{i}"):
        st.session_state.example_query = example_questions[i]

query = st.chat_input("Ask a question...")

# Use either typed query or clicked example
if "example_query" in st.session_state:
    query = st.session_state.example_query
    del st.session_state.example_query

if query:
    # Display user message in chat message container
    st.chat_message("user").markdown(query)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("assistant"):
        with st.spinner("Analyzing query..."):
            # PHASE 2: Guardrails
            guardrail_result = apply_guardrails(query)
            
            if not guardrail_result['safe_to_process']:
                st.markdown(guardrail_result['refusal_message'])
                st.session_state.messages.append({"role": "assistant", "content": guardrail_result['refusal_message']})
            else:
                # PHASE 3: Retrieval
                with st.spinner("Retrieving information..."):
                    context, sources, last_updated = retriever.retrieve_context(query)
                    
                # PHASE 4: Generation
                with st.spinner("Generating answer..."):
                    final_answer = generator.generate_answer(query, context, sources, last_updated)
                
                st.markdown(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
