import chromadb
from chromadb.utils import embedding_functions

# Configuración de Chroma DB (persistente)
chroma_client = chromadb.PersistentClient(path="./venom_knowledge")
default_ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name="company_knowledge",
    embedding_function=default_ef
)

def get_collection():
    """Devuelve la colección de ChromaDB."""
    return collection