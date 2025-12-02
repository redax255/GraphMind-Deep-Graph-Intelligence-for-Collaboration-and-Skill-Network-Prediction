"""
Test simple du pipeline d'enrichissement.
Teste sur quelques profils pour vérifier que tout fonctionne.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.utils.enrichment_pipeline import EnrichmentPipeline


def main():
    print("="*80)
    print("🧪 TEST PIPELINE D'ENRICHISSEMENT")
    print("="*80)
    print()
    
    # Test sur 5 profils seulement
    print("Mode TEST : Traitement de 5 profils uniquement")
    print()
    
    # Créer pipeline
    pipeline = EnrichmentPipeline(
        output_collection="linkedin_profiles_enriched_test",
        save_report=True,
        report_dir="data/reports/test"
    )
    
    # Exécuter sur 5 profils
    results = pipeline.run(limit=5)
    
    # Afficher résultats
    print()
    print("="*80)
    print("📊 RÉSUMÉ DU TEST")
    print("="*80)
    print()
    
    if results['success']:
        print("✅ Pipeline testé avec succès !")
        print()
        
        report = results['report']
        
        # Statistiques profils
        print("📋 PROFILS :")
        profiles_stats = report['profiles']
        print(f"   Chargés : {profiles_stats['loaded']}")
        print(f"   Enrichis : {profiles_stats['enriched']}")
        print(f"   Sauvegardés : {profiles_stats['saved']}")
        if profiles_stats['errors'] > 0:
            print(f"   ⚠️  Erreurs : {profiles_stats['errors']}")
        print()
        
        # Statistiques enrichissement
        enrich_stats = report['enrichment_stats']
        
        print("🔬 ENRICHISSEMENT :")
        
        # Compétences
        skills_stats = enrich_stats.get('skills', {})
        print(f"   Compétences :")
        print(f"      - Profils avec compétences : {skills_stats.get('profiles_with_skills', 0)}")
        print(f"      - Moyenne par profil : {skills_stats.get('avg_skills_per_profile', 0)}")
        print(f"      - Catégories uniques : {len(skills_stats.get('unique_categories', []))}")
        print()
        
        # Expériences
        exp_stats = enrich_stats.get('experiences', {})
        print(f"   Expériences :")
        print(f"      - Profils avec expérience : {exp_stats.get('profiles_with_experience', 0)}")
        print(f"      - Expérience moyenne : {exp_stats.get('avg_experience_years', 0)} ans")
        print(f"      - Postes actuels : {exp_stats.get('profiles_with_current_position', 0)}")
        print(f"      - Entreprises uniques : {exp_stats.get('total_companies', 0)}")
        print()
        
        # Formations
        edu_stats = enrich_stats.get('education', {})
        print(f"   Formations :")
        print(f"      - Profils avec formation : {edu_stats.get('profiles_with_education', 0)}")
        print(f"      - Écoles uniques : {edu_stats.get('total_schools', 0)}")
        print()
        
        # Dates
        dates_stats = enrich_stats.get('dates', {})
        print(f"   Parsing dates :")
        exp_parsed = dates_stats.get('experiences_parsed', 0)
        exp_success = dates_stats.get('experiences_success_rate', 0)
        print(f"      - Expériences parsées : {exp_parsed} ({exp_success}% succès)")
        
        edu_parsed = dates_stats.get('education_parsed', 0)
        edu_success = dates_stats.get('education_success_rate', 0)
        print(f"      - Formations parsées : {edu_parsed} ({edu_success}% succès)")
        print()
        
        # Performance
        duration = report['pipeline_info']['duration_seconds']
        print(f"⏱️  Durée totale : {duration:.1f}s")
        
        print()
        print("🎉 Test réussi ! Pipeline prêt pour production.")
        print()
        print("💡 Pour lancer sur TOUS les profils :")
        print("   python run_enrichment.py")
        
    else:
        print(f"❌ Test échoué : {results.get('error')}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())