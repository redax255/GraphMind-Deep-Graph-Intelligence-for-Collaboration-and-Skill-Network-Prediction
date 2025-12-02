"""
Test de normalisation ML des entreprises avec visualisation.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.database import MongoDBClient
from app.utils.company_normalizer_ml import (
    CompanyNormalizerML,
    normalize_companies_from_profile,
    get_company_statistics
)


def print_separator(char="=", length=80):
    print(char * length)


def main():
    print_separator()
    print("🧪 TEST - NORMALISATION ML DES ENTREPRISES")
    print("   Sentence-BERT + DBSCAN Clustering")
    print_separator()
    print()
    
    # Vérifier sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ sentence-transformers installé")
    except ImportError:
        print("❌ sentence-transformers NON installé")
        print()
        print("Installation requise:")
        print("  pip install sentence-transformers")
        return
    
    print()
    
    # Test unitaire
    print_separator()
    print("📋 TEST UNITAIRE - Normalisation simple")
    print_separator()
    print()
    
    print("⏳ Initialisation du normaliseur ML...")
    normalizer = CompanyNormalizerML()
    
    print()
    print("🧪 Test sur exemples :")
    
    test_cases = [
        ["Capgemini Morocco", "capgemini maroc", "Capgemini · Temps plein"],
        ["SQLI Group", "sqli", "SQLI Maroc"],
        ["OCP Group", "ocp", "Office Chérifien des Phosphates"],
    ]
    
    for i, cases in enumerate(test_cases, 1):
        print(f"\n{i}. Test groupe {i} :")
        print(f"   Input  : {cases}")
        
        normalized = normalizer.normalize_companies_batch(cases)
        unique_normalized = set(normalized.values())
        
        print(f"   Output : {unique_normalized}")
        print(f"   ✅ {len(unique_normalized)} entreprise(s) unique(s)")
    
    # Test sur profils réels
    print()
    print_separator()
    print("📊 TEST SUR PROFILS RÉELS")
    print_separator()
    
    try:
        with MongoDBClient() as db:
            print("\n✅ Connexion MongoDB OK")
            
            profiles = db.get_all_profiles()
            print(f"📊 {len(profiles)} profils chargés\n")
            
            # Exemples sur 5 profils
            print_separator("-")
            print("🔍 EXTRACTION (5 premiers profils)")
            print_separator("-")
            
            for i, profile in enumerate(profiles[:5], 1):
                name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}"
                print(f"\n{i}. {name}")
                
                # Extraire entreprises brutes
                raw_companies = []
                for exp in profile.get('experience', []):
                    if exp.get('company'):
                        raw_companies.append(exp.get('company'))
                
                if raw_companies:
                    print(f"   Brut  : {raw_companies[:3]}")
                    if len(raw_companies) > 3:
                        print(f"           ... et {len(raw_companies)-3} autres")
                    
                    # Normaliser
                    normalized = normalize_companies_from_profile(profile, normalizer)
                    print(f"   Normalisé : {sorted(normalized)}")
                else:
                    print(f"   ❌ Aucune entreprise")
            
            # Statistiques globales
            print()
            print_separator()
            print("📈 STATISTIQUES GLOBALES - CLUSTERING GLOBAL")
            print_separator()
            
            print("\n⏳ Normalisation globale (clustering sur toutes les entreprises)...")
            print("   Cela peut prendre 1-2 minutes...")
            
            stats = get_company_statistics(profiles, normalizer, use_global_clustering=True)
            
            print(f"\n✅ Total profils : {stats['total_profiles']}")
            print(f"✅ Entreprises uniques : {stats['unique_companies']}")
            print(f"✅ Entreprises avec 1 profil : {stats['companies_with_1_profile']} ({stats['companies_with_1_profile']/stats['unique_companies']*100:.1f}%)")
            print(f"✅ Entreprises avec 5+ profils : {stats['companies_with_5plus_profiles']}")
            print(f"✅ Entreprises avec 10+ profils : {stats['companies_with_10plus_profiles']}")
            
            print(f"\n📊 TOP 20 ENTREPRISES :")
            print(f"{'#':<4} {'Entreprise':<35} {'Profils':<10} {'%':<10}")
            print("-" * 80)
            for i, (company, count) in enumerate(stats['top_20_companies'], 1):
                percentage = (count / stats['total_profiles']) * 100
                print(f"{i:<4} {company:<35} {count:<10} {percentage:>5.1f}%")
            
            # Validation
            print()
            print_separator()
            print("✅ VALIDATION")
            print_separator()
            
            unique = stats['unique_companies']
            
            if unique >= 80:
                print(f"\n✅ {unique} entreprises uniques ≥ 80 ✓")
            else:
                print(f"\n⚠️  {unique} entreprises uniques < 80 (objectif: 80+)")
            
            # Taux de clustering
            clustered = stats['companies_with_5plus_profiles']
            clustering_rate = (clustered / unique) * 100
            
            print(f"✅ Entreprises majeures (5+ profils) : {clustered} ({clustering_rate:.1f}%)")
            
            if clustering_rate >= 10:
                print(f"✅ Taux de clustering ≥ 10% ✓")
            else:
                print(f"⚠️  Taux de clustering {clustering_rate:.1f}% < 10%")
            
            # Entreprises 10+
            major = stats['companies_with_10plus_profiles']
            if major > 0:
                print(f"✅ Entreprises très représentées (10+ profils) : {major}")
            
            print()
            print_separator()
            print("✅ TEST TERMINÉ")
            print_separator()
            
            print()
            print("💡 Info : Les embeddings et normalizations sont sauvegardés dans data/cache/")
            print("   Prochaines exécutions seront plus rapides grâce au cache !")
    
    except Exception as e:
        print()
        print_separator()
        print("❌ ERREUR")
        print_separator()
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()