"""
Test du date parser sur les données MongoDB réelles.
Affiche les résultats de parsing et détecte les erreurs.
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.append(str(Path(__file__).parent))

from app.services.database import MongoDBClient
from app.utils.date_parser import DateParser


def extract_all_periods(profiles):
    """Extrait toutes les périodes des profils."""
    periods = {
        'experience': [],
        'formation': []
    }
    
    for profile in profiles:
        # Expériences
        for exp in profile.get('experience', []):
            period = exp.get('period')
            if period:
                periods['experience'].append({
                    'profile_id': profile.get('_id'),
                    'name': f"{profile.get('first_name')} {profile.get('last_name')}",
                    'position': exp.get('position'),
                    'company': exp.get('company'),
                    'period': period
                })
        
        # Formations
        for edu in profile.get('formation', []):
            period = edu.get('period')
            if period:
                periods['formation'].append({
                    'profile_id': profile.get('_id'),
                    'name': f"{profile.get('first_name')} {profile.get('last_name')}",
                    'university': edu.get('university'),
                    'degree': edu.get('degree'),
                    'period': period
                })
    
    return periods


def main():
    print("="*80)
    print("📅 TEST DATE PARSER - DONNÉES RÉELLES")
    print("="*80)
    print()
    
    # 1. Charger profils
    print("🔄 Chargement des profils...")
    with MongoDBClient() as db:
        profiles = db.get_all_profiles()
    print(f"✅ {len(profiles)} profils chargés")
    print()
    
    # 2. Extraire périodes
    print("🔄 Extraction des périodes...")
    periods = extract_all_periods(profiles)
    
    total_exp = len(periods['experience'])
    total_edu = len(periods['formation'])
    
    print(f"✅ {total_exp} périodes d'expérience")
    print(f"✅ {total_edu} périodes de formation")
    print()
    
    # 3. Parser toutes les périodes
    parser = DateParser()
    
    results = {
        'experience': [],
        'formation': []
    }
    
    print("🔄 Parsing des périodes...")
    
    # Parser expériences
    for item in periods['experience']:
        parsed = parser.parse_period(item['period'])
        results['experience'].append({
            **item,
            'parsed': parsed
        })
    
    # Parser formations
    for item in periods['formation']:
        parsed = parser.parse_education_period(item['period'])
        results['formation'].append({
            **item,
            'parsed': parsed
        })
    
    print("✅ Parsing terminé")
    print()
    
    # 4. Statistiques
    print("="*80)
    print("📊 STATISTIQUES")
    print("="*80)
    print()
    
    # Expériences
    exp_success = sum(1 for r in results['experience'] if not r['parsed']['error'])
    exp_errors = sum(1 for r in results['experience'] if r['parsed']['error'])
    exp_current = sum(1 for r in results['experience'] if r['parsed']['is_current'])
    
    print("📋 EXPÉRIENCES :")
    print(f"   ✅ Parsées avec succès : {exp_success}/{total_exp} ({exp_success/total_exp*100:.1f}%)")
    print(f"   ❌ Erreurs : {exp_errors}/{total_exp} ({exp_errors/total_exp*100:.1f}%)")
    print(f"   🔄 Postes actuels : {exp_current}/{total_exp} ({exp_current/total_exp*100:.1f}%)")
    print()
    
    # Formations
    edu_success = sum(1 for r in results['formation'] if not r['parsed']['error'])
    edu_errors = sum(1 for r in results['formation'] if r['parsed']['error'])
    
    print("📋 FORMATIONS :")
    print(f"   ✅ Parsées avec succès : {edu_success}/{total_edu} ({edu_success/total_edu*100:.1f}%)")
    print(f"   ❌ Erreurs : {edu_errors}/{total_edu} ({edu_errors/total_edu*100:.1f}%)")
    print()
    
    # Distribution durées
    durations = [r['parsed']['duration_months'] for r in results['experience'] 
                 if r['parsed']['duration_months']]
    
    if durations:
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        print("📊 DURÉES (expériences) :")
        print(f"   Moyenne : {avg_duration:.1f} mois ({avg_duration/12:.1f} ans)")
        print(f"   Min : {min_duration} mois")
        print(f"   Max : {max_duration} mois ({max_duration/12:.1f} ans)")
        print()
    
    # 5. Exemples réussis
    print("="*80)
    print("✅ EXEMPLES RÉUSSIS (10 premiers)")
    print("="*80)
    print()
    
    success_examples = [r for r in results['experience'] if not r['parsed']['error']][:10]
    
    for i, ex in enumerate(success_examples, 1):
        print(f"{i}. {ex['position']} @ {ex['company']}")
        print(f"   Input    : {ex['period']}")
        print(f"   Start    : {ex['parsed']['start_date']}")
        print(f"   End      : {ex['parsed']['end_date']}")
        print(f"   Duration : {ex['parsed']['duration_months']} mois")
        print(f"   Current  : {ex['parsed']['is_current']}")
        print()
    
    # 6. Erreurs
    error_examples = [r for r in results['experience'] if r['parsed']['error']]
    
    if error_examples:
        print("="*80)
        print(f"❌ ERREURS ({len(error_examples)} cas)")
        print("="*80)
        print()
        
        # Grouper par type d'erreur
        errors_by_type = defaultdict(list)
        for ex in error_examples:
            error_msg = ex['parsed']['error']
            errors_by_type[error_msg].append(ex)
        
        # Afficher par type
        for error_type, items in sorted(errors_by_type.items(), 
                                       key=lambda x: len(x[1]), 
                                       reverse=True):
            print(f"📋 {error_type} ({len(items)} cas) :")
            for ex in items[:3]:  # Afficher 3 exemples max
                print(f"   - {ex['period']}")
            if len(items) > 3:
                print(f"   ... et {len(items)-3} autres")
            print()
    
    # 7. Formats uniques
    print("="*80)
    print("📋 FORMATS UNIQUES DÉTECTÉS")
    print("="*80)
    print()
    
    # Compter formats
    format_counts = Counter(r['period'] for r in periods['experience'])
    
    print(f"✅ {len(format_counts)} formats uniques d'expérience")
    print()
    
    print("Top 10 formats les plus fréquents :")
    for i, (format_str, count) in enumerate(format_counts.most_common(10), 1):
        parsed = parser.parse_period(format_str)
        status = "✅" if not parsed['error'] else "❌"
        print(f"{i}. {status} {format_str:<50} ({count} fois)")
    
    print()
    
    # 8. Validation cohérence
    print("="*80)
    print("🔍 VALIDATION COHÉRENCE")
    print("="*80)
    print()
    
    # Vérifier dates invalides
    invalid_dates = [
        r for r in results['experience']
        if r['parsed']['start_date'] and r['parsed']['end_date']
        and r['parsed']['start_date'] > r['parsed']['end_date']
    ]
    
    if invalid_dates:
        print(f"⚠️  {len(invalid_dates)} périodes avec date_fin < date_début :")
        for ex in invalid_dates[:5]:
            print(f"   - {ex['period']}")
            print(f"     Start: {ex['parsed']['start_date']}, End: {ex['parsed']['end_date']}")
    else:
        print("✅ Aucune incohérence de dates détectée")
    
    print()
    
    # 9. Résumé final
    print("="*80)
    print("✅ RÉSUMÉ")
    print("="*80)
    print()
    
    total = total_exp + total_edu
    total_success = exp_success + edu_success
    
    print(f"✅ Total périodes parsées : {total}")
    print(f"✅ Succès : {total_success} ({total_success/total*100:.1f}%)")
    print(f"❌ Erreurs : {exp_errors + edu_errors} ({(exp_errors + edu_errors)/total*100:.1f}%)")
    print()
    
    if exp_success / total_exp >= 0.95:
        print("🎉 EXCELLENT : >95% de succès sur les expériences !")
    elif exp_success / total_exp >= 0.90:
        print("✅ BON : >90% de succès sur les expériences")
    else:
        print("⚠️  ATTENTION : <90% de succès, révision nécessaire")


if __name__ == "__main__":
    main()