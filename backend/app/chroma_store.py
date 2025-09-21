from dotenv import load_dotenv
load_dotenv()

import chromadb
from langchain_chroma import Chroma

from sentence_transformers import SentenceTransformer

# Initialize the embedding model
embedding_model = SentenceTransformer("BAAI/bge-base-en-v1.5")


# Custom embedding wrapper class for LangChain compatibility
class SentenceTransformerEmbedder:
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        # Encode list of texts to list of embeddings
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text):
        # Encode a single query text
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


embedder = SentenceTransformerEmbedder(embedding_model)


# Initialize Chroma client and vector store
client = chromadb.Client()

vector_store = Chroma(
    collection_name="pdf_chunks",
    client=client,
    embedding_function=embedder,
    persist_directory="./chroma_persist"
)


def add_chunks_to_chroma(text_chunks, doc_id: str):
    texts = [chunk.page_content for chunk in text_chunks]
    metadatas = [{"page_number": chunk.metadata.get("page", -1)} for chunk in text_chunks]
    ids = [f"{doc_id}_{i}" for i in range(len(text_chunks))]

    # Add texts to the vector store
    vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    
    # Persist via the vector store instead of the client
    #vector_store.persist()  # Persist via the vector_store object


def semantic_search(query: str, n_results=5):
    return vector_store.similarity_search(query, k=n_results)
