import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.models import Account
from mcp_server.utils.db import get_db_session

# Global model instance to avoid reloading on every call
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def build_index():
    """
    Build a FAISS index from the current chart of accounts.
    Returns:
        index: FAISS index
        account_ids: List of account IDs matching the index order
    """
    model = get_model()
    
    with get_db_session() as session:
        accounts = session.query(Account).filter(Account.is_active == True).all()
        # Extract IDs to avoid session-bound object issues later
        account_ids = [acc.id for acc in accounts]
        
        if not accounts:
            return None, []
            
        # Prepare text for embedding
        # We combine name, type, and subtype for better context
        texts = []
        for acc in accounts:
            text = f"{acc.name} {acc.type or ''} {acc.subtype or ''}".strip()
            texts.append(text)
        
    # Generate embeddings
    embeddings = model.encode(texts)
    embeddings = np.array(embeddings).astype('float32')
    
    # Initialize FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    return index, account_ids

def search_accounts_semantic(query_text, top_k=5):
    """
    Perform a semantic search on the chart of accounts and return account IDs.
    """
    index, account_ids = build_index()
    if not index or not account_ids:
        return []
        
    model = get_model()
    query_embedding = model.encode([query_text])
    query_embedding = np.array(query_embedding).astype('float32')
    
    distances, indices = index.search(query_embedding, min(top_k, len(account_ids)))
    
    results_ids = []
    for idx in indices[0]:
        if idx != -1 and idx < len(account_ids):
            results_ids.append(account_ids[idx])
            
    return results_ids
