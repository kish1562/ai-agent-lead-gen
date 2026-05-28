"""
RAG Retriever — retrieves relevant context using vector embeddings.
Uses Azure AI Search with vector embeddings for contextual memory.
"""
import logging
from typing import List
from openai import OpenAI
from config.settings import settings

logger = logging.getLogger("RAGRetriever")


class RAGRetriever:
    """
    Retrieval-Augmented Generation retriever using vector embeddings.
    Searches a knowledge base for context relevant to lead qualification.
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model
        # In production, this connects to Azure AI Search / Cosmos DB
        self.search_endpoint = settings.azure_ai_search_endpoint
        self._init_vector_store()

    def _init_vector_store(self):
        """Initialize connection to the vector store."""
        logger.info(f"Initializing vector store: {self.search_endpoint}")
        # Placeholder: in production use azure-search-documents SDK
        self._knowledge_base = self._load_sample_kb()

    def embed_query(self, text: str) -> List[float]:
        """Generate an embedding vector for the query text."""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve the top-k most relevant context passages for a query.

        In production, performs vector similarity search against Azure AI Search.
        """
        logger.info(f"Retrieving context for: '{query[:50]}...' (top_k={top_k})")

        query_embedding = self.embed_query(query)
        results = self._vector_search(query_embedding, top_k)

        logger.info(f"Retrieved {len(results)} context passages")
        return results

    def _vector_search(self, query_embedding: List[float], top_k: int) -> List[str]:
        """
        Perform cosine-similarity search against the vector store.

        Production: replace with Azure AI Search vector query.
        """
        import math

        def cosine_similarity(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x * x for x in a))
            mag_b = math.sqrt(sum(y * y for y in b))
            return dot / (mag_a * mag_b) if mag_a and mag_b else 0

        scored = []
        for doc in self._knowledge_base:
            sim = cosine_similarity(query_embedding, doc["embedding"])
            scored.append((sim, doc["text"]))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [text for _, text in scored[:top_k]]

    def _load_sample_kb(self) -> List[dict]:
        """Load a sample knowledge base with pre-computed embeddings."""
        sample_docs = [
            "Enterprise clients in healthcare prioritize HIPAA compliance and data security.",
            "Mid-market SaaS companies typically have 3-6 month sales cycles.",
            "Leads mentioning 'urgent' or 'this quarter' indicate strong buying intent.",
            "Financial services leads require SOC 2 and audit-ready reporting capabilities.",
            "High-value leads usually have defined budgets above $50k annually.",
        ]
        # Pre-compute embeddings for sample docs
        kb = []
        for text in sample_docs:
            try:
                emb = self.embed_query(text)
                kb.append({"text": text, "embedding": emb})
            except Exception as e:
                logger.warning(f"Failed to embed sample doc: {e}")
        return kb
