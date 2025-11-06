# text_processing_nlp.py

"""
Module d'extraction de compétences avec NLP (spaCy).

Supporte le français ET l'anglais.
Utilise Named Entity Recognition et POS tagging.
"""

import re
from typing import List, Set, Dict
from collections import Counter

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️  spaCy non installé. Installez avec: pip install spacy")

from app.utils.skills_database import (
    get_all_skills,
    normalize_skill,
    SKILL_VARIATIONS
)


# ============================================
# CONFIGURATION NLP
# ============================================

# Modèles spaCy à charger
NLP_MODELS = {
    "en": None,  # Sera chargé à la demande
    "fr": None   # Sera chargé à la demande
}

# Mots contextuels indiquant des compétences
SKILL_CONTEXT_KEYWORDS = {
    "en": {"skills", "technologies", "tools", "stack", "using", "experience", 
           "worked with", "proficient", "expert", "knowledge"},
    "fr": {"compétences", "technologies", "outils", "stack", "utilisant", 
           "expérience", "maîtrise", "expert", "connaissance"}
}


# ============================================
# CHARGEMENT DES MODÈLES
# ============================================

def load_nlp_model(lang: str):
    """
    Charge le modèle spaCy pour une langue.
    
    Args:
        lang: "en" ou "fr"
    
    Returns:
        Modèle spaCy chargé
    """
    if not SPACY_AVAILABLE:
        raise ImportError("spaCy n'est pas installé")
    
    if NLP_MODELS[lang] is not None:
        return NLP_MODELS[lang]
    
    try:
        if lang == "en":
            # Modèle anglais
            nlp = spacy.load("en_core_web_sm")
        elif lang == "fr":
            # Modèle français
            nlp = spacy.load("fr_core_news_sm")
        else:
            raise ValueError(f"Langue non supportée: {lang}")
        
        NLP_MODELS[lang] = nlp
        return nlp
    
    except OSError:
        error_msg = f"""
        Modèle spaCy '{lang}' non trouvé.
        
        Installez-le avec:
        python -m spacy download {"en_core_web_sm" if lang == "en" else "fr_core_news_sm"}
        """
        raise OSError(error_msg)


def detect_language(text: str) -> str:
    """
    Détecte la langue d'un texte (simple heuristique).
    
    Args:
        text: Texte à analyser
    
    Returns:
        "en" ou "fr"
    """
    if not text:
        return "en"  # Par défaut
    
    text_lower = text.lower()
    
    # Mots français courants
    french_words = ["avec", "dans", "pour", "sur", "compétences", "expérience", 
                    "développement", "données", "ingénieur"]
    
    # Compter occurrences
    french_count = sum(1 for word in french_words if word in text_lower)
    
    # Si plusieurs mots français, c'est probablement du français
    return "fr" if french_count >= 2 else "en"


# ============================================
# EXTRACTION NLP
# ============================================

def extract_skills_with_nlp(text: str, known_skills: Set[str] = None) -> List[str]:
    """
    Extrait les compétences avec NLP (spaCy).
    
    Méthodes utilisées:
    1. Named Entity Recognition (PRODUCT, ORG)
    2. POS Tagging (PROPN - noms propres)
    3. Patterns linguistiques contextuels
    4. Validation contre liste de compétences connues
    
    Args:
        text: Texte à analyser
        known_skills: Set de compétences connues (optionnel)
    
    Returns:
        Liste de compétences extraites
    """
    if not text or not isinstance(text, str):
        return []
    
    if not SPACY_AVAILABLE:
        print("⚠️  spaCy non disponible, utiliser Pattern Matching")
        return []
    
    # Utiliser la base de données par défaut
    if known_skills is None:
        known_skills = get_all_skills()
    
    # Détecter la langue
    lang = detect_language(text)
    
    # Charger le modèle spaCy
    try:
        nlp = load_nlp_model(lang)
    except (ImportError, OSError) as e:
        print(f"⚠️  Erreur chargement modèle spaCy: {e}")
        return []
    
    found_skills = set()
    
    # Traiter le texte avec spaCy
    doc = nlp(text[:1000000])  # Limiter à 1M caractères pour performance
    
    # Méthode 1 : Named Entity Recognition
    for ent in doc.ents:
        if ent.label_ in ["PRODUCT", "ORG", "WORK_OF_ART"]:
            skill_candidate = ent.text.strip()
            if _is_valid_skill(skill_candidate, known_skills):
                found_skills.add(skill_candidate)
    
    # Méthode 2 : POS Tagging - Noms propres
    for token in doc:
        if token.pos_ == "PROPN":  # Nom propre
            skill_candidate = token.text.strip()
            if _is_valid_skill(skill_candidate, known_skills):
                found_skills.add(skill_candidate)
    
    # Méthode 3 : Patterns contextuels
    context_keywords = SKILL_CONTEXT_KEYWORDS.get(lang, SKILL_CONTEXT_KEYWORDS["en"])
    
    for sent in doc.sents:
        sent_lower = sent.text.lower()
        
        # Si la phrase contient un mot-clé contextuel
        if any(keyword in sent_lower for keyword in context_keywords):
            # Extraire les noms propres de cette phrase
            for token in sent:
                if token.pos_ in ["PROPN", "NOUN"]:
                    skill_candidate = token.text.strip()
                    if _is_valid_skill(skill_candidate, known_skills):
                        found_skills.add(skill_candidate)
    
    # Méthode 4 : Pattern Matching classique (backup)
    # Chercher les compétences connues directement
    text_lower = text.lower()
    for skill in known_skills:
        pattern = r'(?<![a-zA-Z])' + re.escape(skill.lower()) + r'(?![a-zA-Z])'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    
    # Normaliser et filtrer
    normalized_skills = set()
    for skill in found_skills:
        normalized = normalize_skill(skill)
        # Vérifier si normalisé existe dans known_skills
        for known_skill in known_skills:
            if normalized.lower() == known_skill.lower():
                normalized_skills.add(known_skill)
                break
    
    return sorted(list(normalized_skills))


