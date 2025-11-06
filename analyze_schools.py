"""
Analyse des écoles/universités dans la base de données.
Détecte les doublons potentiels et prépare la normalisation.
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.append(str(Path(__file__).parent))

from app.services.database import MongoDBClient


def extract_schools_from_profiles(profiles):
    """Extrait toutes les écoles des profils."""
    all_schools = []
    profiles_with_formation = 0
    
    for profile in profiles:
        # Formation
        formations = profile.get('formation', [])
        if formations:
            profiles_with_formation += 1
            
        for formation in formations:
            # Clé 'university'
            school = formation.get('university')
            if school and isinstance(school, str) and school.strip():
                all_schools.append(school.strip())
    
    print(f"ℹ️  Profils avec formation : {profiles_with_formation}/{len(profiles)} ({profiles_with_formation/len(profiles)*100:.1f}%)")
    
    return all_schools


def main():
    print("="*80)
    print("🎓 ANALYSE DES ÉCOLES")
    print("="*80)
    print()
    
    # Charger profils
    with MongoDBClient() as db:
        profiles = db.get_all_profiles()
        print(f"✅ {len(profiles)} profils chargés\n")
    
    # Extraire écoles
    all_schools = extract_schools_from_profiles(profiles)
    
    print(f"✅ {len(all_schools)} écoles extraites (total)")
    
    # Si aucune école trouvée
    if not all_schools:
        print("\n❌ AUCUNE ÉCOLE TROUVÉE")
        print("\n🔍 Vérification de la structure des données...")
        
        # Debug : afficher structure d'un profil avec formation
        for profile in profiles[:10]:
            if profile.get('formation'):
                print(f"\n📋 Exemple de formation trouvée :")
                print(f"   Profil : {profile.get('first_name')} {profile.get('last_name')}")
                print(f"   Formation : {profile.get('formation')}")
                break
        
        return
    
    # Écoles uniques
    unique_schools = set(all_schools)
    print(f"✅ {len(unique_schools)} écoles uniques (brutes)")
    print()
    
    # Compter occurrences
    school_counts = Counter(all_schools)
    
    # Statistiques
    print("="*80)
    print("📊 STATISTIQUES")
    print("="*80)
    print()
    
    schools_1 = sum(1 for count in school_counts.values() if count == 1)
    schools_2_4 = sum(1 for count in school_counts.values() if 2 <= count <= 4)
    schools_5plus = sum(1 for count in school_counts.values() if count >= 5)
    schools_10plus = sum(1 for count in school_counts.values() if count >= 10)
    
    print(f"✅ Écoles avec 1 profil : {schools_1} ({schools_1/len(school_counts)*100:.1f}%)")
    print(f"✅ Écoles avec 2-4 profils : {schools_2_4} ({schools_2_4/len(school_counts)*100:.1f}%)")
    print(f"✅ Écoles avec 5+ profils : {schools_5plus} ({schools_5plus/len(school_counts)*100:.1f}%)")
    print(f"✅ Écoles avec 10+ profils : {schools_10plus}")
    print()
    
    # Profils sans formation
    profiles_without_formation = sum(1 for p in profiles if not p.get('formation'))
    print(f"⚠️  Profils sans formation : {profiles_without_formation} ({profiles_without_formation/len(profiles)*100:.1f}%)")
    print()
    
    # Top 30
    print("="*80)
    print("📊 TOP 30 ÉCOLES")
    print("="*80)
    print()
    print(f"{'#':<4} {'École':<65} {'Profils':<8} {'%':<6}")
    print("-" * 85)
    
    for i, (school, count) in enumerate(school_counts.most_common(30), 1):
        pct = count / len(profiles) * 100
        # Tronquer si trop long
        display_school = school if len(school) <= 64 else school[:61] + "..."
        print(f"{i:<4} {display_school:<65} {count:<8} {pct:<6.1f}%")
    
    # Détecter doublons potentiels
    print()
    print("="*80)
    print("🔍 DÉTECTION DE DOUBLONS POTENTIELS")
    print("="*80)
    print()
    
    # Grouper par similarité simple (lowercase, sans espaces)
    normalized_simple = defaultdict(list)
    for school in unique_schools:
        # Normalisation simple
        simple_key = (school.lower()
                      .replace(" ", "")
                      .replace("-", "")
                      .replace("'", "")
                      .replace("'", "")
                      .replace("é", "e")
                      .replace("è", "e")
                      .replace("ê", "e")
                      .replace("à", "a")
                      .replace("ô", "o"))
        normalized_simple[simple_key].append(school)
    
    # Filtrer groupes avec variations
    potential_duplicates = {k: v for k, v in normalized_simple.items() if len(v) > 1}
    
    if potential_duplicates:
        print(f"⚠️  {len(potential_duplicates)} groupes de doublons potentiels détectés")
        print()
        
        # Afficher top 20
        count_displayed = 0
        for key, schools in sorted(potential_duplicates.items(), 
                                   key=lambda x: sum(school_counts[s] for s in x[1]), 
                                   reverse=True):
            if count_displayed >= 20:
                break
            
            total_profiles = sum(school_counts[s] for s in schools)
            print(f"{count_displayed+1}. {len(schools)} variations ({total_profiles} profils au total) :")
            for school in sorted(schools):
                count = school_counts[school]
                display_school = school if len(school) <= 55 else school[:52] + "..."
                print(f"      - {display_school:<55} ({count} profils)")
            print()
            count_displayed += 1
            
        if len(potential_duplicates) > 20:
            print(f"   ... et {len(potential_duplicates) - 20} autres groupes")
    else:
        print("✅ Aucun doublon évident détecté")
    
    # Patterns communs
    print()
    print("="*80)
    print("🔍 PATTERNS COMMUNS À NETTOYER")
    print("="*80)
    print()
    
    # Détecter suffixes/préfixes
    patterns = {
        'Diplômes': ["Bachelor", "Master", "PhD", "Doctorat", "Licence", "Ingénieur", "DUT", "BTS"],
        'Types': ["École", "Université", "University", "Institut", "Institute", "Ecole", "Faculté"],
        'Symboles': ["·", "|", "/", "\\"],
        'Écoles Maroc': ["ENSIAS", "INPT", "EMI", "ENSAM", "INSEA", "UM6P", "ENSA", "FST", "ENSEM"]
    }
    
    patterns_found = defaultdict(lambda: defaultdict(int))
    
    for school in all_schools:
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern.lower() in school.lower():
                    patterns_found[category][pattern] += 1
    
    for category in ['Diplômes', 'Types', 'Symboles', 'Écoles Maroc']:
        if patterns_found[category]:
            print(f"📋 {category} :")
            for pattern, count in sorted(patterns_found[category].items(), 
                                        key=lambda x: x[1], reverse=True)[:10]:
                pct = count / len(all_schools) * 100
                print(f"   - '{pattern}' : {count} fois ({pct:.1f}%)")
            print()
    
    # Statistiques textuelles
    print("="*80)
    print("📏 STATISTIQUES TEXTUELLES")
    print("="*80)
    print()
    
    # Longueur moyenne des noms d'écoles
    avg_length = sum(len(school) for school in all_schools) / len(all_schools)
    print(f"📏 Longueur moyenne : {avg_length:.1f} caractères")
    
    # Écoles avec des caractères spéciaux
    schools_with_special = sum(1 for school in all_schools 
                              if any(c in school for c in ['·', '|', '/', '\\']))
    print(f"⚠️  Avec caractères spéciaux : {schools_with_special} ({schools_with_special/len(all_schools)*100:.1f}%)")
    
    # Écoles en plusieurs mots
    multi_word = sum(1 for school in all_schools if len(school.split()) > 3)
    print(f"📝 Noms longs (>3 mots) : {multi_word} ({multi_word/len(all_schools)*100:.1f}%)")
    
    print()
    print("="*80)
    print("✅ ANALYSE TERMINÉE")
    print("="*80)
    print()
    
    # Estimation après normalisation
    estimated_reduction = 0.15  # 15% réduction estimée
    estimated_final = int(len(unique_schools) * (1 - estimated_reduction))
    
    print("💡 Prochaines étapes :")
    print("   1. ✅ Créer school_normalizer_ml.py")
    print("   2. ✅ Adapter suffixes spécifiques écoles :")
    print("      - Supprimer : '·', 'Bachelor', 'Master', 'Licence', etc.")
    print("   3. ✅ Utiliser Sentence-BERT + DBSCAN (eps=0.03)")
    print("   4. ✅ Tester et valider les clusters")
    print()
    print(f"📊 Estimation après normalisation : {len(unique_schools)} → ~{estimated_final} écoles uniques")
    print(f"   (Réduction estimée : {int(estimated_reduction*100)}%)")


if __name__ == "__main__":
    main()