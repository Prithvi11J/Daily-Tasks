"""Streamlit frontend for the Spotify architecture Hybrid RAG project.

Run from the project directory: python -m streamlit run app.py
Requires existing main.py, source PDF, ChromaDB, Neo4j and OpenAI credentials.
"""
import os
from pathlib import Path

import streamlit as st
from main import (
    CHROMA_PATH,
    create_vector_database,
    hybrid_rag,
    load_documents,
    split_documents,
)

# STEP 1: PAGE CONFIGURATION
st.set_page_config(
    page_title="Spotify Architecture | Hybrid RAG",
    page_icon="🔎",
    layout="centered",
)

# STEP 2: LOAD THE EXISTING VECTOR INDEX ONCE
@st.cache_resource(show_spinner="Loading the knowledge base...")
def get_vector_db():
    if not CHROMA_PATH.exists() or not any(CHROMA_PATH.iterdir()):
        raise FileNotFoundError(
            "ChromaDB index is missing. First run 'python main.py' locally "
            "to build the vector index."
        )
    documents = load_documents()
    chunks = split_documents(documents)
    db = create_vector_database(chunks)
    return db, len(documents), len(chunks)

# STEP 3: APP HEADER AND SIDEBAR
st.title("🔎 Spotify Architecture — Hybrid RAG")
st.caption("Ask questions about the 6-page Spotify-like web app architecture document.")

with st.sidebar:
    st.header("Knowledge sources")
    st.markdown("**Vector DB:** ChromaDB (semantic search)")
    st.markdown("**Knowledge Graph:** Neo4j AuraDB (relationships)")
    st.markdown("**Orchestration:** LangChain + OpenAI")
    st.divider()
    st.markdown("**How it works**")
    st.write("Question → vector search + graph search → combined context → answer")
    st.info("Answers are based on the supplied architecture PDF, not a live Spotify system.")
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# STEP 4: VERIFY CREDENTIALS WITHOUT DISPLAYING SECRETS
required = ["OPENAI_API_KEY", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]
missing = [name for name in required if not os.getenv(name)]
if missing:
    st.error("Missing environment variables: " + ", ".join(missing))
    st.stop()

try:
    vector_db, page_count, chunk_count = get_vector_db()
except Exception as exc:
    st.error(f"Unable to load knowledge base: {exc}")
    st.stop()

with st.sidebar:
    st.success(f"Source loaded: {page_count} pages / {chunk_count} chunks")

# STEP 5: CONVERSATION DISPLAY
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# STEP 6: USER QUESTION → EXISTING HYBRID RAG BACKEND
question = st.chat_input("Ask about services, databases, APIs, or architecture...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching ChromaDB and Neo4j..."):
            try:
                answer = hybrid_rag(question, vector_db)
            except Exception as exc:
                st.error(f"Question could not be answered: {exc}")
                st.stop()
        st.markdown(answer)
        st.caption("Check cited PDF pages for important decisions; AI answers can contain mistakes.")
    st.session_state.messages.append({"role": "assistant", "content": answer})

# UNDERSTAND THE IMPORTANT CODE
# st.cache_resource(): Reuses the loaded ChromaDB across Streamlit reruns.
# get_vector_db(): Opens the existing vector index; does not rebuild Neo4j.
# st.session_state.messages: Keeps chat messages in the current browser session.
# st.chat_input(): Accepts a new user question.
# hybrid_rag(): Uses BOTH ChromaDB and Neo4j, then calls the LLM.

# IMPORTANT NOTES
# 1. The source PDF must remain in data/.
# 2. Windows system environment variables supply credentials locally.
# 3. On the VPS, Docker Compose must supply the environment variables.
# 4. Each new question uses paid OpenAI embedding/chat API calls.
# 5. This app does not rebuild or modify the Neo4j knowledge graph.
# 6. Displayed conversation is temporary and is not stored in a database.
# 7. Do not expose this public demo without rate limits or access controls.