def _is_valid_skill(candidate: str, known_skills: Set[str]) -> bool:
    """
    Vérifie si un candidat est une compétence valide.
    
    Args:
        candidate: Candidat à valider
        known_skills: Set de compétences connues
    
    Returns:
        True si valide
    """
    if not candidate or len(candidate) < 2:
        return False
    
    # Trop long = probablement pas une compétence
    if len(candidate) > 30:
        return False
    
    # Vérifier si dans la liste connue (case-insensitive)
    candidate_lower = candidate.lower()
    for skill in known_skills:
        if candidate_lower == skill.lower():
            return True
    
    # Vérifier variations
    if candidate_lower in SKILL_VARIATIONS:
        return True
    
    return False


# ============================================
# EXTRACTION DEPUIS PROFIL
# ============================================

def extract_skills_from_profile_nlp(profile: Dict) -> List[str]:
    """
    Extrait les compétences d'un profil avec NLP.
    
    Args:
        profile: Dictionnaire du profil
    
    Returns:
        Liste de compétences
    """
    all_text = []
    
    # Extraire tous les textes
    if profile.get('resume'):
        all_text.append(profile.get('resume'))
    
    if profile.get('position'):
        all_text.append(profile.get('position'))
    
    experiences = profile.get('experience', [])
    for exp in experiences:
        if exp.get('position'):
            all_text.append(exp.get('position'))
        
        description = exp.get('description', [])
        if isinstance(description, list):
            all_text.extend(description)
        elif isinstance(description, str):
            all_text.append(description)
    
    formations = profile.get('formation', [])
    for formation in formations:
        if formation.get('degree'):
            all_text.append(formation.get('degree'))
    
    existing_skills = profile.get('skills', [])
    if existing_skills:
        all_text.append(', '.join(existing_skills))
    
    # Combiner
    combined_text = ' '.join(filter(None, all_text))
    
    # Extraire avec NLP
    skills = extract_skills_with_nlp(combined_text)
    
    return skills


# ============================================
# STATISTIQUES
# ============================================

def get_skills_statistics_nlp(profiles: List[Dict]) -> Dict:
    """
    Calcule des statistiques sur les compétences (NLP).
    
    Args:
        profiles: Liste de profils
    
    Returns:
        Dictionnaire avec statistiques
    """
    all_skills = []
    skills_per_profile = []
    
    for profile in profiles:
        skills = extract_skills_from_profile_nlp(profile)
        all_skills.extend(skills)
        skills_per_profile.append(len(skills))
    
    skill_counts = Counter(all_skills)
    
    stats = {
        "total_profiles": len(profiles),
        "profiles_with_skills": len([s for s in skills_per_profile if s > 0]),
        "avg_skills_per_profile": sum(skills_per_profile) / len(skills_per_profile) if skills_per_profile else 0,
        "min_skills": min(skills_per_profile) if skills_per_profile else 0,
        "max_skills": max(skills_per_profile) if skills_per_profile else 0,
        "unique_skills": len(skill_counts),
        "top_20_skills": skill_counts.most_common(20)
    }
    
    return stats


# ============================================
# EXPORT
# ============================================

__all__ = [
    "extract_skills_with_nlp",
    "extract_skills_from_profile_nlp",
    "get_skills_statistics_nlp",
    "detect_language",
    "load_nlp_model"
]