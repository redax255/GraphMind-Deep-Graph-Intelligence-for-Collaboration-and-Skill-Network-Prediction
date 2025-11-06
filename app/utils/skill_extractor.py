# skill_extractor.py

"""
Interface unifiée pour l'extraction de compétences.

Permet de switcher facilement entre:
- Pattern Matching (rapide, précis)
- NLP (plus complet, plus lent)
"""

from typing import List, Dict, Literal
from enum import Enum

from app.utils.text_processing import (
    extract_skills_from_text,
    extract_skills_from_profile,
    get_skills_statistics
)

from app.utils.text_processing_nlp import (
    extract_skills_with_nlp,
    extract_skills_from_profile_nlp,
    get_skills_statistics_nlp
)


# ============================================
# ENUM DES MÉTHODES
# ============================================

class ExtractionMethod(str, Enum):
    """Méthodes d'extraction disponibles"""
    PATTERN_MATCHING = "pattern_matching"
    NLP = "nlp"


# ============================================
# INTERFACE UNIFIÉE
# ============================================

class SkillExtractor:
    """
    Interface unifiée pour l'extraction de compétences.
    
    Usage:
        >>> extractor = SkillExtractor(method="pattern_matching")
        >>> skills = extractor.extract_from_text("Expert en Python et Docker")
        ['Python', 'Docker']
        
        >>> extractor = SkillExtractor(method="nlp")
        >>> skills = extractor.extract_from_text("Expert en Python et Docker")
        ['Python', 'Docker', ...]  # Peut en trouver plus
    """
    
    def __init__(self, method: str = "pattern_matching"):
        """
        Initialise l'extracteur.
        
        Args:
            method: "pattern_matching" ou "nlp"
        """
        if method not in [ExtractionMethod.PATTERN_MATCHING, ExtractionMethod.NLP]:
            raise ValueError(f"Méthode invalide: {method}. Utilisez 'pattern_matching' ou 'nlp'")
        
        self.method = method
    
    def extract_from_text(self, text: str) -> List[str]:
        """
        Extrait les compétences d'un texte.
        
        Args:
            text: Texte à analyser
        
        Returns:
            Liste de compétences
        """
        if self.method == ExtractionMethod.PATTERN_MATCHING:
            return extract_skills_from_text(text)
        else:  # NLP
            return extract_skills_with_nlp(text)
    
    def extract_from_profile(self, profile: Dict) -> List[str]:
        """
        Extrait les compétences d'un profil complet.
        
        Args:
            profile: Dictionnaire du profil MongoDB
        
        Returns:
            Liste de compétences
        """
        if self.method == ExtractionMethod.PATTERN_MATCHING:
            return extract_skills_from_profile(profile)
        else:  # NLP
            return extract_skills_from_profile_nlp(profile)
    
    def get_statistics(self, profiles: List[Dict]) -> Dict:
        """
        Calcule des statistiques sur une liste de profils.
        
        Args:
            profiles: Liste de profils
        
        Returns:
            Dictionnaire avec statistiques
        """
        if self.method == ExtractionMethod.PATTERN_MATCHING:
            return get_skills_statistics(profiles)
        else:  # NLP
            return get_skills_statistics_nlp(profiles)
    
    def __repr__(self) -> str:
        return f"SkillExtractor(method='{self.method}')"


# ============================================
# FONCTIONS HELPER
# ============================================

def get_available_methods() -> List[str]:
    """
    Retourne la liste des méthodes disponibles.
    
    Returns:
        Liste des méthodes
    """
    return [ExtractionMethod.PATTERN_MATCHING, ExtractionMethod.NLP]


def get_default_extractor() -> SkillExtractor:
    """
    Retourne l'extracteur par défaut (Pattern Matching).
    
    Returns:
        SkillExtractor configuré
    """
    return SkillExtractor(method=ExtractionMethod.PATTERN_MATCHING)


def create_extractor(method: str = "pattern_matching") -> SkillExtractor:
    """
    Factory pour créer un extracteur.
    
    Args:
        method: "pattern_matching" ou "nlp"
    
    Returns:
        SkillExtractor configuré
    """
    return SkillExtractor(method=method)


# ============================================
# EXPORT
# ============================================

__all__ = [
    "SkillExtractor",
    "ExtractionMethod",
    "get_available_methods",
    "get_default_extractor",
    "create_extractor"
]