"""
Script pour vider le cache et re-tester la normalisation.
"""

import shutil
from pathlib import Path

# Supprimer cache
cache_dir = Path("data/cache")
if cache_dir.exists():
    print("🗑️  Suppression du cache...")
    shutil.rmtree(cache_dir)
    print("✅ Cache supprimé")

print("\n🔄 Relancer le test maintenant:")
print("   python test_company_clustering.py")