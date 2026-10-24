"""Hybrid RAG demo: Spotify architecture PDF + ChromaDB + Neo4j + OpenAI.

Usage:
    python main.py                 # Ask questions using existing indexes
    python main.py --build-graph   # Extract/store KG (paid LLM calls)
    python main.py --rebuild-vectors  # Recreate vector index (paid embeddings)
"""

import argparse
import os
import re
from pathlib import Path

from neo4j import GraphDatabase
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

# STEP 1: PROJECT CONFIGURATION
BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "data" / "spotify_web_app_architecture.pdf"
CHROMA_PATH = BASE_DIR / "chroma_db"
COLLECTION_NAME = "spotify_architecture"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"


def neo4j_config():
    """Read credentials only when a Neo4j operation is needed."""
    required = ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")
    return (os.environ["NEO4J_URI"], os.environ["NEO4J_USERNAME"],
            os.environ["NEO4J_PASSWORD"], os.getenv("NEO4J_DATABASE", "neo4j"))


# STEP 2: LOAD THE PDF
def load_documents():
    if not PDF_PATH.is_file():
        raise FileNotFoundError(f"Missing source PDF: {PDF_PATH}")
    documents = PyPDFLoader(str(PDF_PATH)).load()
    print(f"Pages loaded: {len(documents)}")
    return documents


# STEP 3: CHUNK DOCUMENTS
def split_documents(documents):
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=150
    ).split_documents(documents)
    print(f"Chunks created: {len(chunks)}")
    return chunks


# STEP 4: CREATE OR OPEN VECTOR DATABASE
def create_vector_database(chunks, rebuild=False):
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    db = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_PATH),
    )
    # Reuse existing embeddings for normal Q&A; never call embedding API to
    # index documents again unless explicitly asked to rebuild.
    stored = db.get(include=[])  # IDs only; avoids accessing private internals
    count = len(stored["ids"])
    if rebuild:
        if count:
            db.delete(ids=stored["ids"])
        db.add_documents(chunks, ids=[f"spotify_chunk_{i}" for i in range(len(chunks))])
        print("Vector index rebuilt.")
    elif count == 0:
        db.add_documents(chunks, ids=[f"spotify_chunk_{i}" for i in range(len(chunks))])
        print("Embeddings generated and stored in ChromaDB.")
    else:
        print("Existing ChromaDB collection loaded.")
        if count != len(chunks):
            print("Warning: PDF chunk count has changed. Run --rebuild-vectors to refresh.")
    print(f"Vectors stored: {len(db.get(include=[])['ids'])}")
    return db


# STEP 5: STRUCTURED KG EXTRACTION FORMAT
class Relationship(BaseModel):
    source: str = Field(description="Source entity")
    relation: str = Field(description="Relationship label, e.g. MANAGES")
    target: str = Field(description="Target entity")


class GraphData(BaseModel):
    relationships: list[Relationship] = Field(default_factory=list)


# STEP 6: EXTRACT GRAPH FACTS (ONLY WHEN REQUESTED)
def extract_graph_relationships(chunks):
    extractor = ChatOpenAI(model=CHAT_MODEL, temperature=0).with_structured_output(GraphData)
    relationships = []
    for index, chunk in enumerate(chunks, start=1):
        print(f"Extracting relationships: {index}/{len(chunks)}")
        result = extractor.invoke(
            "Extract technical entities and relationships from the Spotify-like "
            "application architecture text. Focus on services, databases, technologies, "
            "and responsibilities. Extract only relationships supported by the text. "
            "Use consistent, short entity names and uppercase relationship labels "
            "(e.g. USES, STORES, MANAGES, PROVIDES). Do not invent facts.\n\n"
            f"Document text:\n{chunk.page_content}"
        )
        for rel in result.relationships:
            source, target = rel.source.strip(), rel.target.strip()
            relation = re.sub(r"[^A-Z0-9_]", "_", rel.relation.upper().strip()).strip("_")
            if source and target and relation:
                relationships.append({
                    "source": source, "source_key": source.casefold(),
                    "relation": relation,
                    "target": target, "target_key": target.casefold(),
                    "page": chunk.metadata.get("page", 0) + 1,
                })
    print(f"Relationships extracted: {len(relationships)}")
    return relationships


# STEP 7: STORE GRAPH IN NEO4J (ONLY WHEN REQUESTED)
def save_graph_to_neo4j(relationships):
    uri, username, password, database = neo4j_config()
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j AuraDB.")
        if relationships:
            driver.execute_query(
                """
                UNWIND $relationships AS item
                MERGE (a:SpotifyEntity {key: item.source_key})
                ON CREATE SET a.name = item.source
                MERGE (b:SpotifyEntity {key: item.target_key})
                ON CREATE SET b.name = item.target
                MERGE (a)-[r:RELATES_TO {relation: item.relation}]->(b)
                ON CREATE SET r.source_page = item.page
                """,
                relationships=relationships, database_=database,
            )
        nodes, _, _ = driver.execute_query(
            "MATCH (n:SpotifyEntity) RETURN count(n) AS total", database_=database
        )
        edges, _, _ = driver.execute_query(
            "MATCH (:SpotifyEntity)-[r:RELATES_TO]->(:SpotifyEntity) "
            "RETURN count(r) AS total", database_=database
        )
        print(f"Neo4j graph: {nodes[0]['total']} nodes, {edges[0]['total']} relationships")


