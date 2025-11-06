"""
Module d'extraction de compétences depuis les textes de profils.

Extrait les compétences techniques depuis :
- Champ resume
- Champs description dans experience[]
"""

import re
from typing import List, Set, Dict
from collections import Counter

from app.utils.skills_database import (
    get_all_skills,
    normalize_skill,
    SKILL_VARIATIONS
)


# ============================================
# CONFIGURATION
# ============================================

# Patterns à ignorer (faux positifs)
IGNORE_PATTERNS = {
    "go", "c", "r"  # Trop courts, beaucoup de faux positifs
}

# Mots contextuels qui indiquent une compétence
SKILL_CONTEXT_WORDS = {
    "compétences", "skills", "technologies", "outils", "tools",
    "stack", "langage", "language", "framework", "using", "avec",
    "utilisant", "maîtrise", "expérience", "experience"
}


# ============================================
# EXTRACTION PRINCIPALE
# ============================================

def extract_skills_from_text(text: str, known_skills: Set[str] = None) -> List[str]:
    """
    Extrait les compétences techniques d'un texte.
    
    Args:
        text: Texte à analyser (resume ou description)
        known_skills: Set de compétences connues (optionnel)
    
    Returns:
        Liste de compétences uniques trouvées
    
    Example:
        >>> text = "Expert en Python, SQL et Docker. Utilise React et Node.js"
        >>> extract_skills_from_text(text)
        ['Python', 'SQL', 'Docker', 'React', 'Node.js']
    """
    if not text or not isinstance(text, str):
        return []
    
    # Utiliser la base de données par défaut si non fournie
    if known_skills is None:
        known_skills = get_all_skills()
    
    found_skills = set()
    
    # Nettoyer et normaliser le texte
    text_lower = text.lower()
    
    # Méthode 1 : Recherche par mots-clés exacts (case-insensitive)
    for skill in known_skills:
        skill_lower = skill.lower()
        
        # Pattern plus flexible : accepte avec ou sans ponctuation autour
        pattern = r'(?<![a-zA-Z])' + re.escape(skill_lower) + r'(?![a-zA-Z])'
        
        if re.search(pattern, text_lower):
            # Ignorer les compétences trop courtes sauf si contexte clair
            if len(skill) <= 2 and skill.lower() in IGNORE_PATTERNS:
                if not _has_clear_context(text_lower, skill_lower):
                    continue
            
            found_skills.add(skill)
    
    # Méthode 2 : Recherche de variations connues
    for variation, normalized in SKILL_VARIATIONS.items():
        pattern = r'(?<![a-zA-Z])' + re.escape(variation) + r'(?![a-zA-Z])'
        if re.search(pattern, text_lower):
            found_skills.add(normalized)
    
    # Méthode 3 : Détection de patterns spéciaux
    special_skills = _extract_special_patterns(text)
    for skill in special_skills:
        normalized = normalize_skill(skill)
        # Recherche fuzzy dans known_skills
        for known_skill in known_skills:
            if normalized.lower() == known_skill.lower():
                found_skills.add(known_skill)
                break
    
    return sorted(list(found_skills))


def _has_clear_context(text: str, skill: str) -> bool:
    """
    Vérifie si une compétence courte a un contexte clair.
    
    Args:
        text: Texte complet
        skill: Compétence à vérifier
    
    Returns:
        True si contexte clair
    """
    # Chercher "langage C", "language C", "C programming", etc.
    context_patterns = [
        f"langage {skill}",
        f"language {skill}",
        f"{skill} programming",
        f"{skill} developer",
        f"programmation {skill}"
    ]
    
    for pattern in context_patterns:
        if pattern in text:
            return True
    
    return False


