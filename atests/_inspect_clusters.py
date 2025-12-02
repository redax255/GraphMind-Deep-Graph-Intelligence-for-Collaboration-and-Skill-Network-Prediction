"""
Script pour inspecter les clusters formés et valider leur qualité.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.database import MongoDBClient
from app.utils.company_normalizer_ml import (
    CompanyNormalizerML,
    normalize_all_companies_global
)


def inspect_clusters():
    """
    Inspecte les clusters formés pour valider la qualité.
    """
    
    print("="*80)
    print("🔍 INSPECTION DES CLUSTERS")
    print("="*80)
    print()
    
    try:
        with MongoDBClient() as db:
            profiles = db.get_all_profiles()
            print(f"✅ {len(profiles)} profils chargés\n")
            
            # Initialiser normaliseur
            print("⏳ Initialisation normaliseur...")
            normalizer = CompanyNormalizerML()
            print()
            
            # Normaliser globalement
            normalized_map = normalize_all_companies_global(profiles, normalizer)
            
            print()
            print("-"*80)
            print("📊 ANALYSE DES CLUSTERS")
            print("-"*80)
            
            # Inverser le mapping : normalized → [brutes]
            from collections import defaultdict
            inverse_map = defaultdict(list)
            
            for brute, normalized in normalized_map.items():
                inverse_map[normalized].append(brute)
            
            # Filtrer clusters (2+ variations)
            clusters = {
                norm: brutes 
                for norm, brutes in inverse_map.items() 
                if len(set(brutes)) > 1
            }
            
            print(f"\n✅ {len(clusters)} cluster(s) avec variations multiples")
            
            if clusters:
                print("\n📋 CLUSTERS FORMÉS :\n")
                
                # Trier par nombre de variations
                sorted_clusters = sorted(
                    clusters.items(), 
                    key=lambda x: len(set(x[1])), 
                    reverse=True
                )
                
                for i, (normalized, brutes) in enumerate(sorted_clusters, 1):
                    unique_brutes = list(set(brutes))
                    
                    print(f"{i:2d}. '{normalized}' ← {len(unique_brutes)} variation(s)")
                    
                    for brute in sorted(unique_brutes)[:10]:
                        print(f"      - {brute}")
                    
                    if len(unique_brutes) > 10:
                        print(f"      ... et {len(unique_brutes)-10} autres")
                    
                    print()
                
                # Validation manuelle
                print()
                print("-"*80)
                print("✅ VALIDATION")
                print("-"*80)
                
                print("\nVérifiez manuellement :")
                print("  1. Les variations sont-elles similaires ?")
                print("  2. Pas de groupement d'entreprises différentes ?")
                print()
                
                # Clusters suspects (>5 variations)
                large_clusters = [
                    (norm, brutes) 
                    for norm, brutes in sorted_clusters 
                    if len(set(brutes)) > 5
                ]
                
                if large_clusters:
                    print("⚠️  CLUSTERS LARGES (>5 variations) :")
                    for norm, brutes in large_clusters:
                        print(f"   - {norm} : {len(set(brutes))} variations")
                    print()
            else:
                print("\n✅ Aucun cluster multi-variations")
                print("   (eps très strict, tout est considéré unique)")
            
            print()
            print("="*80)
            print("✅ INSPECTION TERMINÉE")
            print("="*80)
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    inspect_clusters()