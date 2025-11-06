# schemas.py
"""
Modèles Pydantic pour la validation des données.

Ce module définit tous les schémas de données utilisés dans l'API :
- Profils LinkedIn
- Graphe et nœuds
- Prédictions et recommandations
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class NodeType(str, Enum):
    """Types de nœuds dans le graphe"""
    PROFILE = "profile"
    COMPANY = "company"
    SKILL = "skill"
    SCHOOL = "school"


class EdgeType(str, Enum):
    """Types de relations dans le graphe"""
    WORKS_AT = "works_at"
    WORKED_AT = "worked_at"
    HAS_SKILL = "has_skill"
    STUDIED_AT = "studied_at"
    COLLABORATED_WITH = "collaborated_with"
    KNOWS = "knows"


# ============================================
# PROFIL LINKEDIN - SOUS-MODÈLES
# ============================================

class Experience(BaseModel):
    """Expérience professionnelle d'un profil"""
    position: Optional[str] = None
    company: Optional[str] = None
    period: Optional[str] = None
    location: Optional[str] = None
    description: Optional[List[str]] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "position": "Data Scientist",
                "company": "SQLI",
                "period": "janv. 2023 - aujourd'hui · 2 ans",
                "location": "Rabat, Maroc",
                "description": ["Développement de modèles ML", "Python · SQL · Spark"]
            }
        }


class Formation(BaseModel):
    """Formation académique d'un profil"""
    university: Optional[str] = None
    degree: Optional[str] = None
    period: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "university": "ENSIAS",
                "degree": "Ingénieur en Data Science",
                "period": "2018 - 2021"
            }
        }


# ============================================
# PROFIL LINKEDIN - MODÈLE PRINCIPAL
# ============================================

class ProfileBase(BaseModel):
    """Modèle de base d'un profil (champs essentiels)"""
    linkedinUrl: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    resume: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "linkedinUrl": "https://www.linkedin.com/in/ahmed-benali",
                "first_name": "Ahmed",
                "last_name": "Benali",
                "position": "Machine Learning Engineer",
                "location": "Casablanca, Maroc",
                "resume": "Expert en ML avec 5 ans d'expérience..."
            }
        }


class Profile(ProfileBase):
    """
    Modèle complet d'un profil LinkedIn.
    
    Correspond à la structure MongoDB.
    """
    # Informations de contact (souvent vides)
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    
    # Parcours professionnel
    experience: List[Experience] = Field(default_factory=list)
    formation: List[Formation] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    
    # Métadonnées MongoDB
    id: Optional[str] = Field(None, alias="_id")
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    
    # Champs internes (non utilisés dans le projet)
    Image: Optional[str] = None
    addedby: Optional[str] = None
    type: Optional[str] = None
    isDeleted: Optional[bool] = False
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "linkedinUrl": "https://www.linkedin.com/in/ahmed-benali",
                "first_name": "Ahmed",
                "last_name": "Benali",
                "position": "Data Scientist @ OCP",
                "location": "Casablanca, Maroc",
                "resume": "Passionné par l'IA et le ML...",
                "experience": [
                    {
                        "position": "Data Scientist",
                        "company": "OCP",
                        "period": "2023 - aujourd'hui"
                    }
                ],
                "skills": ["Python", "TensorFlow", "SQL"]
            }
        }


class ProfileCleaned(BaseModel):
    """
    Profil nettoyé après preprocessing (Phase 2).
    
    Contient les données extraites et normalisées.
    """
    profile_id: str
    full_name: str
    current_position: Optional[str] = None
    location: Optional[str] = None
    
    # Compétences extraites (depuis resume + experience)
    skills: List[str] = Field(default_factory=list)
    
    # Entreprises (historique)
    companies: List[str] = Field(default_factory=list)
    current_company: Optional[str] = None
    
    # Écoles
    schools: List[str] = Field(default_factory=list)
    
    # Expériences avec dates normalisées
    experiences_normalized: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "ahmed-benali",
                "full_name": "Ahmed Benali",
                "current_position": "Data Scientist",
                "location": "Casablanca, Maroc",
                "skills": ["Python", "TensorFlow", "SQL", "Docker"],
                "companies": ["OCP", "SQLI", "Capgemini"],
                "current_company": "OCP",
                "schools": ["ENSIAS"]
            }
        }


