import logging
from .chroma_client import get_collection

logger = logging.getLogger("VenomEngine")

async def purge_document(doc_id: str, company_id: str) -> bool:
    """Elimina todos los fragmentos de un documento de la base vectorial."""
    try:
        cid = str(company_id).strip()
        collection = get_collection()
        collection.delete(
            where={
                "$and": [
                    {"source": doc_id},
                    {"company_id": cid}
                ]
            }
        )
        logger.info(f"🗑️ Purga exitosa: {doc_id} para empresa {cid}")
        return True
    except Exception as e:
        logger.error(f"❌ Error en Purga: {e}")
        return False

async def process_and_index(file_bytes: bytes, filename: str, doc_id: str, company_id: str) -> bool:
    """Indexa un archivo en la base vectorial. Soporta varios formatos."""
    from app.services.file_processor import FileProcessor
    cid = str(company_id).strip()
    try:
        text = await FileProcessor.extract_text(file_bytes, filename)
        if not text or not text.strip():
            logger.warning(f"⚠️ No se pudo extraer texto de {filename}")
            return False

        chunk_size, overlap = 1000, 200
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]
        if not chunks:
            return False

        file_type = filename.split('.')[-1] if '.' in filename else 'unknown'
        metadatas = []
        for _ in chunks:
            metadatas.append({
                "source": doc_id,
                "company_id": cid,
                "filename": filename,
                "filetype": file_type
            })

        collection = get_collection()
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=[f"{doc_id}_{i}" for i in range(len(chunks))]
        )
        logger.info(f"✅ Indexado {len(chunks)} fragmentos de {filename} (doc_id={doc_id})")
        return True
    except Exception as e:
        logger.error(f"❌ Error en indexación de {filename}: {e}", exc_info=True)
        raise e

async def search_context(query: str, company_id: str) -> str:
    """Recupera fragmentos relevantes para la consulta desde la base vectorial."""
    try:
        cid = str(company_id).strip()
        collection = get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=5,
            where={"company_id": cid},
            include=["documents", "metadatas"]
        )
        if results['documents'] and results['documents'][0]:
            fragments = []
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                filename = meta.get('filename', 'documento desconocido')
                fragments.append(f"[Del archivo '{filename}']: {doc}")
            content = "\n\n".join(fragments)
            logger.info(f"🔍 RAG: {len(fragments)} fragmentos recuperados para {cid}")
            return content
        logger.warning(f"🔍 RAG: Sin contexto para {cid} en la consulta: {query[:50]}")
        return ""
    except Exception as e:
        logger.error(f"⚠️ Error en búsqueda RAG: {e}")
        return ""