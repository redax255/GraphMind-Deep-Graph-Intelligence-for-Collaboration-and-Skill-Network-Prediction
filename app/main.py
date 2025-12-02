"""
API FastAPI pour GraphMind.

Endpoints pour accéder aux résultats ML :
- Embeddings
- Similarités
- Communautés
- Prédictions de collaboration
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import pickle
import json
from pathlib import Path

from app.ml.embeddings import Node2VecEmbeddings
from app.ml.link_prediction import LinkPredictor

from app.config import settings


# ============================================
# CONFIGURATION
# ============================================

app = FastAPI(
    title="GraphMind API",
    description="API pour l'analyse de graphe LinkedIn et prédictions ML",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chemins des modèles
EMBEDDINGS_PATH = "data/models/node2vec_embeddings.pkl"
COMMUNITIES_PATH = "data/reports/communities.json"
LINK_PREDICTOR_PATH = "data/models/link_predictor.pkl"

# Configuration Neo4j
NEO4J_CONFIG = {
    "uri": settings.neo4j_uri,
    "user": settings.neo4j_user,
    "password": settings.neo4j_password
}


# ============================================
# MODELS PYDANTIC
# ============================================

class ProfileSimilarity(BaseModel):
    """Modèle pour similarité entre profils."""
    profile_id: str
    similarity: float = Field(..., ge=0, le=1, description="Score de similarité (0-1)")


class SimilarProfilesResponse(BaseModel):
    """Réponse pour profils similaires."""
    profile_id: str
    similar_profiles: List[ProfileSimilarity]


class CommunityInfo(BaseModel):
    """Informations sur une communauté."""
    community_id: int
    size: int
    top_skills: List[tuple]
    top_schools: List[tuple]
    top_companies: List[tuple]


class CollaborationPrediction(BaseModel):
    """Prédiction de collaboration."""
    profile_1: str
    profile_2: str
    probability: float = Field(..., ge=0, le=1, description="Probabilité de collaboration (0-1)")
    features: Optional[Dict] = None


class RecommendationResponse(BaseModel):
    """Recommandations de connexions."""
    profile_id: str
    recommendations: List[CollaborationPrediction]


class HealthResponse(BaseModel):
    """Santé de l'API."""
    status: str
    embeddings_loaded: bool
    communities_loaded: bool
    link_predictor_loaded: bool


class StatsResponse(BaseModel):
    """Statistiques globales."""
    total_profiles: int
    total_communities: int
    embedding_dimensions: int
    modularity: float


# ============================================
# CHARGEMENT DES MODÈLES
# ============================================

embeddings_data = None
communities_data = None
link_predictor = None


def load_models():
    """Charge les modèles au démarrage."""
    global embeddings_data, communities_data, link_predictor
    
    try:
        # Embeddings
        if Path(EMBEDDINGS_PATH).exists():
            with open(EMBEDDINGS_PATH, 'rb') as f:
                embeddings_data = pickle.load(f)
            print(f"✅ Embeddings chargés : {len(embeddings_data['embeddings'])} profils")
        else:
            print(f"⚠️  Embeddings non trouvés : {EMBEDDINGS_PATH}")
        
        # Communities
        if Path(COMMUNITIES_PATH).exists():
            with open(COMMUNITIES_PATH, 'r', encoding='utf-8') as f:
                communities_data = json.load(f)
            print(f"✅ Communautés chargées : {communities_data['n_communities']} communautés")
        else:
            print(f"⚠️  Communautés non trouvées : {COMMUNITIES_PATH}")
        
        # Link Predictor
        if Path(LINK_PREDICTOR_PATH).exists():
            with open(LINK_PREDICTOR_PATH, 'rb') as f:
                link_predictor = pickle.load(f)
            print(f"✅ Link Predictor chargé")
        else:
            print(f"⚠️  Link Predictor non trouvé : {LINK_PREDICTOR_PATH}")
        
    except Exception as e:
        print(f"❌ Erreur chargement modèles : {e}")


@app.on_event("startup")
async def startup_event():
    """Événement au démarrage de l'API."""
    print("🚀 Démarrage de l'API GraphMind...")
    load_models()
    print("✅ API prête !")


# ============================================
# ENDPOINTS
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API."""
    return {
        "message": "Bienvenue sur GraphMind API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "stats": "/stats",
            "embeddings": "/embeddings/{profile_id}",
            "similar": "/similar/{profile_id}",
            "communities": "/communities",
            "community": "/community/{community_id}",
            "predict": "/predict/collaboration",
            "recommendations": "/recommendations/{profile_id}"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Vérifier la santé de l'API."""
    return {
        "status": "healthy",
        "embeddings_loaded": embeddings_data is not None,
        "communities_loaded": communities_data is not None,
        "link_predictor_loaded": link_predictor is not None
    }


