"""
Analyse approfondie des profils sans compétences extraites.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.database import MongoDBClient
from app.utils.text_processing import extract_skills_from_profile


def main():
    print("=" * 70)
    print("🔍 ANALYSE - PROFILS SANS COMPÉTENCES")
    print("=" * 70)
    print()
    
    with MongoDBClient() as db:
        profiles = db.get_all_profiles()
        
        # Séparer profils avec/sans compétences
        profiles_with_skills = []
        profiles_without_skills = []
        
        for profile in profiles:
            skills = extract_skills_from_profile(profile)
            if skills:
                profiles_with_skills.append((profile, skills))
            else:
                profiles_without_skills.append(profile)
        
        print(f"✅ Profils AVEC compétences: {len(profiles_with_skills)}")
        print(f"❌ Profils SANS compétences: {len(profiles_without_skills)}")
        print()
        
        # Analyser les profils SANS compétences
        print("=" * 70)
        print("❌ ANALYSE DES PROFILS SANS COMPÉTENCES (5 premiers)")
        print("=" * 70)
        
        for i, profile in enumerate(profiles_without_skills[:5], 1):
            print(f"\n--- Profil #{i} ---")
            name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}"
            print(f"Nom: {name}")
            print(f"Poste: {profile.get('position', 'N/A')}")
            print(f"Location: {profile.get('location', 'N/A')}")
            
            # Analyser les champs
            resume = profile.get('resume', '')
            experiences = profile.get('experience', [])
            
            print(f"\nContenu:")
            print(f"  • Resume: {len(resume) if resume else 0} caractères")
            if resume:
                print(f"    Preview: {resume[:200]}...")
            
            print(f"  • Expériences: {len(experiences)}")
            for j, exp in enumerate(experiences[:2], 1):
                print(f"    {j}. {exp.get('position', 'N/A')} @ {exp.get('company', 'N/A')}")
                desc = exp.get('description', [])
                if isinstance(desc, list) and desc:
                    print(f"       Description: {desc[0][:100] if desc[0] else 'Vide'}...")
                elif isinstance(desc, str) and desc:
                    print(f"       Description: {desc[:100]}...")
                else:
                    print(f"       Description: Vide")
        
        # Statistiques des champs vides
        print()
        print("=" * 70)
        print("📊 STATISTIQUES PROFILS SANS COMPÉTENCES")
        print("=" * 70)
        
        empty_resume = sum(1 for p in profiles_without_skills if not p.get('resume'))
        empty_exp = sum(1 for p in profiles_without_skills if not p.get('experience'))
        empty_both = sum(1 for p in profiles_without_skills 
                        if not p.get('resume') and not p.get('experience'))
        
        total_without = len(profiles_without_skills)
        
        print(f"\n❌ {empty_resume}/{total_without} ({empty_resume/total_without*100:.1f}%) sans resume")
        print(f"❌ {empty_exp}/{total_without} ({empty_exp/total_without*100:.1f}%) sans experience")
        print(f"❌ {empty_both}/{total_without} ({empty_both/total_without*100:.1f}%) sans resume NI experience")
        
        print()
        print("=" * 70)


if __name__ == "__main__":
    main()