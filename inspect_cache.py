"""
Script pour inspecter le VRAI contenu du cache .pkl et .json
(sans refaire de clustering)

Ce script ouvre DIRECTEMENT les fichiers cache pour voir ce qui est stocké.
"""

import pickle
import json
from pathlib import Path
from collections import Counter

print("="*80)
print("🔍 INSPECTION DU CACHE RÉEL (.pkl + .json)")
print("="*80)
print()

# Chemins des fichiers cache
CACHE_DIR = Path("data/cache")
EMBEDDINGS_CACHE_FILE = CACHE_DIR / "company_embeddings.pkl"
NORMALIZATION_CACHE_FILE = CACHE_DIR / "company_normalizations.json"

# ============================================
# 1. VÉRIFIER EXISTENCE
# ============================================

print("📂 VÉRIFICATION DES FICHIERS CACHE...")
print()

if not CACHE_DIR.exists():
    print(f"❌ Dossier cache introuvable : {CACHE_DIR}")
    print("   Le cache n'existe pas ou a été supprimé.")
    exit(0)

if not EMBEDDINGS_CACHE_FILE.exists():
    print(f"❌ Fichier embeddings introuvable : {EMBEDDINGS_CACHE_FILE}")
    embeddings_cache = {}
else:
    print(f"✅ Fichier embeddings trouvé : {EMBEDDINGS_CACHE_FILE}")
    print(f"   Taille : {EMBEDDINGS_CACHE_FILE.stat().st_size / 1024:.1f} KB")
    
    # Charger
    try:
        with open(EMBEDDINGS_CACHE_FILE, 'rb') as f:
            embeddings_cache = pickle.load(f)
        print(f"   ✅ {len(embeddings_cache)} embeddings chargés")
    except Exception as e:
        print(f"   ❌ Erreur chargement : {e}")
        embeddings_cache = {}

print()

if not NORMALIZATION_CACHE_FILE.exists():
    print(f"❌ Fichier normalizations introuvable : {NORMALIZATION_CACHE_FILE}")
    normalization_cache = {}
else:
    print(f"✅ Fichier normalizations trouvé : {NORMALIZATION_CACHE_FILE}")
    print(f"   Taille : {NORMALIZATION_CACHE_FILE.stat().st_size / 1024:.1f} KB")
    
    # Charger
    try:
        with open(NORMALIZATION_CACHE_FILE, 'r', encoding='utf-8') as f:
            normalization_cache = json.load(f)
        print(f"   ✅ {len(normalization_cache)} normalizations chargées")
    except Exception as e:
        print(f"   ❌ Erreur chargement : {e}")
        normalization_cache = {}

print()

if not embeddings_cache and not normalization_cache:
    print("⚠️  Aucun cache trouvé. Exécutez d'abord test_company_clustering.py")
    exit(0)

# ============================================
# 2. ANALYSER EMBEDDINGS CACHE (.pkl)
# ============================================

print("="*80)
print("📊 ANALYSE DU CACHE EMBEDDINGS (.pkl)")
print("="*80)
print()

if embeddings_cache:
    # Statistiques
    print(f"✅ Total : {len(embeddings_cache)} embeddings stockés")
    print()
    
    # Détecter noms avec suffixes (PROBLÈME!)
    print("🔍 DÉTECTION DE SUFFIXES DANS LES CLÉS...")
    print()
    
    suffixes_problematiques = [
        " · stage", "· stage", "·stage",
        " · temps plein", "· temps plein", "·temps plein",
        " · temps partiel", "· temps partiel", "·temps partiel",
        " · cdi", "· cdi", "·cdi",
        " · cdd", "· cdd", "·cdd",
        " · freelance", "· freelance", "·freelance",
    ]
    
    noms_avec_suffixes = []
    noms_propres = []
    
    for nom in embeddings_cache.keys():
        nom_lower = nom.lower()
        has_suffix = any(suffix in nom_lower for suffix in suffixes_problematiques)
        
        if has_suffix:
            noms_avec_suffixes.append(nom)
        else:
            noms_propres.append(nom)
    
    if noms_avec_suffixes:
        print(f"❌ {len(noms_avec_suffixes)} noms AVEC SUFFIXES détectés (PROBLÈME!)")
        print()
        print("   Exemples (10 premiers) :")
        for nom in noms_avec_suffixes[:10]:
            print(f"      - '{nom}'")
        
        if len(noms_avec_suffixes) > 10:
            print(f"      ... et {len(noms_avec_suffixes) - 10} autres")
        
        print()
        print("   ⚠️  Ces noms contiennent des suffixes qui devraient être supprimés!")
        print("   ⚠️  Le cache est CORROMPU et doit être vidé.")
    else:
        print(f"✅ {len(noms_propres)} noms SANS SUFFIXES (BON!)")
        print("   Le cache est propre.")
    
    print()
    
    # Afficher échantillon aléatoire
    print("📋 ÉCHANTILLON (20 premiers noms stockés) :")
    print()
    for i, nom in enumerate(list(embeddings_cache.keys())[:20], 1):
        # Taille embedding
        embedding = embeddings_cache[nom]
        embedding_size = len(embedding)
        print(f"   {i:2d}. '{nom}' → embedding [{embedding_size}D]")
    
    if len(embeddings_cache) > 20:
        print(f"   ... et {len(embeddings_cache) - 20} autres")

