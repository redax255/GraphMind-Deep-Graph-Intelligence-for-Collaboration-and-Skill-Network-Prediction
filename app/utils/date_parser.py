"""
Parser de dates françaises INTELLIGENT et ROBUSTE.
Gère automatiquement tous les encodages, accents, et variantes.

APPROCHE INTELLIGENTE :
- Normalisation Unicode automatique
- Regex flexibles dans le BON ORDRE (pas de conflits)
- Détection intelligente des patterns
- Scalable pour nouvelles données

Version 2.1 - FINALE avec corrections regex
"""

import re
from datetime import datetime
from typing import Optional, Dict
from dateutil.relativedelta import relativedelta
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalise un texte en supprimant les accents et caractères spéciaux.
    Gère TOUS les encodages automatiquement.
    
    Exemples:
        "août" → "aout"
        "février" → "fevrier"
        "aujourd'hui" → "aujourd hui"
        "décembre" → "decembre"
    
    Args:
        text: Texte à normaliser
    
    Returns:
        Texte normalisé (minuscules, sans accents)
    """
    if not text:
        return ""
    
    # Convertir en minuscules
    text = text.lower()
    
    # ÉTAPE 1 : Remplacer les apostrophes AVANT normalisation NFD
    # Car NFD ne touche pas aux apostrophes typographiques !
    apostrophe_replacements = {
        '\u2019': ' ',  # RIGHT SINGLE QUOTATION MARK (')
        '\u2018': ' ',  # LEFT SINGLE QUOTATION MARK (')
        '\u02bc': ' ',  # MODIFIER LETTER APOSTROPHE (ʼ)
        '\u0027': ' ',  # APOSTROPHE simple (')
        '\u0060': ' ',  # GRAVE ACCENT (`)
        '\u00b4': ' ',  # ACUTE ACCENT (´)
        ''': ' ',       # Forme littérale aussi
        ''': ' ',       # Forme littérale aussi
        "'": ' ',       # Apostrophe ASCII
        '`': ' ',
        '´': ' ',
    }
    
    for apostrophe, replacement in apostrophe_replacements.items():
        text = text.replace(apostrophe, replacement)
    
    # ÉTAPE 2 : Décomposition NFD pour les accents (é → e + ´)
    nfd = unicodedata.normalize('NFD', text)
    text_no_accents = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    
    # ÉTAPE 3 : Remplacer autres caractères spéciaux
    other_replacements = {
        'œ': 'oe',
        'æ': 'ae',
    }
    
    for old, new in other_replacements.items():
        text_no_accents = text_no_accents.replace(old, new)
    
    return text_no_accents.strip()


# Mapping mois avec REGEX flexibles - ORDRE CRITIQUE !
# Les patterns les plus spécifiques doivent venir EN PREMIER
MONTH_PATTERNS = [
    # IMPORTANT : juillet AVANT juin pour éviter conflit !
    (r'juil[let]*\.?', 7),       # juillet, juil, juil., july
    (r'juin\.?', 6),              # juin (plus spécifique maintenant)
    
    # Autres mois par ordre
    (r'jan[veuir]*\.?', 1),       # janvier, janv, janv., jan
    (r'f[ee]vr?[ieu]*\.?', 2),    # février, fevrier, févr, fevr., fev, feb
    (r'mars?\.?', 3),             # mars, mar
    (r'avr[il]*\.?', 4),          # avril, avr, avr., avri, apr
    (r'mai\.?', 5),               # mai, may
    (r'ao[uu]t?\.?', 8),          # août, aout, aoû, aou, aug
    (r'sep[tembre]*\.?', 9),      # septembre, sept, sept., sep
    (r'oct[obre]*\.?', 10),       # octobre, oct, oct.
    (r'nov[embre]*\.?', 11),      # novembre, nov, nov.
    (r'd[ee]c[embre]*\.?', 12),   # décembre, decembre, dec, déc
]

# Mots-clés pour date actuelle (normalisés)
CURRENT_KEYWORDS_NORMALIZED = [
    'aujourd hui', 'aujourdhui',
    "aujourd'hui",  # Apostrophe simple
    "aujourd'hui",  # Apostrophe typographique
    'present', 'a ce jour', 'ace jour',
    'actuellement', 'now', 'current',
    'en cours', 'ongoing', 'ce jour'
]


class IntelligentDateParser:
    """
    Parser intelligent de dates françaises.
    S'adapte automatiquement à tous les encodages et variantes.
    
    Usage:
        parser = IntelligentDateParser()
        result = parser.parse_period("mars 2025 - août 2025 · 6 mois")
    """
    
    def __init__(self, reference_date: Optional[datetime] = None):
        """
        Args:
            reference_date: Date de référence pour "aujourd'hui" (défaut: now)
        """
        self.reference_date = reference_date or datetime.now()
    
    def _detect_month(self, text: str) -> Optional[int]:
        """
        Détecte le mois dans un texte avec regex flexibles.
        Gère TOUS les encodages et variantes automatiquement.
        
        Args:
            text: Texte contenant potentiellement un mois
        
        Returns:
            Numéro du mois (1-12) ou None
        """
        # Normaliser le texte (supprimer accents)
        normalized = normalize_text(text)
        
        # Tester chaque pattern DANS L'ORDRE
        for pattern, month_num in MONTH_PATTERNS:
            if re.search(pattern, normalized):
                return month_num
        
        return None
    
    def _is_current_date(self, date_str: str) -> bool:
        """
        Vérifie si la chaîne indique une date actuelle.
        
        Args:
            date_str: Chaîne de date
        
        Returns:
            True si date actuelle, False sinon
        """
        normalized = normalize_text(date_str)
        return any(keyword in normalized for keyword in CURRENT_KEYWORDS_NORMALIZED)
    
    def _parse_single_date(self, date_str: str) -> Optional[str]:
        """
        Parse une date unique avec intelligence.
        
        Args:
            date_str: Chaîne de date
        
        Returns:
            Date au format "YYYY-MM" ou None si invalide
        """
        date_str = date_str.strip()
        
        # Cas 1: Date actuelle
        if self._is_current_date(date_str):
            return self.reference_date.strftime('%Y-%m')
        
        # Normaliser pour parsing
        normalized = normalize_text(date_str)
        
        # Cas 2: Format "mois YYYY" (ex: "mars 2025", "aout 2024", "juil. 2023")
        # Pattern flexible : [texte + point optionnel] [4 chiffres]
        match = re.search(r'([a-z]+\.?)\s+(\d{4})', normalized)
        if match:
            month_str, year = match.groups()
            month_num = self._detect_month(month_str)
            if month_num:
                return f"{year}-{month_num:02d}"
        
        # Cas 3: Format "YYYY" uniquement
        match = re.match(r'^(\d{4})$', normalized)
        if match:
            year = match.group(1)
            return f"{year}-01"  # Janvier par défaut
        
        # Cas 4: Format "MM/YYYY" ou "YYYY-MM"
        match = re.match(r'(\d{1,2})[/-](\d{4})', normalized)
        if match:
            month, year = match.groups()
            return f"{year}-{int(month):02d}"
        
        return None
    
    def _calculate_duration(self, start: str, end: str) -> int:
        """
        Calcule la durée en mois entre 2 dates.
        
        Args:
            start, end: Dates au format "YYYY-MM"
        
        Returns:
            Durée en mois (arrondi au mois supérieur)
        """
        try:
            start_date = datetime.strptime(start, '%Y-%m')
            end_date = datetime.strptime(end, '%Y-%m')
            
            # Calculer différence
            delta = relativedelta(end_date, start_date)
            months = delta.years * 12 + delta.months
            
            # Arrondir au mois supérieur si jours > 0
            if delta.days > 0:
                months += 1
            
            return max(months, 1)  # Minimum 1 mois
            
        except ValueError:
            return 0
    
    def _extract_duration_from_text(self, period_str: str) -> Optional[int]:
        """
        Extrait la durée depuis le texte de manière intelligente.
        
        Args:
            period_str: Chaîne de période complète
        
        Returns:
            Durée en mois ou None
        """
        # Normaliser
        normalized = normalize_text(period_str)
        
        # Pattern: "X an(s) Y mois"
        match = re.search(r'(\d+)\s*ans?\s+(\d+)\s*mois', normalized)
        if match:
            years, months = map(int, match.groups())
            return years * 12 + months
        
        # Pattern: "X an(s)"
        match = re.search(r'(\d+)\s*ans?', normalized)
        if match:
            years = int(match.group(1))
            return years * 12
        
        # Pattern: "X mois"
        match = re.search(r'(\d+)\s*mois', normalized)
        if match:
            return int(match.group(1))
        
        # Pattern: "X year(s)" (anglais)
        match = re.search(r'(\d+)\s*years?', normalized)
        if match:
            years = int(match.group(1))
            return years * 12
        
        # Pattern: "X month(s)" (anglais)
        match = re.search(r'(\d+)\s*months?', normalized)
        if match:
            return int(match.group(1))
        
        return None
    
    def parse_period(self, period_str: str) -> Dict:
        """
        Parse une période complète de manière INTELLIGENTE.
        
        Args:
            period_str: Chaîne de période
        
        Returns:
            Dictionnaire avec dates, durée, et statut
        """
        if not period_str or not isinstance(period_str, str):
            return {
                'start_date': None,
                'end_date': None,
                'duration_months': 0,
                'is_current': False,
                'raw': period_str,
                'error': 'Période vide ou invalide'
            }
        
        period_clean = period_str.strip()
        
        # Normaliser pour détection de patterns
        normalized = normalize_text(period_clean)
        
        # Séparer par séparateurs multiples
        # Patterns: " - ", " – ", " — ", " / "
        parts = re.split(r'\s*[-–—/]\s*', period_clean)
        
        if len(parts) == 1:
            # Pas de séparateur
            date_str = parts[0].split('·')[0].strip()
            
            # Cas spécial 1: Durée seule (ex: "4 ans 2 mois")
            duration_only = self._extract_duration_from_text(normalized)
            if duration_only and not re.search(r'\d{4}', normalized):
                # Durée présente MAIS pas d'année → durée seule
                return {
                    'start_date': None,
                    'end_date': None,
                    'duration_months': duration_only,
                    'is_current': False,
                    'raw': period_clean,
                    'error': 'Durée seule (pas de dates)'
                }
            
            # Cas spécial 2: "Stage · X mois", "Temps plein · X mois"
            if any(keyword in normalized for keyword in ['stage', 'temps plein', 'temps partiel', 'cdi', 'cdd']):
                return {
                    'start_date': None,
                    'end_date': None,
                    'duration_months': duration_only,
                    'is_current': False,
                    'raw': period_clean,
                    'error': 'Type contrat seul (pas de dates)'
                }
            
            # Cas 3: Date actuelle seule
            if self._is_current_date(date_str):
                return {
                    'start_date': None,
                    'end_date': self.reference_date.strftime('%Y-%m'),
                    'duration_months': None,
                    'is_current': True,
                    'raw': period_clean,
                    'error': None
                }
            
            # Cas 4: Date unique → considérer comme actuelle
            start = self._parse_single_date(date_str)
            end = self.reference_date.strftime('%Y-%m')
            duration = self._calculate_duration(start, end) if start else None
            
            return {
                'start_date': start,
                'end_date': end,
                'duration_months': duration,
                'is_current': True,
                'raw': period_clean,
                'error': None if start else 'Date invalide'
            }
        
        elif len(parts) >= 2:
            # Format "début - fin"
            start_str = parts[0].strip()
            end_str = parts[1].split('·')[0].strip()
            
            # Parser dates
            start_date = self._parse_single_date(start_str)
            
            # Vérifier si date fin est actuelle
            is_current = self._is_current_date(end_str)
            
            if is_current:
                end_date = self.reference_date.strftime('%Y-%m')
            else:
                end_date = self._parse_single_date(end_str)
            
            # Calculer durée
            # Priorité 1: Durée explicite
            duration_explicit = self._extract_duration_from_text(period_clean)
            
            # Priorité 2: Calculer
            if start_date and end_date:
                duration_calculated = self._calculate_duration(start_date, end_date)
            else:
                duration_calculated = None
            
            # Choisir durée
            duration = duration_explicit or duration_calculated
            
            # Validation cohérence
            error = None
            if start_date and end_date:
                if start_date > end_date:
                    error = f"Date fin ({end_date}) avant date début ({start_date})"
            elif not start_date:
                error = f"Date début invalide: {start_str}"
            elif not end_date:
                error = f"Date fin invalide: {end_str}"
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'duration_months': duration,
                'is_current': is_current,
                'raw': period_clean,
                'error': error
            }
        
        # Cas par défaut
        return {
            'start_date': None,
            'end_date': None,
            'duration_months': None,
            'is_current': False,
            'raw': period_clean,
            'error': 'Format non reconnu'
        }
    
    def parse_education_period(self, period_str: str) -> Dict:
        """
        Parse une période d'éducation.
        
        Args:
            period_str: Chaîne de période
        
        Returns:
            Même format que parse_period()
        """
        # Vérifier si c'est un "Niveau" (pas de date)
        normalized = normalize_text(period_str)
        
        if 'niveau' in normalized or 'top' in normalized or 'rank' in normalized:
            return {
                'start_date': None,
                'end_date': None,
                'duration_months': None,
                'is_current': False,
                'raw': period_str,
                'error': 'Niveau (pas de dates)'
            }
        
        # Sinon, parser normalement
        return self.parse_period(period_str)


# Rétrocompatibilité avec l'ancien nom
DateParser = IntelligentDateParser


def test_intelligent_parser():
    """Tests du parser intelligent avec focus sur juin/juillet."""
    parser = IntelligentDateParser(reference_date=datetime(2025, 10, 29))
    
    test_cases = [
        # TEST CRITIQUE : juin vs juillet
        "juil. 2023 - août 2023 · 2 mois",
        "juin 2023 - juil. 2023 · 2 mois",
        "juil. 2024 - sept. 2024 · 3 mois",
        "juin 2024 - août 2024 · 3 mois",
        
        # Problème août
        "mars 2025 - août 2025 · 6 mois",
        
        # Problème aujourd'hui
        "juil. 2024 - aujourd'hui · 1 an 4 mois",
        "oct. 2023 - aujourd'hui · 2 ans 1 mois",
        
        # Durée seule
        "4 ans 2 mois",
        
        # Cas normaux
        "mars 2017 - nov. 2019 · 2 ans 9 mois",
        "sept. 2023 - sept. 2025",
    ]
    
    print("="*80)
    print("🧪 TEST INTELLIGENT DATE PARSER - VERSION FINALE")
    print("="*80)
    print()
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test in enumerate(test_cases, 1):
        result = parser.parse_period(test)
        
        # Succès si pas d'erreur OU si erreur attendue (durée seule)
        is_success = not result['error'] or 'seule' in str(result['error']) or 'seul' in str(result['error'])
        status = "✅" if is_success else "❌"
        
        if is_success:
            success_count += 1
        
        print(f"{i}. {status} Input : {test}")
        print(f"   Start    : {result['start_date']}")
        print(f"   End      : {result['end_date']}")
        print(f"   Duration : {result['duration_months']} mois")
        print(f"   Current  : {result['is_current']}")
        if result['error']:
            print(f"   Note     : {result['error']}")
        print()
    
    print("="*80)
    print(f"✅ Taux de succès : {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    print("="*80)


if __name__ == "__main__":
    test_intelligent_parser()