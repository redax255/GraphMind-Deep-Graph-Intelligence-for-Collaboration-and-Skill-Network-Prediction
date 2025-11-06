"""
Test de normalisation des écoles sur la base MongoDB complète.
"""

import sys
from pathlib import Path
from collections import Counter

sys.path.append(str(Path(__file__).parent))

from app.services.database import MongoDBClient
from app.utils.school_normalizer_ml import SchoolNormalizerML


def extract_schools_from_profiles(profiles):
    """Extrait toutes les écoles des profils."""
    all_schools = []
    
    for profile in profiles:
        formations = profile.get('formation', [])
        for formation in formations:
            school = formation.get('university')
            if school and isinstance(school, str) and school.strip():
                all_schools.append(school.strip())
    
    return all_schools


def main():
    print("="*80)
    print("🎓 TEST NORMALISATION ÉCOLES (ML)")
    print("="*80)
    print()
    
    # 1. Charger profils
    print("🔄 Chargement des profils...")
    with MongoDBClient() as db:
        profiles = db.get_all_profiles()
    print(f"✅ {len(profiles)} profils chargés")
    print()
    
    # 2. Extraire écoles
    print("🔄 Extraction des écoles...")
    all_schools = extract_schools_from_profiles(profiles)
    unique_schools = sorted(set(all_schools))
    
    print(f"✅ {len(all_schools)} écoles extraites (total)")
    print(f"✅ {len(unique_schools)} écoles uniques (brutes)")
    print()
    
    # 3. Normaliser avec ML
    normalizer = SchoolNormalizerML(use_cache=True)
    normalizations = normalizer.normalize_schools(unique_schools)
    
    # 4. Statistiques détaillées
    print()
    print("="*80)
    print("📊 STATISTIQUES DÉTAILLÉES")
    print("="*80)
    print()
    
    # Compter écoles normalisées
    normalized_schools = [normalizations[school] for school in all_schools]
    school_counts_normalized = Counter(normalized_schools)
    
    unique_normalized = len(set(normalized_schools))
    reduction = (1 - unique_normalized / len(unique_schools)) * 100
    
    print(f"✅ Écoles uniques (avant) : {len(unique_schools)}")
    print(f"✅ Écoles uniques (après) : {unique_normalized}")
    print(f"✅ Réduction : {reduction:.1f}%")
    print()
    
    # Distribution
    schools_1 = sum(1 for count in school_counts_normalized.values() if count == 1)
    schools_5plus = sum(1 for count in school_counts_normalized.values() if count >= 5)
    schools_10plus = sum(1 for count in school_counts_normalized.values() if count >= 10)
    
    print(f"✅ Écoles avec 1 profil : {schools_1} ({schools_1/unique_normalized*100:.1f}%)")
    print(f"✅ Écoles avec 5+ profils : {schools_5plus} ({schools_5plus/unique_normalized*100:.1f}%)")
    print(f"✅ Écoles avec 10+ profils : {schools_10plus}")
    print()
    
    # Top écoles normalisées
    print("="*80)
    print("📊 TOP 20 ÉCOLES NORMALISÉES")
    print("="*80)
    print()
    print(f"{'#':<4} {'École':<65} {'Profils':<8} {'%':<6}")
    print("-" * 85)
    
    for i, (school, count) in enumerate(school_counts_normalized.most_common(20), 1):
        pct = count / len(profiles) * 100
        display_school = school if len(school) <= 64 else school[:61] + "..."
        print(f"{i:<4} {display_school:<65} {count:<8} {pct:<6.1f}%")
    
    # Clusters formés
    print()
    print("="*80)
    print("📋 EXEMPLES DE CLUSTERS FORMÉS")
    print("="*80)
    print()
    
    # Grouper par école normalisée
    from collections import defaultdict
    clusters = defaultdict(list)
    
    for original, normalized in normalizations.items():
        clusters[normalized].append(original)
    
    # Filtrer clusters avec variations
    multi_variation_clusters = {k: v for k, v in clusters.items() if len(v) > 1}
    
    if multi_variation_clusters:
        print(f"✅ {len(multi_variation_clusters)} clusters formés")
        print()
        
        # Trier par nombre de profils
        clusters_sorted = sorted(
            multi_variation_clusters.items(),
            key=lambda x: sum(Counter(all_schools)[var] for var in x[1]),
            reverse=True
        )
        
        # Afficher top 15
        for i, (normalized, variations) in enumerate(clusters_sorted[:15], 1):
            total_profiles = sum(Counter(all_schools)[var] for var in variations)
            print(f"{i}. '{normalized}' ← {len(variations)} variations ({total_profiles} profils) :")
            for var in sorted(variations):
                count = Counter(all_schools)[var]
                if var != normalized:
                    display_var = var if len(var) <= 55 else var[:52] + "..."
                    print(f"      - {display_var:<55} ({count} profils)")
            print()
    else:
        print("ℹ️  Aucun cluster formé (toutes les écoles sont déjà normalisées)")
    
    # Validation qualité
    print("="*80)
    print("✅ VALIDATION QUALITÉ")
    print("="*80)
    print()
    
    # Vérifier top école
    top_school, top_count = school_counts_normalized.most_common(1)[0]
    top_pct = top_count / len(profiles) * 100
    
    print(f"✅ Top 1 école : {top_school} ({top_pct:.1f}%)")
    
    if top_pct > 30:
        print(f"⚠️  ATTENTION : Top école > 30% (possible mega-cluster)")
    else:
        print(f"✅ Distribution réaliste (top < 30%)")
    
    print()
    
    # Cas particuliers à vérifier
    test_cases = [
        ("ENSIAS", "Ecole Nationale Supérieure d'Informatique"),
        ("INPT", "Institut National des Postes"),
        ("Université Ibn Tofail", "Ibn tofaïl university"),
    ]
    
    print("🔍 Vérification cas particuliers :")
    for school_a, school_b in test_cases:
        # Chercher dans normalizations
        norm_a = normalizations.get(school_a, "N/A")
        norm_b = normalizations.get(school_b, "N/A")
        
        if school_a in normalizations or school_b in normalizations:
            same = norm_a == norm_b
            status = "✅ Groupées" if same else "✅ Séparées"
            print(f"   {school_a} vs {school_b} : {status}")
    
    print()
    print("="*80)
    print("✅ TEST TERMINÉ")
    print("="*80)


if __name__ == "__main__":
    main()