@app.get("/stats", response_model=StatsResponse, tags=["System"])
async def get_stats():
    """Statistiques globales du système."""
    if not embeddings_data or not communities_data:
        raise HTTPException(status_code=503, detail="Modèles non chargés")
    
    return {
        "total_profiles": len(embeddings_data['embeddings']),
        "total_communities": communities_data['n_communities'],
        "embedding_dimensions": embeddings_data['dimensions'],
        "modularity": communities_data['modularity']
    }


@app.get("/embeddings/{profile_id}", tags=["Embeddings"])
async def get_embedding(profile_id: str):
    """
    Récupérer le vecteur embedding d'un profil.
    
    Args:
        profile_id: ID du profil
    
    Returns:
        Vecteur 128D
    """
    if not embeddings_data:
        raise HTTPException(status_code=503, detail="Embeddings non chargés")
    
    embeddings = embeddings_data['embeddings']
    
    if profile_id not in embeddings:
        raise HTTPException(status_code=404, detail=f"Profil '{profile_id}' non trouvé")
    
    embedding = embeddings[profile_id].tolist()
    
    return {
        "profile_id": profile_id,
        "embedding": embedding,
        "dimensions": len(embedding)
    }


@app.get("/similar/{profile_id}", response_model=SimilarProfilesResponse, tags=["Embeddings"])
async def get_similar_profiles(
    profile_id: str,
    top_k: int = Query(default=10, ge=1, le=50, description="Nombre de profils similaires")
):
    """
    Trouver les profils les plus similaires.
    
    Args:
        profile_id: ID du profil
        top_k: Nombre de profils à retourner
    
    Returns:
        Liste des profils similaires avec scores
    """
    if not embeddings_data:
        raise HTTPException(status_code=503, detail="Embeddings non chargés")
    
    embeddings = embeddings_data['embeddings']
    
    if profile_id not in embeddings:
        raise HTTPException(status_code=404, detail=f"Profil '{profile_id}' non trouvé")
    
    # Calculer similarités
    import numpy as np
    
    target_emb = embeddings[profile_id]
    similarities = []
    
    for other_id, other_emb in embeddings.items():
        if other_id == profile_id:
            continue
        
        # Cosine similarity
        cos_sim = np.dot(target_emb, other_emb) / (
            np.linalg.norm(target_emb) * np.linalg.norm(other_emb)
        )
        
        similarities.append({
            "profile_id": other_id,
            "similarity": float(cos_sim)
        })
    
    # Trier et prendre top K
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    top_similar = similarities[:top_k]
    
    return {
        "profile_id": profile_id,
        "similar_profiles": top_similar
    }


@app.get("/communities", tags=["Communities"])
async def get_communities():
    """
    Liste toutes les communautés.
    
    Returns:
        Liste des communautés avec statistiques
    """
    if not communities_data:
        raise HTTPException(status_code=503, detail="Communautés non chargées")
    
    communities = communities_data['communities']
    
    # Formater réponse
    result = []
    for comm_id, data in communities.items():
        result.append({
            "community_id": int(comm_id),
            "size": data['size'],
            "top_skills": data['top_skills'][:5],
            "top_schools": data['top_schools'][:3],
            "top_companies": data['top_companies'][:3]
        })
    
    # Trier par taille
    result.sort(key=lambda x: x['size'], reverse=True)
    
    return {
        "n_communities": len(result),
        "modularity": communities_data['modularity'],
        "communities": result
    }


@app.get("/community/{community_id}", response_model=CommunityInfo, tags=["Communities"])
async def get_community(community_id: int):
    """
    Détails d'une communauté spécifique.
    
    Args:
        community_id: ID de la communauté
    
    Returns:
        Détails de la communauté
    """
    if not communities_data:
        raise HTTPException(status_code=503, detail="Communautés non chargées")
    
    communities = communities_data['communities']
    comm_id_str = str(community_id)
    
    if comm_id_str not in communities:
        raise HTTPException(status_code=404, detail=f"Communauté {community_id} non trouvée")
    
    data = communities[comm_id_str]
    
    return {
        "community_id": community_id,
        "size": data['size'],
        "top_skills": data['top_skills'],
        "top_schools": data['top_schools'],
        "top_companies": data['top_companies']
    }


@app.get("/profile/{profile_id}/community", tags=["Communities"])
async def get_profile_community(profile_id: str):
    """
    Communauté d'un profil spécifique.
    
    Args:
        profile_id: ID du profil
    
    Returns:
        Communauté du profil
    """
    if not communities_data:
        raise HTTPException(status_code=503, detail="Communautés non chargées")
    
    assignments = communities_data['assignments']
    
    if profile_id not in assignments:
        raise HTTPException(status_code=404, detail=f"Profil '{profile_id}' non trouvé")
    
    community_id = assignments[profile_id]
    
    # Récupérer info communauté
    communities = communities_data['communities']
    comm_data = communities[str(community_id)]
    
    return {
        "profile_id": profile_id,
        "community_id": community_id,
        "community_size": comm_data['size'],
        "top_skills": comm_data['top_skills'][:5]
    }