# ============================================
# GRAPHE - MODÈLES
# ============================================

class Node(BaseModel):
    """Nœud du graphe"""
    node_id: str
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "profile_123",
                "node_type": "profile",
                "label": "Ahmed Benali",
                "properties": {"position": "Data Scientist", "location": "Casablanca"}
            }
        }


class Edge(BaseModel):
    """Arête du graphe (relation entre 2 nœuds)"""
    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "profile_123",
                "target": "company_ocp",
                "edge_type": "works_at",
                "weight": 1.0
            }
        }


class GraphStats(BaseModel):
    """Statistiques du graphe"""
    num_nodes: int
    num_edges: int
    num_profiles: int
    num_companies: int
    num_skills: int
    num_schools: int
    avg_degree: float
    density: float
    num_connected_components: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "num_nodes": 2847,
                "num_edges": 9532,
                "num_profiles": 847,
                "num_companies": 250,
                "num_skills": 1500,
                "num_schools": 250,
                "avg_degree": 6.7,
                "density": 0.0024,
                "num_connected_components": 1
            }
        }


# ============================================
# PRÉDICTIONS - MODÈLES
# ============================================

class CollaborationPrediction(BaseModel):
    """Prédiction de collaboration entre 2 profils"""
    profile_1: str
    profile_2: str
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: str  # "low", "medium", "high"
    common_skills: List[str] = Field(default_factory=list)
    common_companies: List[str] = Field(default_factory=list)
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if v not in ['low', 'medium', 'high']:
            raise ValueError('confidence must be low, medium, or high')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_1": "ahmed-benali",
                "profile_2": "fatima-alaoui",
                "score": 0.87,
                "confidence": "high",
                "common_skills": ["Python", "TensorFlow", "Docker"],
                "common_companies": ["SQLI"]
            }
        }


class Recommendation(BaseModel):
    """Recommandation de connexion pour un profil"""
    profile_id: str
    name: str
    position: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "fatima-alaoui",
                "name": "Fatima Alaoui",
                "position": "ML Engineer @ OCP",
                "score": 0.87,
                "reason": "3 compétences communes, même entreprise"
            }
        }


class RecommendationRequest(BaseModel):
    """Requête pour obtenir des recommandations"""
    profile_id: str
    top_k: int = Field(default=10, ge=1, le=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "ahmed-benali",
                "top_k": 10
            }
        }


class RecommendationResponse(BaseModel):
    """Réponse avec liste de recommandations"""
    profile_id: str
    recommendations: List[Recommendation]
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "ahmed-benali",
                "recommendations": [
                    {
                        "profile_id": "fatima-alaoui",
                        "name": "Fatima Alaoui",
                        "score": 0.87,
                        "reason": "3 compétences communes"
                    }
                ]
            }
        }


# ============================================
# API - RÉPONSES GÉNÉRIQUES
# ============================================

class SuccessResponse(BaseModel):
    """Réponse générique de succès"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Réponse générique d'erreur"""
    success: bool = False
    error: str
    details: Optional[str] = None


# ============================================
# EXPORT
# ============================================

__all__ = [
    # Enums
    "NodeType",
    "EdgeType",
    
    # Profils
    "Experience",
    "Formation",
    "ProfileBase",
    "Profile",
    "ProfileCleaned",
    
    # Graphe
    "Node",
    "Edge",
    "GraphStats",
    
    # Prédictions
    "CollaborationPrediction",
    "Recommendation",
    "RecommendationRequest",
    "RecommendationResponse",
    
    # Réponses API
    "SuccessResponse",
    "ErrorResponse",
]