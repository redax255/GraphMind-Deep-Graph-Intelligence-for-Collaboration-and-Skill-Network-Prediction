"""
Pipeline complète GraphMind.

Exécute toutes les phases du projet dans l'ordre :
1. Preprocessing (optionnel si déjà fait)
2. Construction graphe (optionnel si déjà fait)
3. Inférence relations (optionnel si déjà fait)
4. Node2Vec embeddings
5. Community detection
6. Link prediction
7. Visualisations

Usage:
    python scripts/pipeline_complete.py
    python scripts/pipeline_complete.py --skip-preprocessing
    python scripts/pipeline_complete.py --only-ml
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from app.ml.embeddings import Node2VecEmbeddings
from app.ml.community_detection import CommunityDetector
from app.ml.link_prediction import LinkPredictor


from app.config import settings

def print_separator(char="=", length=80):
    """Affiche un séparateur."""
    print(char * length)


def print_header(title: str):
    """Affiche un header."""
    print()
    print_separator()
    print(f"🚀 {title}")
    print_separator()
    print()


def print_step(step: str, description: str):
    """Affiche une étape."""
    print(f"\n{'='*80}")
    print(f"📍 ÉTAPE {step}")
    print(f"{'='*80}")
    print(f"{description}")
    print()


class GraphMindPipeline:
    """Pipeline complète GraphMind."""
    
    def __init__(
        self,
        neo4j_uri: str = settings.neo4j_uri,
        neo4j_user: str = settings.neo4j_user,
        neo4j_password: str = settings.neo4j_password,
        skip_preprocessing: bool = False,
        only_ml: bool = False
    ):
        """
        Initialise le pipeline.
        
        Args:
            neo4j_uri: URI Neo4j
            neo4j_user: Utilisateur Neo4j
            neo4j_password: Mot de passe Neo4j
            skip_preprocessing: Skip preprocessing/graph construction
            only_ml: Exécuter seulement la partie ML (4.1-4.4)
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.skip_preprocessing = skip_preprocessing
        self.only_ml = only_ml
        
        self.start_time = None
        self.stats = {}
        
        print("✅ Pipeline initialisé")
    
    def run(self):
        """Exécute le pipeline complet."""
        self.start_time = time.time()
        
        print_header("PIPELINE GRAPHMIND - EXÉCUTION COMPLÈTE")
        
        print(f"⏰ Démarrage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⚙️  Configuration :")
        print(f"   Neo4j URI : {self.neo4j_uri}")
        print(f"   Skip preprocessing : {self.skip_preprocessing}")
        print(f"   Only ML : {self.only_ml}")
        
        try:
            # Phases 1-3 (optionnelles)
            if not self.skip_preprocessing and not self.only_ml:
                self._run_preprocessing()
            
            # Phase 4 : Machine Learning
            self._run_ml_pipeline()
            
            # Résumé final
            self._print_summary()
            
            print()
            print_separator()
            print("✅ PIPELINE TERMINÉ AVEC SUCCÈS")
            print_separator()
            
        except Exception as e:
            print()
            print_separator()
            print(f"❌ ERREUR DANS LE PIPELINE : {e}")
            print_separator()
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _run_preprocessing(self):
        """Exécute preprocessing + construction graphe (Phases 1-3)."""
        print_step("1-3", "Preprocessing & Construction Graphe")
        
        print("⚠️  NOTE : Cette étape nécessite que vous ayez déjà :")
        print("   • MongoDB avec collection 'linkedin_profiles'")
        print("   • Scripts de preprocessing créés")
        print()
        print("⏭️  Si déjà fait, utilisez : --skip-preprocessing")
        print()
        
        response = input("Voulez-vous exécuter le preprocessing maintenant ? (y/n) : ")
        
        if response.lower() == 'y':
            print("\n🔄 Exécution preprocessing...")
            print("   → Cette étape prend 2-3 minutes")
            print()
            print("⚠️  TODO : Implémenter l'appel aux scripts de preprocessing")
            print("   (Pour l'instant, exécutez manuellement si besoin)")
        else:
            print("⏭️  Preprocessing ignoré, passage à la phase ML")
    
    def _run_ml_pipeline(self):
        """Exécute la pipeline ML complète (Phase 4)."""
        print_header("PHASE 4 : MACHINE LEARNING")
        
        # 4.1 : Node2Vec
        self._run_node2vec()
        
        # 4.2 : Community Detection
        self._run_community_detection()
        
        # 4.3 : Link Prediction
        self._run_link_prediction()
        
        # 4.4 : Visualisations
        self._run_visualizations()
    
    def _run_node2vec(self):
        """Exécute Node2Vec embeddings."""
        print_step("4.1", "Node2Vec Embeddings")
        
        start = time.time()
        
        try:
            # Initialisation
            embedder = Node2VecEmbeddings(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password,
                dimensions=128,
                walk_length=80,
                num_walks=10,
                workers=4
            )
            
            # Chargement graphe
            print("📊 Chargement graphe depuis Neo4j...")
            graph = embedder.load_graph_from_neo4j()
            
            # Entraînement
            print("\n🧠 Entraînement Node2Vec...")
            embedder.train(p=1.0, q=1.0)
            
            # Statistiques
            print("\n📊 Statistiques embeddings...")
            stats = embedder.get_statistics()
            
            print(f"   Nœuds : {len(embedder.embeddings)}")
            print(f"   Dimensions : {embedder.dimensions}")
            print(f"   Norme moyenne : {stats['mean_norm']:.4f}")
            
            # Test similarités
            print("\n🔍 Test similarités...")
            import random
            random.seed(42)
            sample_nodes = random.sample(list(embedder.embeddings.keys()), min(3, len(embedder.embeddings)))
            
            for node in sample_nodes:
                similar = embedder.get_most_similar(node, top_k=3)
                print(f"\n   Profil : {node[:30]}")
                for sim_node, score in similar[:3]:
                    print(f"      → {sim_node[:30]:<30} ({score:.2%})")
            
            # Sauvegarde
            print("\n💾 Sauvegarde embeddings...")
            embedder.save("data/models/node2vec_embeddings.pkl")
            
            duration = time.time() - start
            self.stats['node2vec'] = {
                'duration': duration,
                'nodes': len(embedder.embeddings),
                'dimensions': embedder.dimensions
            }
            
            print(f"\n✅ Node2Vec terminé en {duration:.1f}s")
            
        except Exception as e:
            print(f"\n❌ Erreur Node2Vec : {e}")
            raise
    
    def _run_community_detection(self):
        """Exécute détection de communautés."""
        print_step("4.2", "Community Detection")
        
        start = time.time()
        
        try:
            # Initialisation
            detector = CommunityDetector(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password
            )
            
            # Chargement graphe
            print("📊 Chargement graphe...")
            graph = detector.load_graph_from_neo4j()
            
            # Détection
            print("\n🔍 Détection communautés (Louvain)...")
            communities = detector.detect_communities(algorithm="louvain")
            
            # Analyse
            print("\n📊 Analyse communautés...")
            community_data = detector.analyze_communities()
            
            # Affichage résumé
            print(f"\n📋 Résumé :")
            print(f"   Communautés détectées : {len(community_data)}")
            print(f"   Modularité : {detector._calculate_modularity():.4f}")
            
            # Top 3 communautés
            sorted_comms = sorted(
                community_data.items(),
                key=lambda x: x[1]['size'],
                reverse=True
            )
            
            print(f"\n   Top 3 communautés :")
            for i, (comm_id, data) in enumerate(sorted_comms[:3], 1):
                top_skill = data['top_skills'][0][0] if data['top_skills'] else "N/A"
                print(f"      {i}. Comm. {comm_id} : {data['size']} profils - {top_skill}")
            
            # Sauvegarde
            print("\n💾 Sauvegarde résultats...")
            detector.save_results("data/reports/communities.json")
            
            duration = time.time() - start
            self.stats['community_detection'] = {
                'duration': duration,
                'n_communities': len(community_data),
                'modularity': detector._calculate_modularity()
            }
            
            print(f"\n✅ Community Detection terminé en {duration:.1f}s")
            
        except Exception as e:
            print(f"\n❌ Erreur Community Detection : {e}")
            raise
    
    def _run_link_prediction(self):
        """Exécute link prediction."""
        print_step("4.3", "Link Prediction")
        
        start = time.time()
        
        try:
            # Initialisation
            predictor = LinkPredictor(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password
            )
            
            # Chargement
            print("📊 Chargement graphe...")
            graph = predictor.load_graph_from_neo4j()
            
            print("📂 Chargement embeddings...")
            embeddings = predictor.load_embeddings()
            
            # Dataset
            print("\n📝 Création dataset...")
            pairs, labels = predictor.create_dataset()
            
            # Features
            print("\n🔧 Extraction features...")
            X = predictor.extract_features(pairs)
            
            # Entraînement
            print("\n🧠 Entraînement modèle...")
            metrics = predictor.train(X, labels)
            
            # Prédictions
            print("\n🔮 Prédictions top connexions...")
            predictions = predictor.predict_new_links(top_k=10)
            
            print(f"\n   Top 10 prédictions :")
            for i, (node1, node2, proba) in enumerate(predictions, 1):
                print(f"      {i:2d}. {node1[:25]:<25} ↔ {node2[:25]:<25} ({proba:.1%})")
            
            # Sauvegarde
            print("\n💾 Sauvegarde modèle...")
            predictor.save_model()
            
            duration = time.time() - start
            self.stats['link_prediction'] = {
                'duration': duration,
                'auc': metrics['auc'],
                'accuracy': metrics['accuracy']
            }
            
            print(f"\n✅ Link Prediction terminé en {duration:.1f}s")
            print(f"   AUC-ROC : {metrics['auc']:.4f}")
            
        except Exception as e:
            print(f"\n❌ Erreur Link Prediction : {e}")
            raise
    
    def _run_visualizations(self):
        """Exécute visualisations."""
        print_step("4.4", "Visualisations")
        
        print("📊 Génération des visualisations...")
        print()
        print("⚠️  NOTE : Exécutez manuellement pour voir les graphiques :")
        print("   python scripts/visualize_embeddings.py")
        print("   python scripts/visualize_communities.py")
        print()
        print("✅ Visualisations : OK (à exécuter manuellement)")
    
    def _print_summary(self):
        """Affiche résumé final."""
        print()
        print_separator()
        print("📊 RÉSUMÉ DE L'EXÉCUTION")
        print_separator()
        print()
        
        total_duration = time.time() - self.start_time
        
        print(f"⏱️  Durée totale : {total_duration:.1f}s ({total_duration/60:.1f} min)")
        print()
        
        if 'node2vec' in self.stats:
            print(f"📍 Node2Vec :")
            print(f"   • Durée : {self.stats['node2vec']['duration']:.1f}s")
            print(f"   • Nœuds : {self.stats['node2vec']['nodes']}")
            print(f"   • Dimensions : {self.stats['node2vec']['dimensions']}")
            print()
        
        if 'community_detection' in self.stats:
            print(f"📍 Community Detection :")
            print(f"   • Durée : {self.stats['community_detection']['duration']:.1f}s")
            print(f"   • Communautés : {self.stats['community_detection']['n_communities']}")
            print(f"   • Modularité : {self.stats['community_detection']['modularity']:.4f}")
            print()
        
        if 'link_prediction' in self.stats:
            print(f"📍 Link Prediction :")
            print(f"   • Durée : {self.stats['link_prediction']['duration']:.1f}s")
            print(f"   • AUC-ROC : {self.stats['link_prediction']['auc']:.4f}")
            print(f"   • Accuracy : {self.stats['link_prediction']['accuracy']:.4f}")
            print()
        
        print(f"📁 Fichiers générés :")
        print(f"   • data/models/node2vec_embeddings.pkl")
        print(f"   • data/models/link_predictor.pkl")
        print(f"   • data/reports/communities.json")
        print()


def main():
    """Point d'entrée."""
    parser = argparse.ArgumentParser(description="Pipeline complète GraphMind")
    
    parser.add_argument(
        '--neo4j-uri',
        default='bolt://localhost:7687',
        help='URI Neo4j'
    )
    parser.add_argument(
        '--neo4j-user',
        default='neo4j',
        help='Utilisateur Neo4j'
    )
    parser.add_argument(
        '--neo4j-password',
        default='your_password',
        help='Mot de passe Neo4j'
    )
    parser.add_argument(
        '--skip-preprocessing',
        action='store_true',
        help='Skip preprocessing et construction graphe'
    )
    parser.add_argument(
        '--only-ml',
        action='store_true',
        help='Exécuter seulement la partie ML (Phase 4)'
    )
    
    args = parser.parse_args()
    
    # Créer et exécuter pipeline
    pipeline = GraphMindPipeline(
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        skip_preprocessing=args.skip_preprocessing,
        only_ml=args.only_ml
    )
    
    pipeline.run()


if __name__ == "__main__":
    main()