# STEP 8: RETRIEVE QUESTION-RELEVANT GRAPH RELATIONSHIPS
def retrieve_graph_facts(question):
    stopwords = {"what", "which", "where", "when", "does", "with", "from", "this",
                 "that", "have", "about", "using", "service", "services", "system",
                 "explain", "store", "stores", "data", "information"}
    terms = list(dict.fromkeys(
        word for word in re.findall(r"[a-z0-9]+", question.casefold())
        if len(word) >= 4 and word not in stopwords
    ))
    if not terms:
        return []
    uri, username, password, database = neo4j_config()
    query = """
    MATCH (a:SpotifyEntity)-[r:RELATES_TO]->(b:SpotifyEntity)
    WHERE any(term IN $terms WHERE
        toLower(a.name) CONTAINS term OR toLower(b.name) CONTAINS term)
    RETURN a.name AS source, r.relation AS relation,
           b.name AS target, r.source_page AS page
    LIMIT 20
    """
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        records, _, _ = driver.execute_query(
            query, terms=terms, database_=database, routing_="r"
        )
    return [
        f"{row['source']} -> {row['relation']} -> {row['target']} "
        f"(PDF page {row['page']})"
        for row in records
    ]


# STEP 9: HYBRID RETRIEVAL AND LLM ANSWERING
def hybrid_rag(question, vector_db):
    vector_results = vector_db.similarity_search(question, k=3)
    graph_facts = retrieve_graph_facts(question)
    vector_context = "\n\n".join(
        f"[PDF page {doc.metadata.get('page', 0) + 1}]\n{doc.page_content}"
        for doc in vector_results
    )
    graph_context = "\n".join(graph_facts) if graph_facts else "No matching graph facts."
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You answer technical architecture questions using ONLY the supplied "
         "PDF passages and knowledge graph facts. Combine both where useful. "
         "Prefer direct PDF passages if a graph fact is ambiguous or conflicts. "
         "Cite PDF page numbers for claims when available. "
         "If the supplied evidence does not support an answer, say so. "
         "Do not invent details."),
        ("human", "PDF Passages:\n{vector_context}\n\n"
         "Knowledge Graph Facts:\n{graph_context}\n\nQuestion: {question}"),
    ])
    response = (prompt | ChatOpenAI(model=CHAT_MODEL, temperature=0)).invoke({
        "question": question,
        "vector_context": vector_context,
        "graph_context": graph_context,
    })
    print(f"\nVector chunks retrieved: {len(vector_results)}")
    print(f"Graph relationships retrieved: {len(graph_facts)}")
    return response.content


# STEP 10: MAIN ENTRY POINT
def main():
    parser = argparse.ArgumentParser(description="Spotify Architecture Hybrid RAG")
    parser.add_argument("--build-graph", action="store_true",
                        help="Run LLM extraction and store Neo4j relationships")
    parser.add_argument("--rebuild-vectors", action="store_true",
                        help="Recreate ChromaDB embeddings from the current PDF")
    args = parser.parse_args()

    documents = load_documents()
    chunks = split_documents(documents)
    vector_db = create_vector_database(chunks, rebuild=args.rebuild_vectors)

    if args.build_graph:
        relationships = extract_graph_relationships(chunks)
        save_graph_to_neo4j(relationships)
        print("\nGraph build complete.")
        return

    print("\nHybrid RAG ready! Type 'exit' to stop.")
    while True:
        try:
            question = input("\nAsk a question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHybrid RAG session ended.")
            break
        if question.casefold() in {"exit", "quit"}:
            print("Hybrid RAG session ended.")
            break
        if not question:
            continue
        try:
            print("\nAnswer:", hybrid_rag(question, vector_db))
        except Exception as error:
            print(f"Could not answer question: {error}")


if __name__ == "__main__":
    main()

# UNDERSTAND THE IMPORTANT CODE
# load_documents(): Reads the six-page PDF and preserves page metadata.
# split_documents(): Creates overlapping text chunks for search.
# create_vector_database(): Uses or creates Chroma embeddings, avoiding re-indexing.
# --build-graph: Explicitly invokes the LLM extractor and saves Neo4j data.
# retrieve_graph_facts(): Uses a parameterized read-only Cypher graph query.
# hybrid_rag(): Combines three vector hits with up to 20 graph relationships.
# prompt | llm: LangChain sends the combined context to the chat model.
# input(): Keeps the console chat running until you enter 'exit'.

# IMPORTANT NOTES
# 1. Credentials come from system environment variables; no .env file required.
# 2. Standard `python main.py` does NOT rebuild the Neo4j graph.
# 3. Building the graph and rebuilding embeddings use paid OpenAI calls.
# 4. Normal Q&A uses OpenAI for query embeddings and generating each answer.
# 5. Graph retrieval uses keyword matching; it can miss synonyms or multi-hop links.
# 6. `--rebuild-vectors` refreshes chunks after changing the source PDF.
# 7. Existing unrelated Neo4j nodes are untouched (SpotifyEntity label only).
# 8. LLM-extracted graph relationships may be wrong; PDF text is preferred.
# 9. PDF citations are based on retrieved page metadata, not independently verified.
