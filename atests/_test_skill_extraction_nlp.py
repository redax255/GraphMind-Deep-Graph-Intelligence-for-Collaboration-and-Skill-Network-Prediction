"""
Test de l'extraction de compétences avec NLP.

Compare la méthode NLP avec Pattern Matching.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.database import MongoDBClient
from app.utils.skill_extractor import SkillExtractor
from app.utils.skills_database import get_all_skills


def extract_skills_with_context(profile: dict) -> List[Tuple[str, str]]:
    """
    Extrait les compétences avec leur phrase minimale d'extraction.
    
    Args:
        profile: Profil MongoDB
    
    Returns:
        Liste de tuples (compétence, phrase_minimale)
    """
    known_skills = get_all_skills()
    results = []
    
    # Collecter tous les textes
    texts = []
    
    if profile.get('resume'):
        texts.append(('Resume', profile.get('resume')))
    
    if profile.get('position'):
        texts.append(('Position', profile.get('position')))
    
    for exp in profile.get('experience', []):
        if exp.get('position'):
            texts.append((f"Exp: {exp.get('company', 'N/A')}", exp.get('position')))
        
        descriptions = exp.get('description', [])
        if isinstance(descriptions, list):
            for desc in descriptions:
                if desc:
                    texts.append((f"Exp: {exp.get('company', 'N/A')}", desc))
        elif descriptions:
            texts.append((f"Exp: {exp.get('company', 'N/A')}", descriptions))
    
    # Chercher les compétences dans chaque texte
    for source, text in texts:
        if not text:
            continue
        
        text_lower = text.lower()
        
        for skill in known_skills:
            pattern = r'(?<![a-zA-Z])' + re.escape(skill.lower()) + r'(?![a-zA-Z])'
            match = re.search(pattern, text_lower)
            
            if match:
                # Extraire la phrase minimale
                sentence = extract_minimal_sentence(text, match.start(), match.end())
                
                # Ajouter seulement si pas déjà présent
                if not any(r[0] == skill for r in results):
                    results.append((skill, sentence))
    
    return sorted(results, key=lambda x: x[0])


def extract_minimal_sentence(text: str, start: int, end: int) -> str:
    """
    Extrait la phrase minimale contenant le mot trouvé.
    
    Args:
        text: Texte complet
        start: Position de début du mot
        end: Position de fin du mot
    
    Returns:
        Phrase minimale
    """
    # Chercher le début de la phrase (. ! ? ou début du texte)
    sentence_start = start
    for i in range(start - 1, -1, -1):
        if text[i] in '.!?\n':
            sentence_start = i + 1
            break
        if i == 0:
            sentence_start = 0
    
    # Chercher la fin de la phrase (. ! ? ou fin du texte)
    sentence_end = end
    for i in range(end, len(text)):
        if text[i] in '.!?\n':
            sentence_end = i
            break
        if i == len(text) - 1:
            sentence_end = len(text)
    
    # Extraire la phrase
    sentence = text[sentence_start:sentence_end].strip()
    
    # Nettoyer
    sentence = sentence.replace('\n', ' ').replace('\r', ' ')
    sentence = re.sub(r'\s+', ' ', sentence)
    
    # Limiter à 100 caractères si trop long
    if len(sentence) > 100:
        # Trouver la position du mot dans la phrase
        word_pos_in_sentence = start - sentence_start
        
        # Extraire autour du mot (30 caractères avant/après)
        extract_start = max(0, word_pos_in_sentence - 30)
        extract_end = min(len(sentence), word_pos_in_sentence + (end - start) + 30)
        
        sentence = "..." + sentence[extract_start:extract_end].strip() + "..."
    
    return sentence


def print_separator(char="=", length=70):
    """Affiche un séparateur"""
    print(char * length)


def main():
    print_separator()
    print("🧪 TEST - EXTRACTION NLP (spaCy)")
    print_separator()
    print()
    
    # Vérifier que spaCy est installé
    try:
        import spacy
        print("✅ spaCy installé")
    except ImportError:
        print("❌ spaCy NON installé")
        print()
        print("Installation requise:")
        print("  pip install spacy")
        print("  python -m spacy download en_core_web_sm")
        print("  python -m spacy download fr_core_news_sm")
        return
    
    # Vérifier les modèles
    print()
    print("Vérification des modèles spaCy...")
    
    models_ok = True
    try:
        spacy.load("en_core_web_sm")
        print("  ✅ Modèle anglais (en_core_web_sm)")
    except OSError:
        print("  ❌ Modèle anglais manquant")
        print("     → python -m spacy download en_core_web_sm")
        models_ok = False
    
    try:
        spacy.load("fr_core_news_sm")
        print("  ✅ Modèle français (fr_core_news_sm)")
    except OSError:
        print("  ❌ Modèle français manquant")
        print("     → python -m spacy download fr_core_news_sm")
        models_ok = False
    
    if not models_ok:
        print()
        print("⚠️  Installez les modèles manquants avant de continuer")
        return
    
    print()
    print_separator()
    
    try:
        # Connexion MongoDB
        with MongoDBClient() as db:
            print("✅ Connexion MongoDB OK")
            print()
            
            # Récupérer profils
            profiles = db.get_all_profiles()
            print(f"📊 {len(profiles)} profils chargés")
            print()
            
            # Créer les extracteurs
            extractor_pattern = SkillExtractor(method="pattern_matching")
            extractor_nlp = SkillExtractor(method="nlp")
            
            # Test sur 3 profils
            print_separator()
            print("👤 TEST SUR 3 PROFILS - COMPARAISON")
            print_separator()
            
            for i, profile in enumerate(profiles[:3], 1):
                print(f"\n--- Profil #{i} ---")
                name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}"
                print(f"Nom: {name}")
                print(f"Poste: {profile.get('position', 'N/A')}")
                
                # Extraire avec Pattern Matching
                skills_pattern = extractor_pattern.extract_from_profile(profile)
                
                # Extraire avec NLP
                print("\n⏳ Extraction NLP en cours...")
                skills_nlp = extractor_nlp.extract_from_profile(profile)
                
                # Afficher résultats
                print(f"\n📊 Pattern Matching : {len(skills_pattern)} compétences")
                if skills_pattern:
                    preview = ', '.join(skills_pattern[:10])
                    if len(skills_pattern) > 10:
                        preview += f" ... (+{len(skills_pattern)-10})"
                    print(f"   {preview}")
                
                print(f"\n🧠 NLP (spaCy)      : {len(skills_nlp)} compétences")
                if skills_nlp:
                    preview = ', '.join(skills_nlp[:10])
                    if len(skills_nlp) > 10:
                        preview += f" ... (+{len(skills_nlp)-10})"
                    print(f"   {preview}")
                
                # Différence
                only_nlp = set(skills_nlp) - set(skills_pattern)
                only_pattern = set(skills_pattern) - set(skills_nlp)
                
                if only_nlp:
                    print(f"\n✨ Uniquement NLP (+{len(only_nlp)}): {', '.join(list(only_nlp)[:5])}")
                if only_pattern:
                    print(f"🎯 Uniquement Pattern (+{len(only_pattern)}): {', '.join(list(only_pattern)[:5])}")
            
            # VÉRIFICATION DÉTAILLÉE AVEC CONTEXTE (1 profil)
            print()
            print_separator("=", 120)
            print("🔍 VÉRIFICATION DÉTAILLÉE - PHRASE MINIMALE PAR COMPÉTENCE (Profil #1)")
            print_separator("=", 120)
            
            profile_to_check = profiles[0]
            name = f"{profile_to_check.get('first_name', '')} {profile_to_check.get('last_name', '')}"
            print(f"\nProfil: {name}")
            print()
            
            # Extraire avec contexte
            skills_with_context = extract_skills_with_context(profile_to_check)
            
            if skills_with_context:
                print(f"{'#':<4} {'Compétence':<20} | {'Phrase d extraction':<90}")
                print("-" * 120)
                for idx, (skill, sentence) in enumerate(skills_with_context[:], 1):  # Limiter à 25
                    # Tronquer la phrase si trop longue
                    sentence_short = sentence[:87] + "..." if len(sentence) > 90 else sentence
                    print(f"{idx:<4} {skill:<20} | {sentence_short:<90}")
                
                # if len(skills_with_context) > 25:
                #     print(f"\n... et {len(skills_with_context) - 25} autres compétences")
            else:
                print("❌ Aucune compétence extraite avec contexte")
            
            # Statistiques globales
            print()
            print_separator()
            print("📊 STATISTIQUES GLOBALES")
            print_separator()
            
            print("\n⏳ Calcul statistiques Pattern Matching...")
            stats_pattern = extractor_pattern.get_statistics(profiles)
            
            print("⏳ Calcul statistiques NLP (peut prendre 30-60s)...")
            stats_nlp = extractor_nlp.get_statistics(profiles)
            
            # Afficher comparaison
            print()
            print(f"{'Métrique':<30} {'Pattern':<15} {'NLP':<15} {'Δ':<10}")
            print("-" * 70)
            
            total = stats_pattern['total_profiles']
            
            # Couverture
            cov_p = stats_pattern['profiles_with_skills'] / total * 100
            cov_n = stats_nlp['profiles_with_skills'] / total * 100
            print(f"{'Couverture (%)':<30} {cov_p:>6.1f}%{'':<8} {cov_n:>6.1f}%{'':<8} {cov_n-cov_p:>+6.1f}%")
            
            # Moyenne compétences
            avg_p = stats_pattern['avg_skills_per_profile']
            avg_n = stats_nlp['avg_skills_per_profile']
            print(f"{'Moyenne skills/profil':<30} {avg_p:>6.1f}{'':<9} {avg_n:>6.1f}{'':<9} {avg_n-avg_p:>+6.1f}")
            
            # Min/Max
            print(f"{'Min skills':<30} {stats_pattern['min_skills']:>6}{'':<9} {stats_nlp['min_skills']:>6}{'':<9}")
            print(f"{'Max skills':<30} {stats_pattern['max_skills']:>6}{'':<9} {stats_nlp['max_skills']:>6}{'':<9}")
            
            # Compétences uniques
            unique_p = stats_pattern['unique_skills']
            unique_n = stats_nlp['unique_skills']
            print(f"{'Compétences uniques':<30} {unique_p:>6}{'':<9} {unique_n:>6}{'':<9} {unique_n-unique_p:>+6}")
            
            # Top 10 compétences
            print()
            print_separator()
            print("📈 TOP 10 COMPÉTENCES - COMPARAISON")
            print_separator()
            
            print("\n🎯 Pattern Matching:")
            for i, (skill, count) in enumerate(stats_pattern['top_20_skills'][:10], 1):
                print(f"   {i:2d}. {skill:20s} : {count:3d} profils")
            
            print("\n🧠 NLP (spaCy):")
            for i, (skill, count) in enumerate(stats_nlp['top_20_skills'][:10], 1):
                print(f"   {i:2d}. {skill:20s} : {count:3d} profils")
            
            # Conclusion
            print()
            print_separator()
            print("✅ CONCLUSION")
            print_separator()
            
            if cov_n > cov_p:
                print(f"\n✅ NLP trouve {cov_n-cov_p:.1f}% de profils en plus")
            else:
                print(f"\n⚠️  Pattern Matching trouve {cov_p-cov_n:.1f}% de profils en plus")
            
            if avg_n > avg_p:
                print(f"✅ NLP extrait {avg_n-avg_p:.1f} compétences de plus par profil")
            else:
                print(f"⚠️  Pattern Matching extrait {avg_p-avg_n:.1f} compétences de plus par profil")
            
            print()
            print("💡 Recommandation:")
            if cov_n > cov_p + 10 and avg_n > avg_p + 3:
                print("   → NLP est significativement meilleur, envisagez de l'utiliser")
            elif cov_n > cov_p + 5:
                print("   → NLP est légèrement meilleur mais plus lent")
                print("   → Pattern Matching suffit pour ce projet")
            else:
                print("   → Pattern Matching est suffisant et plus rapide")
            
            print()
            print_separator()
            print("✅ TEST TERMINÉ")
            print_separator()
    
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