def _extract_special_patterns(text: str) -> List[str]:
    """
    Extrait les compétences des patterns spéciaux.
    
    Patterns détectés :
    - "Python · SQL · Docker"
    - "Python, SQL, Docker"
    - "Python | SQL | Docker"
    - "Compétences : Python, SQL"
    - "Python/SQL/Docker"
    - "Technologies: Python SQL Docker"
    
    Args:
        text: Texte à analyser
    
    Returns:
        Liste de compétences extraites
    """
    skills = []
    
    # Pattern 1 : "Compétences : Python, SQL, Docker"
    skills_section_pattern = r'(?:compétences?|skills?|technologies?|stack|outils?|tools?)\s*[:·\-]\s*([^.\n]+)'
    matches = re.finditer(skills_section_pattern, text, re.IGNORECASE)
    
    for match in matches:
        skills_text = match.group(1)
        # Splitter par virgules, points, pipes, slashes
        parts = re.split(r'[,·|•/]+', skills_text)
        for part in parts:
            skill = part.strip()
            if skill and len(skill) > 1 and len(skill) < 30:
                skills.append(skill)
    
    # Pattern 2 : Listes avec tirets ou puces
    # - Python
    # - SQL
    bullet_pattern = r'(?:^|\n)\s*[•\-\*]\s*([A-Za-z][A-Za-z0-9\s\.\+\#]{1,25})'
    matches = re.finditer(bullet_pattern, text, re.MULTILINE)
    
    for match in matches:
        skill = match.group(1).strip()
        if skill and len(skill) > 1:
            skills.append(skill)
    
    # Pattern 3 : Entre parenthèses
    # (Python, SQL, Docker)
    paren_pattern = r'\(([A-Za-z][A-Za-z0-9,\s\.\+\#/|·]{2,100})\)'
    matches = re.finditer(paren_pattern, text)
    
    for match in matches:
        content = match.group(1)
        parts = re.split(r'[,/|·]+', content)
        for part in parts:
            skill = part.strip()
            if skill and len(skill) > 1 and len(skill) < 30:
                skills.append(skill)
    
    return skills


# ============================================
# EXTRACTION DEPUIS PROFIL COMPLET
# ============================================

def extract_skills_from_profile(profile: Dict) -> List[str]:
    """
    Extrait toutes les compétences d'un profil complet.
    
    Args:
        profile: Dictionnaire du profil (depuis MongoDB)
    
    Returns:
        Liste de compétences uniques
    
    Example:
        >>> profile = {
        ...     "resume": "Expert Python et SQL...",
        ...     "experience": [{"description": ["Docker, Kubernetes"]}]
        ... }
        >>> extract_skills_from_profile(profile)
        ['Python', 'SQL', 'Docker', 'Kubernetes']
    """
    all_text = []
    
    # 1. Extraire depuis resume
    resume = profile.get('resume', '')
    if resume:
        all_text.append(resume)
    
    # 2. Extraire depuis position (titre du poste actuel)
    position = profile.get('position', '')
    if position:
        all_text.append(position)
    
    # 3. Extraire depuis experience
    experiences = profile.get('experience', [])
    for exp in experiences:
        # Position dans l'expérience
        if exp.get('position'):
            all_text.append(exp.get('position'))
        
        # Description peut être une liste ou un string
        description = exp.get('description', [])
        
        if isinstance(description, list):
            all_text.extend(description)
        elif isinstance(description, str):
            all_text.append(description)
        
        # Entreprise (peut contenir des technos)
        if exp.get('company'):
            all_text.append(exp.get('company'))
    
    # 4. Extraire depuis formation (peut avoir des cours/projets)
    formations = profile.get('formation', [])
    for formation in formations:
        if formation.get('degree'):
            all_text.append(formation.get('degree'))
    
    # 5. Extraire depuis skills[] existants (même si souvent vide)
    existing_skills = profile.get('skills', [])
    if existing_skills:
        all_text.append(', '.join(existing_skills))
    
    # 6. Combiner tout le texte
    combined_text = ' '.join(filter(None, all_text))
    
    # 7. Extraire les compétences
    skills = extract_skills_from_text(combined_text)
    
    return skills


# ============================================
# STATISTIQUES
# ============================================

def get_skills_statistics(profiles: List[Dict]) -> Dict:
    """
    Calcule des statistiques sur les compétences extraites.
    
    Args:
        profiles: Liste de profils
    
    Returns:
        Dictionnaire avec statistiques
    """
    all_skills = []
    skills_per_profile = []
    
    for profile in profiles:
        skills = extract_skills_from_profile(profile)
        all_skills.extend(skills)
        skills_per_profile.append(len(skills))
    
    # Compter les occurrences
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
# UTILITAIRES
# ============================================

def clean_skill_text(text: str) -> str:
    """
    Nettoie un texte de compétence.
    
    Args:
        text: Texte à nettoyer
    
    Returns:
        Texte nettoyé
    """
    # Supprimer les caractères spéciaux excessifs
    text = re.sub(r'[^\w\s\.\-\+\#]', ' ', text)
    
    # Normaliser les espaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


# ============================================
# EXPORT
# ============================================

__all__ = [
    "extract_skills_from_text",
    "extract_skills_from_profile",
    "get_skills_statistics"
]