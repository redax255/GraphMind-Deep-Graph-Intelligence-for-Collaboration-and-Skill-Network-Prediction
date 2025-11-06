"""
Profile Enricher - Enrichit un profil avec compétences, normalisations et dates.

Utilisé par le pipeline d'enrichissement principal.
"""

from typing import Dict, List, Optional
from datetime import datetime

from app.utils.skill_extractor import ExtractionMethod, SkillExtractor
from app.utils.company_normalizer_ml import CompanyNormalizerML
from app.utils.school_normalizer_ml import SchoolNormalizerML
from app.utils.date_parser import IntelligentDateParser


class ProfileEnricher:
    """
    Enrichit un profil LinkedIn avec toutes les normalisations et extractions.
    
    Usage:
        enricher = ProfileEnricher()
        enriched_profile = enricher.enrich(profile)
    """
    
    def __init__(self):
        """Initialise tous les composants d'enrichissement."""
        print("🔧 Initialisation ProfileEnricher...")
        
        # Composants
        self.skill_extractor = SkillExtractor(method=ExtractionMethod.NLP)
        self.company_normalizer = CompanyNormalizerML()
        self.school_normalizer = SchoolNormalizerML()
        self.date_parser = IntelligentDateParser()
        
        print("✅ ProfileEnricher initialisé")
    
    def enrich(self, profile: Dict) -> Dict:
        """
        Enrichit un profil complet.
        
        Args:
            profile: Profil brut depuis MongoDB
        
        Returns:
            Profil enrichi avec toutes les normalisations
        """
        # Créer copie pour ne pas modifier l'original
        enriched = profile.copy()
        
        # Marquer comme enrichi
        enriched['_enriched'] = True
        enriched['_enriched_at'] = datetime.now().isoformat()
        
        # 1. Enrichir compétences
        enriched = self._enrich_skills(enriched)
        
        # 2. Enrichir expériences
        enriched = self._enrich_experiences(enriched)
        
        # 3. Enrichir formations
        enriched = self._enrich_education(enriched)
        
        # 4. Calculer statistiques
        enriched = self._calculate_stats(enriched)
        
        return enriched
    
    def _enrich_skills(self, profile: Dict) -> Dict:
        """
        Extrait et enrichit les compétences.
        
        Args:
            profile: Profil à enrichir
        
        Returns:
            Profil avec compétences enrichies
        """
        # Extraire compétences depuis about + expériences
        extracted_skills = self.skill_extractor.extract_from_profile(profile)
        
        # Ajouter au profil
        profile['skills_extracted'] = extracted_skills
        profile['skills_count'] = len(extracted_skills)
        
        # Grouper par catégorie
        skills_by_category = {}
        for skill_data in extracted_skills:
            # Gérer le cas où skill_data est une string ou un dict
            if isinstance(skill_data, str):
                # Si c'est une string, créer un dict
                skill_dict = {'skill': skill_data, 'category': 'Unknown'}
            else:
                skill_dict = skill_data
            
            category = skill_dict.get('category', 'Unknown')
            skill_name = skill_dict.get('skill', skill_data if isinstance(skill_data, str) else 'Unknown')
            
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(skill_name)
        
        profile['skills_by_category'] = skills_by_category
        
        return profile
    
    def _enrich_experiences(self, profile: Dict) -> Dict:
        """
        Enrichit les expériences avec normalisation et dates.
        
        Args:
            profile: Profil à enrichir
        
        Returns:
            Profil avec expériences enrichies
        """
        experiences = profile.get('experience', [])
        
        if not experiences:
            profile['experience_enriched'] = []
            return profile
        
        enriched_experiences = []
        
        for exp in experiences:
            exp_enriched = exp.copy()
            
            # Normaliser entreprise
            company = exp.get('company', '')
            if company:
                normalized_company = self.company_normalizer.normalize_company(company)
                exp_enriched['company_normalized'] = normalized_company
            
            # Parser dates
            period = exp.get('period', '')
            if period:
                parsed_dates = self.date_parser.parse_period(period)
                exp_enriched['dates_parsed'] = parsed_dates
                exp_enriched['start_date'] = parsed_dates.get('start_date')
                exp_enriched['end_date'] = parsed_dates.get('end_date')
                exp_enriched['duration_months'] = parsed_dates.get('duration_months')
                exp_enriched['is_current'] = parsed_dates.get('is_current', False)
            
            enriched_experiences.append(exp_enriched)
        
        profile['experience_enriched'] = enriched_experiences
        
        return profile
    
    def _enrich_education(self, profile: Dict) -> Dict:
        """
        Enrichit les formations avec normalisation et dates.
        
        Args:
            profile: Profil à enrichir
        
        Returns:
            Profil avec formations enrichies
        """
        education = profile.get('formation', [])
        
        if not education:
            profile['education_enriched'] = []
            return profile
        
        enriched_education = []
        
        for edu in education:
            edu_enriched = edu.copy()
            
            # Normaliser école
            university = edu.get('university', '')
            if university:
                normalized_school = self.school_normalizer.normalize_schools(university)
                edu_enriched['university_normalized'] = normalized_school
            
            # Parser dates
            period = edu.get('period', '')
            if period:
                parsed_dates = self.date_parser.parse_education_period(period)
                edu_enriched['dates_parsed'] = parsed_dates
                edu_enriched['start_date'] = parsed_dates.get('start_date')
                edu_enriched['end_date'] = parsed_dates.get('end_date')
                edu_enriched['duration_months'] = parsed_dates.get('duration_months')
            
            enriched_education.append(edu_enriched)
        
        profile['education_enriched'] = enriched_education
        
        return profile
    
    def _calculate_stats(self, profile: Dict) -> Dict:
        """
        Calcule les statistiques du profil.
        
        Args:
            profile: Profil enrichi
        
        Returns:
            Profil avec statistiques
        """
        stats = {}
        
        # Statistiques expériences
        experiences = profile.get('experience_enriched', [])
        
        total_experience_months = 0
        companies_worked = set()
        current_positions = 0
        
        for exp in experiences:
            # Durée totale
            duration = exp.get('duration_months')
            if duration and isinstance(duration, (int, float)):
                total_experience_months += duration
            
            # Entreprises uniques
            company = exp.get('company_normalized') or exp.get('company')
            if company:
                # Gérer le cas où company est un dict
                if isinstance(company, dict):
                    company_name = company.get('normalized_name') or company.get('name') or str(company)
                else:
                    company_name = str(company)
                companies_worked.add(company_name)
            
            # Postes actuels
            if exp.get('is_current'):
                current_positions += 1
        
        stats['total_experience_months'] = total_experience_months
        stats['total_experience_years'] = round(total_experience_months / 12, 1)
        stats['companies_count'] = len(companies_worked)
        stats['current_positions_count'] = current_positions
        stats['experiences_count'] = len(experiences)
        
        # Statistiques formations
        education = profile.get('education_enriched', [])
        schools_attended = set()
        
        for edu in education:
            school = edu.get('university_normalized') or edu.get('university')
            if school:
                # Gérer le cas où school est un dict
                if isinstance(school, dict):
                    school_name = school.get('normalized_name') or school.get('name') or str(school)
                else:
                    school_name = str(school)
                schools_attended.add(school_name)
        
        stats['schools_count'] = len(schools_attended)
        stats['education_count'] = len(education)
        
        # Statistiques compétences
        stats['skills_count'] = profile.get('skills_count', 0)
        skills_by_cat = profile.get('skills_by_category', {})
        stats['skills_categories'] = list(skills_by_cat.keys())
        stats['skills_categories_count'] = len(skills_by_cat)
        
        profile['stats'] = stats
        
        return profile
    
    def enrich_batch(self, profiles: List[Dict]) -> List[Dict]:
        """
        Enrichit un lot de profils.
        
        Args:
            profiles: Liste de profils bruts
        
        Returns:
            Liste de profils enrichis
        """
        enriched_profiles = []
        
        print(f"\n🔄 Enrichissement de {len(profiles)} profils...")
        
        for i, profile in enumerate(profiles, 1):
            if i % 50 == 0:
                print(f"   Progression : {i}/{len(profiles)} ({i/len(profiles)*100:.1f}%)")
            
            try:
                enriched = self.enrich(profile)
                enriched_profiles.append(enriched)
            except Exception as e:
                print(f"⚠️  Erreur profil {profile.get('_id')} : {e}")
                # Ajouter profil non enrichi avec marqueur d'erreur
                profile['_enrichment_error'] = str(e)
                enriched_profiles.append(profile)
        
        print(f"✅ {len(enriched_profiles)} profils enrichis")
        
        return enriched_profiles