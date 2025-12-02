import json
from pathlib import Path
import pickle
import re
import numpy as np
from typing import Dict, List, Optional
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️  sentence-transformers non installé. Installez avec: pip install sentence-transformers")



MODAL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

DBSCAN_EPS = 0.03
DBSCAN_MIN_SAMPLES = 2


CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDINGS_CACHE_FILE = CACHE_DIR / "company_embeddings.pkl"
NORMALIZATION_CACHE_FILE = CACHE_DIR / "company_normalizations.json"

class CompanyNormalizerML:
    def __init__(self, model_name: str = MODAL_NAME):

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers requis. Installez: pip install sentence-transformers")
        
        self.model = SentenceTransformer(model_name)
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self.normalization_cache: Dict[str, str] = {}
        self.clusters: Optional[np.ndarray] = None

        self._load_cache()

    def _load_cache(self):
        if EMBEDDINGS_CACHE_FILE.exists():
            try:
                with open(EMBEDDINGS_CACHE_FILE, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
            except Exception as e:
                print(f"⚠️  Erreur chargement embeddings cache: {e}")
        else:
            print("🔴 Aucun fichier embeddings cache trouvé")

        
        if NORMALIZATION_CACHE_FILE.exists():
            try:
                with open(NORMALIZATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.normalization_cache = json.load(f)
            except Exception as e:
                print(f"⚠️  Erreur chargement normalizations cache: {e}")
        else:
            print("🔴 Aucun fichier normalizations cache trouvé")

    def clear_cache(self):
        self.embeddings_cache.clear()
        self.normalization_cache.clear()

        if(EMBEDDINGS_CACHE_FILE.exists()):
            EMBEDDINGS_CACHE_FILE.unlink()
        if(NORMALIZATION_CACHE_FILE.exists()):
            NORMALIZATION_CACHE_FILE.unlink()

    def encode_company(self, company: str) -> np.ndarray:
        company_normalized = company.lower().strip()

        if company_normalized in self.embeddings_cache:
            return self.embeddings_cache[company_normalized]
        
        embedding = self.model.encode(company_normalized, convert_to_numpy=True)

        self.embeddings_cache[company_normalized] = embedding

        return embedding
    
    def validate_cluster_coherence(self, cluster_companies: List[str], cluster_embeddings: np.ndarray, coherence_threshold: float = 0.90, min_similarity_threshold: float = 0.75) -> bool:
        if len(cluster_companies) < 2:
             return True
        
        similarity_matrix = cosine_similarity(cluster_embeddings)
        np.fill_diagonal(similarity_matrix, 0)

        avg_similarity = np.mean(similarity_matrix[similarity_matrix > 0])

        min_similarity = np.min(similarity_matrix[similarity_matrix > 0])

        is_coherent = (avg_similarity >= coherence_threshold and min_similarity >= min_similarity_threshold)

        return is_coherent
    
    def fit_clusters(self, companies: List[str], eps: float = DBSCAN_EPS, min_samples: int = DBSCAN_MIN_SAMPLES, validate_coherence: bool = True, coherence_threshold: float = 0.90) -> np.ndarray:
        if not companies:
            return np.array([])
            
        embeddings = np.array([self.encode_company(c) for c in companies])

        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = clustering.fit_predict(embeddings)

        n_clusters_initial = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_initial = list(labels).count(-1)

        if validate_coherence and n_clusters_initial > 0:
            refined_labels = labels.copy()
            next_cluster_id = labels.max() + 1
            refined_count = 0

            for cluster_id in range(n_clusters_initial):
                cluster_mask = labels == cluster_id
                cluster_indices = np.where(cluster_mask)[0]

                if len(cluster_indices) < 2:
                    continue

                cluster_companies = [companies[i] for i in cluster_indices]
                cluster_embeddings = embeddings[cluster_indices]
                
                # Valider cohérence
                is_coherent = self.validate_cluster_coherence(
                    cluster_companies, 
                    cluster_embeddings,
                    coherence_threshold
                )
                
                # Si incohérent, raffiner
                if not is_coherent:
                    sub_clusters = self.refine_cluster_hierarchical(
                        cluster_companies,
                        cluster_embeddings,
                        threshold=0.80
                    )
                    
                    # Réassigner labels
                    if len(sub_clusters) > 1:
                        refined_count += 1
                        for sub_idx, sub_cluster in enumerate(sub_clusters):
                            for company in sub_cluster:
                                # Trouver l'indice global
                                global_idx = cluster_indices[cluster_companies.index(company)]
                                
                                if sub_idx == 0:
                                    # Garder cluster ID original
                                    refined_labels[global_idx] = cluster_id
                                else:
                                    # Nouveau cluster ID
                                    refined_labels[global_idx] = next_cluster_id
                                    next_cluster_id += 1
            
            if refined_count > 0:
                labels = refined_labels
                n_clusters_final = len(set(labels)) - (1 if -1 in labels else 0)
                print(f"\n✅ Raffinement terminé : {refined_count} cluster(s) divisé(s)")
                print(f"✅ {n_clusters_final} clusters finaux (vs {n_clusters_initial} initial)")
            else:
                print(f"\n✅ Tous les clusters sont cohérents")
        
        self.clusters = labels
        return labels
    
    # def refine_cluster_hierarchical(self, cluster_company: List[str], cluster_embeddings: np.ndarray, threshold: float = 0.80) -> List[List[str]]:

    #     from sklearn.cluster import AgglomerativeClustering
    

# print(CompanyNormalizerML().encode_company("Redax"))