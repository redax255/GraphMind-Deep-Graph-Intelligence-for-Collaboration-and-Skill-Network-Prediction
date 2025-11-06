"""
Pipeline d'enrichissement principal.
Orchestre toutes les étapes d'enrichissement des profils.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.services.database import MongoDBClient
from app.utils.profile_enricher import ProfileEnricher


class EnrichmentPipeline:
    """
    Pipeline complet d'enrichissement des profils LinkedIn.
    
    Étapes :
    1. Chargement profils MongoDB
    2. Enrichissement (compétences, normalisations, dates)
    3. Calcul statistiques
    4. Sauvegarde profils enrichis
    5. Génération rapport
    
    Usage:
        pipeline = EnrichmentPipeline()
        results = pipeline.run()
    """
    
    def __init__(
        self,
        output_collection: str = "linkedin_profiles_enriched",
        save_report: bool = True,
        report_dir: str = "data/reports"
    ):
        """
        Args:
            output_collection: Nom collection MongoDB pour profils enrichis
            save_report: Si True, sauvegarde un rapport JSON
            report_dir: Dossier pour rapports
        """
        self.output_collection = output_collection
        self.save_report = save_report
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Composants
        self.enricher = ProfileEnricher()
        
        # Métriques
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'duration_seconds': None,
            'profiles_loaded': 0,
            'profiles_enriched': 0,
            'profiles_saved': 0,
            'errors': []
        }
    
    def run(self, limit: Optional[int] = None) -> Dict:
        """
        Exécute le pipeline complet.
        
        Args:
            limit: Limite de profils à traiter (None = tous)
        
        Returns:
            Dictionnaire avec résultats et métriques
        """
        print("="*80)
        print("🚀 PIPELINE D'ENRICHISSEMENT - DÉMARRAGE")
        print("="*80)
        print()
        
        self.metrics['start_time'] = datetime.now()
        
        try:
            # Étape 1 : Charger profils
            profiles = self._load_profiles(limit)
            
            # Étape 2 : Enrichir profils
            enriched_profiles = self._enrich_profiles(profiles)
            
            # Étape 3 : Sauvegarder profils enrichis
            self._save_profiles(enriched_profiles)
            
            # Étape 4 : Générer rapport
            report = self._generate_report(enriched_profiles)
            
            # Étape 5 : Sauvegarder rapport
            if self.save_report:
                self._save_report(report)
            
            self.metrics['end_time'] = datetime.now()
            self.metrics['duration_seconds'] = (
                self.metrics['end_time'] - self.metrics['start_time']
            ).total_seconds()
            
            print()
            print("="*80)
            print("✅ PIPELINE TERMINÉ AVEC SUCCÈS")
            print("="*80)
            print()
            print(f"⏱️  Durée : {self.metrics['duration_seconds']:.1f}s")
            print(f"✅ Profils enrichis : {self.metrics['profiles_enriched']}")
            print(f"✅ Profils sauvegardés : {self.metrics['profiles_saved']}")
            
            if self.metrics['errors']:
                print(f"⚠️  Erreurs : {len(self.metrics['errors'])}")
            
            return {
                'success': True,
                'metrics': self.metrics,
                'report': report
            }
            
        except Exception as e:
            self.metrics['end_time'] = datetime.now()
            print()
            print("="*80)
            print(f"❌ ERREUR PIPELINE : {e}")
            print("="*80)
            
            return {
                'success': False,
                'error': str(e),
                'metrics': self.metrics
            }
    
    def _load_profiles(self, limit: Optional[int] = None) -> List[Dict]:
        """Charge les profils depuis MongoDB."""
        print("📥 ÉTAPE 1/4 : Chargement des profils")
        print("-" * 80)
        
        with MongoDBClient() as db:
            if limit:
                profiles = db.profiles_collection.find().limit(limit)
            else:
                profiles = db.get_all_profiles()
            
            profiles = list(profiles)
        
        self.metrics['profiles_loaded'] = len(profiles)
        
        print(f"✅ {len(profiles)} profils chargés")
        print()
        
        return profiles
    
    def _enrich_profiles(self, profiles: List[Dict]) -> List[Dict]:
        """Enrichit tous les profils."""
        print("🔬 ÉTAPE 2/4 : Enrichissement des profils")
        print("-" * 80)
        
        enriched_profiles = self.enricher.enrich_batch(profiles)
        
        self.metrics['profiles_enriched'] = len(enriched_profiles)
        
        # Compter erreurs
        errors = [p for p in enriched_profiles if '_enrichment_error' in p]
        if errors:
            self.metrics['errors'] = [
                {
                    'profile_id': str(p.get('_id')),
                    'error': p.get('_enrichment_error')
                }
                for p in errors
            ]
        
        print()
        return enriched_profiles
    
    def _save_profiles(self, enriched_profiles: List[Dict]) -> None:
        """Sauvegarde les profils enrichis dans MongoDB."""
        print("💾 ÉTAPE 3/4 : Sauvegarde des profils enrichis")
        print("-" * 80)
        
        with MongoDBClient(collection_name=self.output_collection) as db:
            # Supprimer collection existante
            db.collection.delete_many({})
            print(f"   Collection '{self.output_collection}' vidée")
            
            # Insérer profils enrichis
            if enriched_profiles:
                db.collection.insert_many(enriched_profiles)
                self.metrics['profiles_saved'] = len(enriched_profiles)
                print(f"✅ {len(enriched_profiles)} profils sauvegardés")
            else:
                print("⚠️  Aucun profil à sauvegarder")
        
        print()
    
    def _generate_report(self, enriched_profiles: List[Dict]) -> Dict:
        """Génère un rapport d'enrichissement."""
        print("📊 ÉTAPE 4/4 : Génération du rapport")
        print("-" * 80)
        
        report = {
            'pipeline_info': {
                'run_date': datetime.now().isoformat(),
                'duration_seconds': (
                    datetime.now() - self.metrics['start_time']
                ).total_seconds(),
                'output_collection': self.output_collection
            },
            'profiles': {
                'loaded': self.metrics['profiles_loaded'],
                'enriched': self.metrics['profiles_enriched'],
                'saved': self.metrics['profiles_saved'],
                'errors': len(self.metrics['errors'])
            },
            'enrichment_stats': self._calculate_enrichment_stats(enriched_profiles),
            'errors': self.metrics['errors'][:10]  # Top 10 erreurs
        }
        
        print("✅ Rapport généré")
        print()
        
        return report
    
    def _calculate_enrichment_stats(self, enriched_profiles: List[Dict]) -> Dict:
        """Calcule les statistiques d'enrichissement."""
        if not enriched_profiles:
            return {}
        
        stats = {
            'skills': {
                'profiles_with_skills': 0,
                'avg_skills_per_profile': 0,
                'total_skills': 0,
                'unique_categories': set()
            },
            'experiences': {
                'profiles_with_experience': 0,
                'avg_experience_months': 0,
                'profiles_with_current_position': 0,
                'total_companies': set()
            },
            'education': {
                'profiles_with_education': 0,
                'total_schools': set()
            },
            'dates': {
                'experiences_parsed': 0,
                'experiences_with_errors': 0,
                'education_parsed': 0,
                'education_with_errors': 0
            }
        }
        
        for profile in enriched_profiles:
            # Compétences
            skills_count = profile.get('skills_count', 0)
            if skills_count > 0:
                stats['skills']['profiles_with_skills'] += 1
                stats['skills']['total_skills'] += skills_count
            
            skills_by_cat = profile.get('skills_by_category', {})
            stats['skills']['unique_categories'].update(skills_by_cat.keys())
            
            # Expériences
            experiences = profile.get('experience_enriched', [])
            if experiences:
                stats['experiences']['profiles_with_experience'] += 1
            
            profile_stats = profile.get('stats', {})
            exp_months = profile_stats.get('total_experience_months', 0)
            if exp_months > 0:
                stats['experiences']['avg_experience_months'] += exp_months
            
            if profile_stats.get('current_positions_count', 0) > 0:
                stats['experiences']['profiles_with_current_position'] += 1
            
            # Entreprises uniques
            for exp in experiences:
                company = exp.get('company_normalized') or exp.get('company')
                if company:
                    # Gérer le cas où company est un dict
                    if isinstance(company, dict):
                        company_name = company.get('normalized_name') or company.get('name') or str(company)
                    else:
                        company_name = str(company)
                    stats['experiences']['total_companies'].add(company_name)
            
            # Dates expériences
            for exp in experiences:
                if 'dates_parsed' in exp:
                    stats['dates']['experiences_parsed'] += 1
                    if exp['dates_parsed'].get('error'):
                        stats['dates']['experiences_with_errors'] += 1
            
            # Formations
            education = profile.get('education_enriched', [])
            if education:
                stats['education']['profiles_with_education'] += 1
            
            for edu in education:
                school = edu.get('university_normalized') or edu.get('university')
                if school:
                    # Gérer le cas où school est un dict
                    if isinstance(school, dict):
                        school_name = school.get('normalized_name') or school.get('name') or str(school)
                    else:
                        school_name = str(school)
                    stats['education']['total_schools'].add(school_name)
                
                if 'dates_parsed' in edu:
                    stats['dates']['education_parsed'] += 1
                    if edu['dates_parsed'].get('error'):
                        stats['dates']['education_with_errors'] += 1
        
        # Calculer moyennes
        total_profiles = len(enriched_profiles)
        
        if stats['skills']['profiles_with_skills'] > 0:
            stats['skills']['avg_skills_per_profile'] = round(
                stats['skills']['total_skills'] / stats['skills']['profiles_with_skills'],
                1
            )
        
        if stats['experiences']['profiles_with_experience'] > 0:
            stats['experiences']['avg_experience_months'] = round(
                stats['experiences']['avg_experience_months'] / stats['experiences']['profiles_with_experience'],
                1
            )
            stats['experiences']['avg_experience_years'] = round(
                stats['experiences']['avg_experience_months'] / 12,
                1
            )
        
        # Convertir sets en listes pour JSON
        stats['skills']['unique_categories'] = list(stats['skills']['unique_categories'])
        stats['experiences']['total_companies'] = len(stats['experiences']['total_companies'])
        stats['education']['total_schools'] = len(stats['education']['total_schools'])
        
        # Calculer taux de succès parsing
        total_exp_parsed = stats['dates']['experiences_parsed']
        if total_exp_parsed > 0:
            stats['dates']['experiences_success_rate'] = round(
                (total_exp_parsed - stats['dates']['experiences_with_errors']) / total_exp_parsed * 100,
                1
            )
        
        total_edu_parsed = stats['dates']['education_parsed']
        if total_edu_parsed > 0:
            stats['dates']['education_success_rate'] = round(
                (total_edu_parsed - stats['dates']['education_with_errors']) / total_edu_parsed * 100,
                1
            )
        
        return stats
    
    def _save_report(self, report: Dict) -> None:
        """Sauvegarde le rapport en JSON."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.report_dir / f"enrichment_report_{timestamp}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Rapport sauvegardé : {report_path}")


def main():
    """Point d'entrée principal."""
    pipeline = EnrichmentPipeline()
    results = pipeline.run()
    
    if results['success']:
        print("\n🎉 Pipeline exécuté avec succès !")
        return 0
    else:
        print(f"\n❌ Pipeline échoué : {results.get('error')}")
        return 1


if __name__ == "__main__":
    exit(main())