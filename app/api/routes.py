# routes.py
"""
Routes de l'API Graph ML Morocco.

Endpoints disponibles :
- /profiles - Gestion des profils
- /graph - Analyse du graphe
- /predict - Prédictions et recommandations
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging

from app.models.schemas import (
    Profile,
    GraphStats,
    RecommendationRequest,
    RecommendationResponse,
    SuccessResponse,
    ErrorResponse
)
from app.services.database import async_mongo_client, get_async_db_client

# Logger
logger = logging.getLogger(__name__)

# Router principal
router = APIRouter()


# ============================================
# PROFILS - ENDPOINTS
# ============================================

@router.get(
    "/profiles",
    response_model=List[Profile],
    summary="Récupérer tous les profils",
    description="Retourne la liste de tous les profils avec pagination optionnelle"
)
async def get_profiles(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Nombre maximum de profils à retourner"),
    db = Depends(get_async_db_client)
):
    """
    Récupère tous les profils de la base de données.
    
    Args:
        limit: Nombre maximum de profils (None = tous)
    
    Returns:
        Liste des profils
    """
    try:
        profiles = await db.get_all_profiles(limit=limit)
        logger.info(f"✅ {len(profiles)} profils récupérés")
        return profiles
    except Exception as e:
        logger.error(f"❌ Erreur get_profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des profils: {str(e)}")


@router.get(
    "/profiles/count",
    response_model=dict,
    summary="Compter les profils",
    description="Retourne le nombre total de profils dans la base de données"
)
async def get_profiles_count(db = Depends(get_async_db_client)):
    """
    Compte le nombre total de profils.
    
    Returns:
        Dictionnaire avec le count
    """
    try:
        count = await db.get_profile_count()
        return {
            "success": True,
            "count": count,
            "message": f"{count} profils dans la base de données"
        }
    except Exception as e:
        logger.error(f"❌ Erreur get_profiles_count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/profiles/search",
    response_model=List[Profile],
    summary="Rechercher des profils",
    description="Recherche des profils par ville, compétence ou entreprise"
)
async def search_profiles(
    location: Optional[str] = Query(None, description="Filtrer par localisation"),
    company: Optional[str] = Query(None, description="Filtrer par entreprise"),
    skill: Optional[str] = Query(None, description="Filtrer par compétence"),
    limit: int = Query(50, ge=1, le=500, description="Nombre maximum de résultats"),
    db = Depends(get_async_db_client)
):
    """
    Recherche de profils avec filtres.
    
    Args:
        location: Ville ou pays (ex: "Rabat", "Maroc")
        company: Nom d'entreprise (ex: "OCP", "SQLI")
        skill: Compétence (ex: "Python", "React")
        limit: Nombre maximum de résultats
    
    Returns:
        Liste de profils correspondants
    """
    # TODO: Implémenter la recherche complète
    # Pour l'instant, retourne tous les profils
    try:
        profiles = await db.get_all_profiles(limit=limit)
        
        # Filtrage basique par location (si fourni)
        if location:
            profiles = [
                p for p in profiles 
                if p.get('location') and location.lower() in p.get('location', '').lower()
            ]
        
        logger.info(f"🔍 {len(profiles)} profils trouvés")
        return profiles
        
    except Exception as e:
        logger.error(f"❌ Erreur search_profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# GRAPHE - ENDPOINTS
# ============================================

@router.get(
    "/graph/stats",
    response_model=dict,
    summary="Statistiques du graphe",
    description="Retourne les statistiques du graphe de connaissances"
)
async def get_graph_stats():
    """
    Récupère les statistiques du graphe.
    
    Returns:
        Statistiques (nombre de nœuds, edges, etc.)
    """
    # TODO: Implémenter après Phase 3 (construction du graphe)
    return {
        "success": True,
        "message": "Graphe non encore construit",
        "status": "Phase 3 à implémenter",
        "info": "Utilisez le script 'scripts/train_graph.py' pour construire le graphe"
    }


@router.get(
    "/graph/visualize",
    response_model=dict,
    summary="Visualiser le graphe",
    description="Génère une visualisation du graphe"
)
async def visualize_graph(
    node_type: Optional[str] = Query(None, description="Filtrer par type de nœud (profile, company, skill, school)")
):
    """
    Génère une visualisation du graphe.
    
    Args:
        node_type: Type de nœud à visualiser
    
    Returns:
        URL ou données de visualisation
    """
    # TODO: Implémenter la visualisation
    return {
        "success": False,
        "message": "Visualisation non encore implémentée",
        "status": "À implémenter en Phase 4"
    }


# ============================================
# PRÉDICTIONS - ENDPOINTS
# ============================================

@router.post(
    "/predict/recommend",
    response_model=dict,
    summary="Recommandations de connexions",
    description="Obtenir des recommandations de connexions pour un profil"
)
async def recommend_connections(request: RecommendationRequest):
    """
    Recommande des connexions pour un profil donné.
    
    Args:
        request: Requête avec profile_id et top_k
    
    Returns:
        Liste de recommandations
    """
    # TODO: Implémenter après Phase 5 (Link Prediction)
    return {
        "success": False,
        "message": "Système de recommandation non encore entraîné",
        "status": "Phase 5 à implémenter",
        "info": "Utilisez le script 'scripts/train_ml.py' pour entraîner le modèle",
        "requested_profile": request.profile_id,
        "requested_top_k": request.top_k
    }


@router.post(
    "/predict/collaboration",
    response_model=dict,
    summary="Prédire une collaboration",
    description="Prédit la probabilité de collaboration entre deux profils"
)
async def predict_collaboration(
    profile_1: str = Query(..., description="ID du premier profil"),
    profile_2: str = Query(..., description="ID du deuxième profil")
):
    """
    Prédit la probabilité de collaboration entre deux profils.
    
    Args:
        profile_1: ID du premier profil
        profile_2: ID du deuxième profil
    
    Returns:
        Score de prédiction et détails
    """
    # TODO: Implémenter après Phase 5
    return {
        "success": False,
        "message": "Modèle de prédiction non encore entraîné",
        "status": "Phase 5 à implémenter",
        "profile_1": profile_1,
        "profile_2": profile_2
    }


# ============================================
# ADMIN - ENDPOINTS
# ============================================

@router.get(
    "/admin/data-quality",
    response_model=dict,
    summary="Qualité des données",
    description="Analyse la qualité des données (% champs remplis)",
    tags=["Admin"]
)
async def get_data_quality():
    """
    Analyse la qualité des données dans MongoDB.
    
    Returns:
        Statistiques de complétude des champs
    """
    try:
        # Utiliser le client synchrone pour cette opération
        from app.services.database import MongoDBClient
        
        with MongoDBClient() as db:
            stats = db.get_data_quality_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur data_quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/admin/locations",
    response_model=dict,
    summary="Distribution géographique",
    description="Répartition des profils par localisation",
    tags=["Admin"]
)
async def get_locations_distribution():
    """
    Récupère la distribution géographique des profils.
    
    Returns:
        Dictionnaire {location: count}
    """
    try:
        from app.services.database import MongoDBClient
        
        with MongoDBClient() as db:
            locations = db.get_profiles_by_location()
        
        return {
            "success": True,
            "data": locations,
            "total_locations": len(locations)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur locations_distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STATUS - ENDPOINT
# ============================================

@router.get(
    "/status",
    response_model=dict,
    summary="État du projet",
    description="Retourne l'état d'avancement du projet (phases complétées)"
)
async def get_project_status():
    """
    Retourne l'état d'avancement du projet.
    
    Returns:
        État de chaque phase
    """
    return {
        "success": True,
        "project": "Graph ML Morocco - Écosystème Tech Marocain",
        "version": "1.0.0",
        "phases": {
            "phase_1_exploration": {
                "status": "completed",
                "description": "Exploration des données MongoDB",
                "progress": "100%"
            },
            "phase_2_preprocessing": {
                "status": "pending",
                "description": "Nettoyage et extraction de compétences",
                "progress": "0%"
            },
            "phase_3_graph": {
                "status": "pending",
                "description": "Construction du graphe NetworkX",
                "progress": "0%"
            },
            "phase_4_embeddings": {
                "status": "pending",
                "description": "Génération des embeddings (node2vec)",
                "progress": "0%"
            },
            "phase_5_ml": {
                "status": "pending",
                "description": "Link Prediction et recommandations",
                "progress": "0%"
            },
            "phase_6_finalization": {
                "status": "pending",
                "description": "Finalisation et documentation",
                "progress": "0%"
            }
        },
        "next_steps": [
            "Exécuter scripts/data_preprocessing.py pour Phase 2",
            "Exécuter scripts/train_graph.py pour Phase 3",
            "Exécuter scripts/train_ml.py pour Phase 4-5"
        ]
    }


# ============================================
# EXPORT
# ============================================

__all__ = ["router"]