print()

# ============================================
# 3. ANALYSER NORMALIZATIONS CACHE (.json)
# ============================================

print("="*80)
print("📊 ANALYSE DU CACHE NORMALIZATIONS (.json)")
print("="*80)
print()

if normalization_cache:
    # Statistiques
    print(f"✅ Total : {len(normalization_cache)} normalizations stockées")
    print()
    
    # Compter entreprises uniques (valeurs)
    normalized_values = list(normalization_cache.values())
    unique_companies = set(normalized_values)
    company_counts = Counter(normalized_values)
    
    print(f"✅ {len(unique_companies)} entreprises uniques après normalisation")
    print()
    
    # Top 10 entreprises
    print("📊 TOP 10 ENTREPRISES (après normalisation) :")
    print()
    print(f"{'#':<4} {'Entreprise':<50} {'Variations'}")
    print("-"*80)
    
    for i, (company, count) in enumerate(company_counts.most_common(10), 1):
        print(f"{i:<4} {company:<50} {count}")
    
    print()
    
    # Exemples de mappings
    print("📋 EXEMPLES DE MAPPINGS (10 premiers) :")
    print()
    print(f"{'Nom nettoyé (clé)':<50} → {'Normalisé (valeur)'}")
    print("-"*80)
    
    for i, (cle, valeur) in enumerate(list(normalization_cache.items())[:10], 1):
        print(f"{cle:<50} → {valeur}")
    
    if len(normalization_cache) > 10:
        print(f"... et {len(normalization_cache) - 10} autres")
    
    print()
    
    # Détecter suffixes dans les CLÉS
    print("🔍 DÉTECTION DE SUFFIXES DANS LES CLÉS...")
    print()
    
    cles_avec_suffixes = []
    cles_propres = []
    
    for cle in normalization_cache.keys():
        cle_lower = cle.lower()
        has_suffix = any(suffix in cle_lower for suffix in suffixes_problematiques)
        
        if has_suffix:
            cles_avec_suffixes.append(cle)
        else:
            cles_propres.append(cle)
    
    if cles_avec_suffixes:
        print(f"❌ {len(cles_avec_suffixes)} clés AVEC SUFFIXES détectés (PROBLÈME!)")
        print()
        print("   Exemples (10 premiers) :")
        for cle in cles_avec_suffixes[:10]:
            print(f"      - '{cle}' → '{normalization_cache[cle]}'")
        
        if len(cles_avec_suffixes) > 10:
            print(f"      ... et {len(cles_avec_suffixes) - 10} autres")
        
        print()
        print("   ⚠️  Ces clés contiennent des suffixes!")
        print("   ⚠️  Le cache est CORROMPU et doit être vidé.")
    else:
        print(f"✅ {len(cles_propres)} clés SANS SUFFIXES (BON!)")
        print("   Le cache est propre.")

print()

# ============================================
# 4. DIAGNOSTIC FINAL
# ============================================

print("="*80)
print("🩺 DIAGNOSTIC FINAL")
print("="*80)
print()

# Compteurs
total_problems = 0

if embeddings_cache and noms_avec_suffixes:
    print(f"❌ Embeddings : {len(noms_avec_suffixes)} noms avec suffixes")
    total_problems += len(noms_avec_suffixes)
else:
    print(f"✅ Embeddings : Propre")

if normalization_cache and cles_avec_suffixes:
    print(f"❌ Normalizations : {len(cles_avec_suffixes)} clés avec suffixes")
    total_problems += len(cles_avec_suffixes)
else:
    print(f"✅ Normalizations : Propre")

print()

if total_problems > 0:
    print(f"⚠️  {total_problems} problème(s) détecté(s) dans le cache!")
    print()
    print("🔧 SOLUTION : VIDER LE CACHE")
    print()
    print("   Option 1 - PowerShell :")
    print("   Remove-Item 'data\\cache\\*' -Force -Recurse")
    print()
    print("   Option 2 - Python :")
    print("   python -c \"from app.utils.company_normalizer_ml import CompanyNormalizerML; CompanyNormalizerML().clear_cache()\"")
    print()
    print("   Puis re-tester :")
    print("   python test_fixes_deepseek.py")
else:
    print("✅ Le cache est PROPRE!")
    print("   Aucun suffixe détecté dans les clés.")
    print()
    print("   Si vous avez encore des mega-clusters, le problème vient d'ailleurs.")

print()
print("="*80)
print("✅ INSPECTION TERMINÉE")
print("="*80)
print()