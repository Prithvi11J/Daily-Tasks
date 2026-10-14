from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Reopen the FAISS index you just built.
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = FAISS.load_local(
    "data/faiss_index",
    embeddings,
    allow_dangerous_deserialization=True,
)

# Ask about a figure from the manually checked micro-irrigation table.
question = (
    "For 2026-27, what is the total subsidy including GST "
    "for Per Drop More Crop micro-irrigation?"
)

# Retrieve the four most relevant text chunks.
results = vector_store.similarity_search_with_score(question, k=4)

for number, (document, score) in enumerate(results, start=1):
    print(f"\n--- Result {number} ---")
    print("Source:", document.metadata.get("source", "Unknown"))
    print("Page:", document.metadata.get("page", "Unknown"))
    print("Distance:", score)
    print(document.page_content[:1200])