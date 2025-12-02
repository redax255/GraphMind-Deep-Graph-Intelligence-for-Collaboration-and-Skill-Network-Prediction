"""
Script d'entraînement du Link Predictor.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.ml.link_prediction import LinkPredictor

from app.config import settings


def print_separator(char="=", length=80):
    print(char * length)


def main():
    print_separator()
    print("🔗 LINK PREDICTION - GRAPHMIND")
    print_separator()
    print()
    
    # Configuration
    NEO4J_URI = settings.neo4j_uri
    NEO4J_USER = settings.neo4j_user
    NEO4J_PASSWORD = settings.neo4j_password
    
    print("📋 CONFIGURATION")
    print_separator("-")
    print(f"Neo4j URI : {NEO4J_URI}")
    print()
    
    # Initialisation
    print_separator()
    print("📦 INITIALISATION")
    print_separator()
    print()
    
    predictor = LinkPredictor(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD
    )
    
    print()
    
    # Chargement
    print_separator()
    print("📊 CHARGEMENT DES DONNÉES")
    print_separator()
    
    predictor.load_graph_from_neo4j()
    predictor.load_embeddings()
    
    # Dataset
    print_separator()
    print("📝 CRÉATION DU DATASET")
    print_separator()
    
    pairs, labels = predictor.create_dataset()
    
    # Features
    print_separator()
    print("🔧 EXTRACTION DES FEATURES")
    print_separator()
    
    X = predictor.extract_features(pairs)
    
    # Entraînement
    print_separator()
    print("🧠 ENTRAÎNEMENT")
    print_separator()
    
    metrics = predictor.train(X, labels)
    
    # Prédictions
    print_separator()
    print("🔮 PRÉDICTIONS")
    print_separator()
    
    predictions = predictor.predict_new_links(top_k=20)
    
    print("\n📋 TOP 20 NOUVELLES CONNEXIONS PROBABLES :")
    print_separator("-")
    
    for i, (node1, node2, proba) in enumerate(predictions, 1):
        print(f"{i:2d}. {node1[:30]:<30} ↔ {node2[:30]:<30} ({proba:.2%})")
    
    # Sauvegarde
    print()
    print_separator()
    print("💾 SAUVEGARDE")
    print_separator()
    
    predictor.save_model()
    
    # Résumé
    print()
    print_separator()
    print("✅ LINK PREDICTION TERMINÉE")
    print_separator()
    print()
    print(f"🎯 AUC-ROC : {metrics['auc']:.4f}")
    print(f"📊 Accuracy : {metrics['accuracy']:.4f}")
    print(f"💾 Modèle : data/models/link_predictor.pkl")
    print()
    print_separator()


if __name__ == "__main__":
    main()