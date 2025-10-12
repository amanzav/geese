"""
Embeddings Module - Handles text embedding generation and vector search
"""

import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


class EmbeddingsManager:
    """Manage text embeddings and vector similarity search"""
    
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2", cache_dir="embeddings/resume"):
        """Initialize embeddings manager with model and cache directory"""
        print(f"📦 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.index = None
        self.resume_bullets = []
        # Get dimension dynamically from model
        self.dimension = self.model.get_sentence_embedding_dimension()
        os.makedirs(cache_dir, exist_ok=True)
    
    def encode(self, texts, normalize=True, show_progress=False):
        """Generate embeddings for texts"""
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        return embeddings.astype('float32')
    
    def build_resume_index(self, resume_bullets):
        """
        Build FAISS index from resume bullets
        
        Args:
            resume_bullets: List of resume bullet strings
        """
        if not resume_bullets:
            raise ValueError("Cannot build index with empty resume bullets")
        
        print(f"🔨 Building index from {len(resume_bullets)} resume bullets...")
        
        self.resume_bullets = resume_bullets
        
        # Generate embeddings
        embeddings = self.encode(resume_bullets, show_progress=True)
        
        # Create FAISS index (inner product = cosine similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)
        
        print(f"✅ Index built successfully with {self.index.ntotal} vectors")
        
        # Save to disk
        self.save_index()
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        if self.index is None:
            print("⚠️  No index to save")
            return
        
        index_path = os.path.join(self.cache_dir, "index.faiss")
        metadata_path = os.path.join(self.cache_dir, "metadata.json")
        
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        
        # Save metadata (resume bullets mapping)
        metadata = {
            "resume_bullets": self.resume_bullets,
            "dimension": self.dimension,
            "num_vectors": len(self.resume_bullets),
            "model_name": self.model_name
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Index saved to {index_path}")
        print(f"💾 Metadata saved to {metadata_path}")
    
    def load_index(self):
        """Load FAISS index and metadata from disk"""
        index_path = os.path.join(self.cache_dir, "index.faiss")
        metadata_path = os.path.join(self.cache_dir, "metadata.json")
        
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index not found at {index_path}. Build it first with build_resume_index()")
        
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata not found at {metadata_path}")
        
        # Load metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Validate model compatibility
        cached_model = metadata.get('model_name')
        cached_dimension = metadata['dimension']
        
        if cached_model and cached_model != self.model_name:
            raise ValueError(
                f"⚠️  Model mismatch!\n"
                f"   Cached index was built with: {cached_model}\n"
                f"   Current model: {self.model_name}\n"
                f"   Please rebuild the index or change config to use '{cached_model}'"
            )
        
        if cached_dimension != self.dimension:
            raise ValueError(
                f"⚠️  Dimension mismatch!\n"
                f"   Cached index dimension: {cached_dimension}\n"
                f"   Current model dimension: {self.dimension}\n"
                f"   Please rebuild the index with the current model"
            )
        
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        
        self.resume_bullets = metadata['resume_bullets']
        
        print(f"📂 Loaded index with {self.index.ntotal} vectors")
        return True
    
    def search(self, query_texts, k=8):
        """
        Search for similar resume bullets
        
        Args:
            query_texts: List of query strings (e.g., JD bullets)
            k: Number of top results to return per query
            
        Returns:
            List of matches, one per query text:
            [
                [
                    {"resume_bullet": "...", "similarity": 0.78, "index": 0},
                    {"resume_bullet": "...", "similarity": 0.72, "index": 1},
                    ...
                ],
                ...
            ]
        """
        if self.index is None:
            raise ValueError("Index not loaded. Call load_index() or build_resume_index() first")
        
        if not query_texts:
            return []
        
        # Generate query embeddings
        query_embeddings = self.encode(query_texts)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embeddings, min(k, len(self.resume_bullets)))
        
        # Format results
        results = []
        for query_idx, (dists, idxs) in enumerate(zip(distances, indices)):
            matches = []
            for similarity, resume_idx in zip(dists, idxs):
                if resume_idx >= 0 and resume_idx < len(self.resume_bullets):  # Valid index
                    matches.append({
                        "resume_bullet": self.resume_bullets[resume_idx],
                        "similarity": float(similarity),
                        "index": int(resume_idx)
                    })
            results.append(matches)
        
        return results
    
    def index_exists(self):
        """Check if cached index exists"""
        index_path = os.path.join(self.cache_dir, "index.faiss")
        metadata_path = os.path.join(self.cache_dir, "metadata.json")
        return os.path.exists(index_path) and os.path.exists(metadata_path)
