"""
Script de détection de communautés.

Détecte les communautés avec Louvain et analyse leurs caractéristiques.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.ml.community_detection import CommunityDetector

from app.config import settings

def print_separator(char="=", length=80):
    """Affiche un séparateur"""
    print(char * length)


def main():
    print_separator()
    print("🏘️  DÉTECTION DE COMMUNAUTÉS - GRAPHMIND")
    print_separator()
    print()
    
    # ============================================
    # CONFIGURATION
    # ============================================
    
    NEO4J_URI = settings.neo4j_uri
    NEO4J_USER = settings.neo4j_user
    NEO4J_PASSWORD = settings.neo4j_password
    
    ALGORITHM = "louvain"  # ou "label_propagation" ou "greedy_modularity"
    
    print("📋 CONFIGURATION")
    print_separator("-")
    print(f"Neo4j URI  : {NEO4J_URI}")
    print(f"Algorithme : {ALGORITHM}")
    print()
    
    # ============================================
    # INITIALISATION
    # ============================================
    
    print_separator()
    print("📦 INITIALISATION")
    print_separator()
    print()
    
    detector = CommunityDetector(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD
    )
    
    print()
    
    # ============================================
    # CHARGEMENT GRAPHE
    # ============================================
    
    print_separator()
    print("📊 CHARGEMENT GRAPHE")
    print_separator()
    print()
    
    try:
        graph = detector.load_graph_from_neo4j()
    except Exception as e:
        print(f"\n❌ Erreur chargement graphe : {e}")
        return
    
    # ============================================
    # DÉTECTION COMMUNAUTÉS
    # ============================================
    
    print_separator()
    print("🔍 DÉTECTION DES COMMUNAUTÉS")
    print_separator()
    
    try:
        communities = detector.detect_communities(algorithm=ALGORITHM)
    except Exception as e:
        print(f"\n❌ Erreur détection : {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ============================================
    # ANALYSE
    # ============================================
    
    print_separator()
    print("📊 ANALYSE DES COMMUNAUTÉS")
    print_separator()
    
    community_data = detector.analyze_communities()
    
    # ============================================
    # AFFICHAGE RÉSULTATS
    # ============================================
    
    detector.print_community_summary()
    
    # ============================================
    # SAUVEGARDE
    # ============================================
    
    print()
    print_separator()
    print("💾 SAUVEGARDE")
    print_separator()
    
    detector.save_results("data/reports/communities.json")
    
    # ============================================
    # RÉSUMÉ FINAL
    # ============================================
    
    print()
    print_separator()
    print("✅ DÉTECTION TERMINÉE")
    print_separator()
    print()
    print(f"📊 {len(community_data)} communautés détectées")
    print(f"💾 Résultats : data/reports/communities.json")
    print()
    print("🎯 Prochaine étape : Link Prediction")
    print("   → python scripts/train_link_predictor.py")
    print()
    print_separator()


if __name__ == "__main__":
    main()