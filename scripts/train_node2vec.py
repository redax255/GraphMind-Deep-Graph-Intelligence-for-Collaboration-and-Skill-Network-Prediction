"""
Script d'entraînement Node2Vec.

Charge le graphe Neo4j, entraîne Node2Vec, et sauvegarde les embeddings.
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.append(str(Path(__file__).parent.parent))

from app.ml.embeddings import Node2VecEmbeddings

from app.config import settings

def print_separator(char="=", length=80):
    """Affiche un séparateur."""
    print(char * length)


def main():
    print_separator()
    print("🚀 ENTRAÎNEMENT NODE2VEC - GRAPHMIND")
    print_separator()
    print()
    
    # ============================================
    # CONFIGURATION
    # ============================================
    
    # Connexion Neo4j
    NEO4J_URI = settings.neo4j_uri
    NEO4J_USER = settings.neo4j_user
    NEO4J_PASSWORD = settings.neo4j_password
    
    # Hyperparamètres Node2Vec
    DIMENSIONS = 128              # Dimension des embeddings
    WALK_LENGTH = 80              # Longueur de chaque random walk
    NUM_WALKS = 10                # Nombre de walks par nœud
    P = 1.0                       # Return parameter
    Q = 1.0                       # In-out parameter
    WORKERS = 4                   # Nombre de threads
    
    # Types de relations à inclure (None = toutes)
    RELATION_TYPES = None         # Ex: ["WORKS_AT", "STUDIED_AT", "HAS_SKILL"]
    
    # Fichier de sauvegarde
    OUTPUT_FILE = "data/models/node2vec_embeddings.pkl"
    
    print("📋 CONFIGURATION")
    print_separator("-")
    print(f"Neo4j URI       : {NEO4J_URI}")
    print(f"Dimensions      : {DIMENSIONS}")
    print(f"Walk Length     : {WALK_LENGTH}")
    print(f"Num Walks       : {NUM_WALKS}")
    print(f"Parameters p, q : {P}, {Q}")
    print(f"Workers         : {WORKERS}")
    print(f"Output File     : {OUTPUT_FILE}")
    print()
    
    # ============================================
    # INITIALISATION
    # ============================================
    
    print_separator()
    print("📦 INITIALISATION")
    print_separator()
    print()
    
    embedder = Node2VecEmbeddings(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        dimensions=DIMENSIONS,
        walk_length=WALK_LENGTH,
        num_walks=NUM_WALKS,
        workers=WORKERS
    )
    
    print()
    
    # ============================================
    # CHARGEMENT GRAPHE
    # ============================================
    
    print_separator()
    print("📊 CHARGEMENT GRAPHE NEO4J")
    print_separator()
    print()
    
    try:
        graph = embedder.load_graph_from_neo4j(
            relation_types=RELATION_TYPES
        )
    except Exception as e:
        print()
        print_separator()
        print("❌ ERREUR CHARGEMENT GRAPHE")
        print_separator()
        print(f"Erreur : {e}")
        print()
        print("💡 Vérifiez :")
        print("   1. Neo4j est démarré")
        print("   2. Mot de passe correct")
        print("   3. Graphe existe dans Neo4j")
        return
    
    print()
    
    # Statistiques du graphe
    print("📈 STATISTIQUES GRAPHE")
    print_separator("-")
    print(f"Nœuds           : {graph.number_of_nodes()}")
    print(f"Arêtes          : {graph.number_of_edges()}")
    print(f"Densité         : {(2 * graph.number_of_edges()) / (graph.number_of_nodes() * (graph.number_of_nodes() - 1)):.4f}")
    print()
    
    # ============================================
    # ENTRAÎNEMENT NODE2VEC
    # ============================================
    
    print_separator()
    print("🧠 ENTRAÎNEMENT NODE2VEC")
    print_separator()
    print()
    
    try:
        embedder.train(p=P, q=Q)
    except Exception as e:
        print()
        print_separator()
        print("❌ ERREUR ENTRAÎNEMENT")
        print_separator()
        print(f"Erreur : {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # ============================================
    # STATISTIQUES EMBEDDINGS
    # ============================================
    
    print_separator()
    print("📊 STATISTIQUES EMBEDDINGS")
    print_separator()
    print()
    
    stats = embedder.get_statistics()
    
    print(f"Nombre de nœuds : {stats['num_nodes']}")
    print(f"Dimensions      : {stats['dimensions']}")
    print(f"Norme moyenne   : {stats['mean_norm']:.4f}")
    print(f"Écart-type      : {stats['std_norm']:.4f}")
    print(f"Valeur min      : {stats['min_value']:.4f}")
    print(f"Valeur max      : {stats['max_value']:.4f}")
    print()
    
    # ============================================
    # TEST SIMILARITÉS
    # ============================================
    
    print_separator()
    print("🔍 TEST SIMILARITÉS (3 exemples)")
    print_separator()
    print()
    
    # Prendre 3 nœuds aléatoires pour test
    import random
    sample_nodes = random.sample(list(embedder.embeddings.keys()), min(3, len(embedder.embeddings)))
    
    for i, node_id in enumerate(sample_nodes, 1):
        print(f"Exemple {i} : {node_id}")
        print("-" * 80)
        
        similar = embedder.get_most_similar(node_id, top_k=5)
        
        for rank, (similar_id, similarity) in enumerate(similar, 1):
            print(f"   {rank}. {similar_id:<40} (similarité: {similarity:.4f})")
        
        print()
    
    # ============================================
    # SAUVEGARDE
    # ============================================
    
    print_separator()
    print("💾 SAUVEGARDE EMBEDDINGS")
    print_separator()
    print()
    
    try:
        embedder.save(OUTPUT_FILE)
    except Exception as e:
        print()
        print_separator()
        print("❌ ERREUR SAUVEGARDE")
        print_separator()
        print(f"Erreur : {e}")
        return
    
    print()
    
    # ============================================
    # TEST CHARGEMENT
    # ============================================
    
    print_separator()
    print("✅ TEST CHARGEMENT")
    print_separator()
    print()
    
    # Créer nouvelle instance et charger
    embedder_test = Node2VecEmbeddings()
    embedder_test.load(OUTPUT_FILE)
    
    print()
    
    # ============================================
    # RÉSUMÉ FINAL
    # ============================================
    
    print_separator()
    print("✅ ENTRAÎNEMENT TERMINÉ")
    print_separator()
    print()
    print(f"📊 {stats['num_nodes']} nœuds → vecteurs {stats['dimensions']}D")
    print(f"💾 Fichier sauvegardé : {OUTPUT_FILE}")
    print()
    print("🎯 Prochaines étapes :")
    print("   1. Visualiser embeddings en 2D (t-SNE/UMAP)")
    print("   2. Community detection")
    print("   3. Link prediction")
    print()
    print_separator()


if __name__ == "__main__":
    main()