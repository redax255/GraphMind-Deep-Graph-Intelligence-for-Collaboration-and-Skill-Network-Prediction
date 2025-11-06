"""
Test de l'extraction de compétences sur les profils MongoDB.
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.append(str(Path(__file__).parent))

from app.services.database import MongoDBClient
from app.utils.text_processing import extract_skills_from_profile, get_skills_statistics


def main():
    print("=" * 70)
    print("🧪 TEST - EXTRACTION DE COMPÉTENCES")
    print("=" * 70)
    print()
    
    try:
        # Connexion MongoDB
        with MongoDBClient() as db:
            print("✅ Connexion MongoDB OK")
            print()
            
            # Récupérer tous les profils
            profiles = db.get_all_profiles()
            print(f"📊 {len(profiles)} profils chargés")
            print()
            
            # Test sur les 3 premiers profils
            print("=" * 70)
            print("👤 TEST SUR 3 PROFILS")
            print("=" * 70)
            
            for i, profile in enumerate(profiles[:3], 1):
                print(f"\n--- Profil #{i} ---")
                name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}"
                print(f"Nom: {name}")
                print(f"Poste: {profile.get('position', 'N/A')}")
                
                # Extraire compétences
                skills = extract_skills_from_profile(profile)
                print(f"✅ {len(skills)} compétences extraites")
                
                if skills:
                    print(f"Compétences: {', '.join(skills[:15])}")
                    if len(skills) > 15:
                        print(f"            ... et {len(skills) - 15} autres")
            
            # Statistiques globales
            print()
            print("=" * 70)
            print("📊 STATISTIQUES GLOBALES")
            print("=" * 70)
            
            stats = get_skills_statistics(profiles)
            
            print(f"\n✅ Total profils: {stats['total_profiles']}")
            print(f"✅ Profils avec compétences: {stats['profiles_with_skills']} ({stats['profiles_with_skills']/stats['total_profiles']*100:.1f}%)")
            print(f"✅ Moyenne compétences/profil: {stats['avg_skills_per_profile']:.1f}")
            print(f"✅ Min compétences: {stats['min_skills']}")
            print(f"✅ Max compétences: {stats['max_skills']}")
            print(f"✅ Compétences uniques: {stats['unique_skills']}")
            
            print(f"\n📈 TOP 20 COMPÉTENCES :")
            for i, (skill, count) in enumerate(stats['top_20_skills'], 1):
                percentage = (count / stats['total_profiles']) * 100
                print(f"   {i:2d}. {skill:20s} : {count:3d} profils ({percentage:5.1f}%)")
            
            # Validation
            print()
            print("=" * 70)
            print("✅ VALIDATION")
            print("=" * 70)
            
            avg = stats['avg_skills_per_profile']
            coverage = stats['profiles_with_skills'] / stats['total_profiles'] * 100
            
            if avg >= 15:
                print(f"✅ Moyenne ≥ 15 compétences : {avg:.1f} ✓")
            else:
                print(f"⚠️  Moyenne < 15 compétences : {avg:.1f} (objectif: 15+)")
            
            if coverage >= 95:
                print(f"✅ Couverture ≥ 95% : {coverage:.1f}% ✓")
            else:
                print(f"⚠️  Couverture < 95% : {coverage:.1f}% (objectif: 95%+)")
            
            print()
            print("=" * 70)
            print("✅ TEST TERMINÉ")
            print("=" * 70)
    
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERREUR")
        print("=" * 70)
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()