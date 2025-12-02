"""
Script de test : Exploration des profils MongoDB.

Ce script permet de :
1. Tester la connexion MongoDB
2. Afficher des statistiques sur les 60+ profils
3. Analyser la qualité des données
4. Afficher des exemples de profils

Usage:
    python test_mongodb_connection.py
"""

import sys
import json
from pathlib import Path

# Ajouter le dossier parent au path pour importer les modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.database import MongoDBClient
from app.config import settings


def main():
    """Fonction principale"""
    
    print("=" * 70)
    print("🚀 TEST DE CONNEXION MONGODB - EXPLORATION DES PROFILS")
    print("=" * 70)
    print()
    
    # Afficher la configuration
    print("📋 Configuration:")
    print(f"   • MongoDB URI: {settings.mongodb_uri}")
    print(f"   • Database: {settings.mongodb_db_name}")
    print(f"   • Collection: {settings.mongodb_collection_profiles}")
    print()
    
    try:
        # Connexion à MongoDB
        with MongoDBClient() as db:
            
            # ============================================
            # 1. STATISTIQUES GÉNÉRALES
            # ============================================
            
            print("=" * 70)
            print("📊 STATISTIQUES GÉNÉRALES")
            print("=" * 70)
            
            total = db.get_total_profiles_count()
            print(f"✅ Nombre total de profils: {total}")
            print()
            
            # ============================================
            # 2. QUALITÉ DES DONNÉES
            # ============================================
            
            print("=" * 70)
            print("🔍 QUALITÉ DES DONNÉES")
            print("=" * 70)
            
            quality_stats = db.get_data_quality_stats()
            
            if quality_stats:
                print(f"   • Total profils: {quality_stats['total_profiles']}")
                print(f"   • Avec resume: {quality_stats['with_resume']} ({quality_stats['with_resume_percent']}%)")
                print(f"   • Avec expérience: {quality_stats['with_experience']} ({quality_stats['with_experience_percent']}%)")
                print(f"   • Avec formation: {quality_stats['with_formation']} ({quality_stats['with_formation_percent']}%)")
                print(f"   • Avec skills: {quality_stats['with_skills']} ({quality_stats['with_skills_percent']}%)")
                print(f"   • Avec location: {quality_stats['with_location']} ({quality_stats['with_location_percent']}%)")
            print()
            
            # ============================================
            # 3. DISTRIBUTION GÉOGRAPHIQUE
            # ============================================
            
            print("=" * 70)
            print("🌍 DISTRIBUTION GÉOGRAPHIQUE (TOP 10)")
            print("=" * 70)
            
            locations = db.get_profiles_by_location()
            for i, (location, count) in enumerate(list(locations.items())[:10], 1):
                print(f"   {i}. {location}: {count} profils")
            print()
            
            # ============================================
            # 4. EXEMPLES DE PROFILS
            # ============================================
            
            print("=" * 70)
            print("👤 EXEMPLES DE PROFILS (3 premiers)")
            print("=" * 70)
            
            profiles = db.get_all_profiles(limit=3)
            
            for i, profile in enumerate(profiles, 1):
                print(f"\n--- Profil #{i} ---")
                print(f"Nom: {profile.get('first_name', 'N/A')} {profile.get('last_name', 'N/A')}")
                print(f"Poste: {profile.get('position', 'N/A')}")
                print(f"Location: {profile.get('location', 'N/A')}")
                print(f"LinkedIn: {profile.get('linkedinUrl', 'N/A')}")
                
                # Resume (tronqué)
                resume = profile.get('resume', '')
                if resume:
                    resume_preview = resume[:150] + "..." if len(resume) > 150 else resume
                    print(f"Resume: {resume_preview}")
                
                # Expériences
                experiences = profile.get('experience', [])
                print(f"Nombre d'expériences: {len(experiences)}")
                if experiences:
                    exp = experiences[0]
                    print(f"   • Dernière expérience: {exp.get('position', 'N/A')} @ {exp.get('company', 'N/A')}")
                
                # Skills
                skills = profile.get('skills', [])
                print(f"Skills (champ skills[]): {len(skills)} compétences")
                if skills:
                    print(f"   • Exemples: {', '.join(skills[:5])}")
            
            print()
            
            # ============================================
            # 5. ANALYSE POUR LE PROJET
            # ============================================
            
            print("=" * 70)
            print("🎯 ANALYSE POUR LE PROJET GRAPH ML")
            print("=" * 70)
            
            print(f"✅ Profils disponibles: {total}")
            
            if total >= 60:
                print(f"✅ Objectif atteint ! (minimum 60 profils)")
            else:
                print(f"⚠️  Seulement {total} profils (objectif: 60+)")
            
            print()
            
            # Recommandations
            print("📋 Prochaines étapes:")
            print("   1. Phase 2 : Extraire les compétences depuis 'resume' et 'experience'")
            print("   2. Phase 3 : Construire le graphe NetworkX")
            print("   3. Phase 4 : Générer les embeddings (node2vec)")
            print("   4. Phase 5 : Entraîner le modèle de link prediction")
            print()
            
            # Sauvegarder un exemple de profil
            if profiles:
                example_profile_path = settings.data_dir / "example_profile.json"
                with open(example_profile_path, 'w', encoding='utf-8') as f:
                    # Convertir ObjectId en string
                    example = profiles[0].copy()
                    example['_id'] = str(example['_id'])
                    json.dump(example, f, ensure_ascii=False, indent=2)
                print(f"💾 Exemple de profil sauvegardé: {example_profile_path}")
            
            print()
            print("=" * 70)
            print("✅ TEST TERMINÉ AVEC SUCCÈS !")
            print("=" * 70)
    
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERREUR LORS DU TEST")
        print("=" * 70)
        print(f"Erreur: {e}")
        print()
        print("💡 Vérifiez que:")
        print("   • MongoDB est en cours d'exécution (dans WSL)")
        print("   • Le fichier .env est configuré correctement")
        print("   • La base de données contient des profils")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()