@app.post("/predict/collaboration", response_model=CollaborationPrediction, tags=["Predictions"])
async def predict_collaboration(
    profile_1: str = Query(..., description="ID du premier profil"),
    profile_2: str = Query(..., description="ID du second profil")
):
    """
    Prédire la probabilité de collaboration entre 2 profils.
    
    Args:
        profile_1: ID du premier profil
        profile_2: ID du second profil
    
    Returns:
        Probabilité de collaboration
    """
    if not link_predictor:
        raise HTTPException(status_code=503, detail="Link Predictor non chargé")
    
    if not embeddings_data:
        raise HTTPException(status_code=503, detail="Embeddings non chargés")
    
    # Vérifier existence
    embeddings = embeddings_data['embeddings']
    if profile_1 not in embeddings or profile_2 not in embeddings:
        raise HTTPException(status_code=404, detail="Un ou plusieurs profils non trouvés")
    
    # Créer predictor instance pour extraction features
    predictor = LinkPredictor(
        uri=NEO4J_CONFIG['uri'],
        user=NEO4J_CONFIG['user'],
        password=NEO4J_CONFIG['password']
    )
    
    # Charger graphe et embeddings
    predictor.load_graph_from_neo4j()
    predictor.embeddings = embeddings
    predictor.model = link_predictor
    
    # Extraire features
    features = predictor.extract_features([(profile_1, profile_2)])
    
    # Prédire
    proba = link_predictor.predict_proba(features)[0, 1]
    
    return {
        "profile_1": profile_1,
        "profile_2": profile_2,
        "probability": float(proba)
    }


@app.get("/recommendations/{profile_id}", response_model=RecommendationResponse, tags=["Predictions"])
async def get_recommendations(
    profile_id: str,
    top_k: int = Query(default=10, ge=1, le=50, description="Nombre de recommandations")
):
    """
    Recommandations de connexions pour un profil.
    
    Args:
        profile_id: ID du profil
        top_k: Nombre de recommandations
    
    Returns:
        Liste des profils recommandés avec probabilités
    """
    if not link_predictor or not embeddings_data:
        raise HTTPException(status_code=503, detail="Modèles non chargés")
    
    embeddings = embeddings_data['embeddings']
    
    if profile_id not in embeddings:
        raise HTTPException(status_code=404, detail=f"Profil '{profile_id}' non trouvé")
    
    # Créer predictor instance
    predictor = LinkPredictor(
        uri=NEO4J_CONFIG['uri'],
        user=NEO4J_CONFIG['user'],
        password=NEO4J_CONFIG['password']
    )
    
    # Charger graphe
    predictor.load_graph_from_neo4j()
    predictor.embeddings = embeddings
    predictor.model = link_predictor
    
    # Générer candidates (tous les profils non connectés)
    all_profiles = list(embeddings.keys())
    neighbors = set(predictor.graph.neighbors(profile_id)) if profile_id in predictor.graph else set()
    
    candidates = [
        p for p in all_profiles 
        if p != profile_id and p not in neighbors
    ]
    
    # Limiter pour performance
    import random
    if len(candidates) > 500:
        candidates = random.sample(candidates, 500)
    
    # Créer paires
    pairs = [(profile_id, c) for c in candidates]
    
    # Extraire features
    X = predictor.extract_features(pairs)
    
    # Prédire
    probas = link_predictor.predict_proba(X)[:, 1]
    
    # Top K
    top_indices = probas.argsort()[-top_k:][::-1]
    
    recommendations = [
        {
            "profile_1": profile_id,
            "profile_2": candidates[i],
            "probability": float(probas[i])
        }
        for i in top_indices
    ]
    
    return {
        "profile_id": profile_id,
        "recommendations": recommendations
    }


@app.get("/search/profiles", tags=["Search"])
async def search_profiles(
    skills: Optional[str] = Query(None, description="Compétences (séparées par virgule)"),
    school: Optional[str] = Query(None, description="École"),
    company: Optional[str] = Query(None, description="Entreprise"),
    community_id: Optional[int] = Query(None, description="ID communauté"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre de résultats")
):
    """
    Rechercher des profils par critères.
    
    Args:
        skills: Compétences recherchées
        school: École
        company: Entreprise
        community_id: Communauté
        limit: Nombre de résultats
    
    Returns:
        Liste des profils correspondants
    """
    if not communities_data:
        raise HTTPException(status_code=503, detail="Modèles non chargés")
    
    # TODO: Implémenter recherche avec Neo4j
    # Pour l'instant, retour simple
    
    return {
        "message": "Endpoint de recherche (à implémenter)",
        "filters": {
            "skills": skills,
            "school": school,
            "company": company,
            "community_id": community_id
        }
    }


# ============================================
# ENDPOINTS UTILITAIRES
# ============================================

@app.post("/reload", tags=["System"])
async def reload_models():
    """Recharger les modèles."""
    try:
        load_models()
        return {"status": "success", "message": "Modèles rechargés"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur rechargement : {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )