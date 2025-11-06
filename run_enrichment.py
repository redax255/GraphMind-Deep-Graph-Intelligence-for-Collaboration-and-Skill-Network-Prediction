"""
Script d'exécution du pipeline d'enrichissement en PRODUCTION.
Lance l'enrichissement sur TOUS les profils.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.utils.enrichment_pipeline import EnrichmentPipeline


def main():
    print("="*80)
    print("🚀 ENRICHISSEMENT PRODUCTION - TOUS LES PROFILS")
    print("="*80)
    print()
    
    confirmation = input("⚠️  Cette opération va enrichir TOUS les profils. Continuer ? (oui/non) : ")
    
    if confirmation.lower() not in ['oui', 'yes', 'y']:
        print("❌ Opération annulée")
        return 0
    
    print()
    print("🔄 Démarrage du pipeline d'enrichissement...")
    print()
    
    # Créer pipeline
    pipeline = EnrichmentPipeline(
        output_collection="linkedin_profiles_enriched",
        save_report=True,
        report_dir="data/reports"
    )
    
    # Exécuter sur TOUS les profils
    results = pipeline.run()
    
    # Afficher résultats
    print()
    
    if results['success']:
        report = results['report']
        
        print("="*80)
        print("🎉 ENRICHISSEMENT TERMINÉ AVEC SUCCÈS !")
        print("="*80)
        print()
        
        # Afficher statistiques clés
        profiles_stats = report['profiles']
        enrich_stats = report['enrichment_stats']
        
        print(f"📊 Profils enrichis : {profiles_stats['enriched']}/{profiles_stats['loaded']}")
        print(f"⏱️  Durée : {report['pipeline_info']['duration_seconds']:.1f}s")
        print()
        
        print("🔬 Statistiques d'enrichissement :")
        skills = enrich_stats.get('skills', {})
        print(f"   - Compétences extraites : {skills.get('profiles_with_skills', 0)} profils")
        
        exp = enrich_stats.get('experiences', {})
        print(f"   - Expériences normalisées : {exp.get('profiles_with_experience', 0)} profils")
        print(f"   - Expérience moyenne : {exp.get('avg_experience_years', 0)} ans")
        
        dates = enrich_stats.get('dates', {})
        print(f"   - Dates parsées : {dates.get('experiences_success_rate', 0)}% succès")
        print()
        
        print(f"💾 Collection MongoDB : {report['pipeline_info']['output_collection']}")
        print()
        
        if profiles_stats['errors'] > 0:
            print(f"⚠️  {profiles_stats['errors']} profils avec erreurs (voir rapport)")
            print()
        
        print("✅ Les profils enrichis sont prêts pour la Phase 3 (Graph Construction) !")
        
    else:
        print("="*80)
        print("❌ ENRICHISSEMENT ÉCHOUÉ")
        print("="*80)
        print()
        print(f"Erreur : {results.get('error')}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())