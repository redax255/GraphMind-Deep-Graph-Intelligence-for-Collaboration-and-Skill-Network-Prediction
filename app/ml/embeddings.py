"""
Node2Vec Embeddings pour GraphMind.

Transforme les nœuds du graphe Neo4j en vecteurs numériques (embeddings)
pour l'analyse de similarité et le machine learning.
"""

import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import networkx as nx
from node2vec import Node2Vec
from neo4j import GraphDatabase

from app.config import settings


class Node2VecEmbeddings:
    """
    Génère et gère les embeddings Node2Vec depuis Neo4j.
    
    Architecture :
    1. Extraire graphe depuis Neo4j
    2. Entraîner Node2Vec (random walks + Word2Vec)
    3. Sauvegarder embeddings
    4. Requêtes de similarité
    """
    
    def __init__(
        self,
        uri: str = settings.neo4j_uri,
        user: str = settings.neo4j_user,
        password: str = settings.neo4j_password,
        dimensions: int = 128,
        walk_length: int = 80,
        num_walks: int = 10,
        workers: int = 4
    ):
        """
        Initialise Node2Vec.
        
        Args:
            uri: URI Neo4j
            user: Utilisateur Neo4j
            password: Mot de passe Neo4j
            dimensions: Dimension des embeddings (64, 128, 256)
            walk_length: Longueur de chaque random walk
            num_walks: Nombre de walks par nœud
            workers: Nombre de threads
        """
        self.uri = uri
        self.user = user
        self.password = password
        
        # Hyperparamètres Node2Vec
        self.dimensions = dimensions
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.workers = workers
        
        # Modèle et embeddings
        self.model = None
        self.embeddings = {}
        self.graph = None
        
        print(f"✅ Node2Vec initialisé (dim={dimensions}, walks={num_walks})")
    
    def load_graph_from_neo4j(
        self,
        relation_types: List[str] = None
    ) -> nx.Graph:
        """
        Charge le graphe depuis Neo4j vers NetworkX.
        
        Args:
            relation_types: Types de relations à inclure
                        (None = toutes)
        
        Returns:
            Graphe NetworkX
        """
        print("🔄 Chargement graphe depuis Neo4j...")
        
        driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        G = nx.Graph()
        
        with driver.session() as session:
            # Récupérer tous les nœuds Person
            result = session.run("""
                MATCH (p:Person)
                RETURN p.name as name, 
                    COALESCE(p.linkedin_id, p.name) as id,
                    labels(p) as labels
            """)
            
            nodes_count = 0
            for record in result:
                node_id = record["id"]
                if node_id:
                    G.add_node(node_id, 
                            name=record["name"],
                            labels=record["labels"])
                    nodes_count += 1
            
            print(f"   ✅ {nodes_count} nœuds chargés")
            
            # Récupérer les relations Person→Person
            # KNOWS, SIMILAR_TO, STUDIED_TOGETHER
            query = """
                MATCH (p1:Person)-[r]->(p2:Person)
                RETURN COALESCE(p1.linkedin_id, p1.name) as source,
                    COALESCE(p2.linkedin_id, p2.name) as target,
                    type(r) as rel_type
            """
            
            result = session.run(query)
            
            edges_count = 0
            for record in result:
                source = record["source"]
                target = record["target"]
                rel_type = record["rel_type"]
                
                if source and target and source in G.nodes and target in G.nodes:
                    G.add_edge(source, target, relation=rel_type)
                    edges_count += 1
            
            print(f"   ✅ {edges_count} relations chargées")
        
        driver.close()
        
        self.graph = G
        
        print(f"✅ Graphe chargé : {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes")
        
        return G

    def train(self, p: float = 1.0, q: float = 1.0) -> None:
        """
        Entraîne Node2Vec sur le graphe.
        
        Args:
            p: Return parameter (contrôle retour au nœud précédent)
            q: In-out parameter (contrôle exploration vs exploitation)
               - q > 1 : BFS (exploration locale)
               - q < 1 : DFS (exploration globale)
        """
        if self.graph is None:
            raise ValueError("⚠️ Chargez d'abord le graphe avec load_graph_from_neo4j()")
        
        print("🔄 Entraînement Node2Vec...")
        print(f"   Paramètres : dim={self.dimensions}, p={p}, q={q}")
        print(f"   Walks : length={self.walk_length}, num={self.num_walks}")
        
        # Initialiser Node2Vec
        node2vec = Node2Vec(
            self.graph,
            dimensions=self.dimensions,
            walk_length=self.walk_length,
            num_walks=self.num_walks,
            workers=self.workers,
            p=p,
            q=q,
            quiet=False
        )
        
        # Entraîner le modèle Word2Vec
        print("   🔄 Génération des random walks...")
        self.model = node2vec.fit(
            window=10,        # Taille de la fenêtre Word2Vec
            min_count=1,      # Fréquence minimale
            batch_words=4     # Batch size
        )
        
        print("✅ Entraînement terminé")
        
        # Extraire les embeddings
        self._extract_embeddings()
    
    def _extract_embeddings(self) -> None:
        """Extrait les embeddings du modèle Word2Vec."""
        print("🔄 Extraction des embeddings...")
        
        self.embeddings = {}
        
        for node in self.graph.nodes():
            try:
                # Convertir node en string si nécessaire
                node_str = str(node)
                embedding = self.model.wv[node_str]
                self.embeddings[node] = embedding
            except KeyError:
                print(f"⚠️ Embedding manquant pour nœud : {node}")
        
        print(f"✅ {len(self.embeddings)} embeddings extraits")
    
    def save(self, filepath: str = "data/models/node2vec_embeddings.pkl") -> None:
        """
        Sauvegarde les embeddings.
        
        Args:
            filepath: Chemin du fichier de sauvegarde
        """
        # Créer dossier si nécessaire
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder
        data = {
            'embeddings': self.embeddings,
            'dimensions': self.dimensions,
            'graph_stats': {
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges()
            }
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"✅ Embeddings sauvegardés : {filepath}")
    
    def load(self, filepath: str = "data/models/node2vec_embeddings.pkl") -> None:
        """
        Charge les embeddings depuis un fichier.
        
        Args:
            filepath: Chemin du fichier
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.embeddings = data['embeddings']
        self.dimensions = data['dimensions']
        
        print(f"✅ {len(self.embeddings)} embeddings chargés")
        print(f"   Dimension : {self.dimensions}D")
    
    def get_embedding(self, node_id: str) -> Optional[np.ndarray]:
        """
        Retourne l'embedding d'un nœud.
        
        Args:
            node_id: ID du nœud
        
        Returns:
            Vecteur embedding ou None
        """
        return self.embeddings.get(node_id)
    
    def get_most_similar(
        self,
        node_id: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Trouve les nœuds les plus similaires.
        
        Args:
            node_id: ID du nœud de référence
            top_k: Nombre de résultats
        
        Returns:
            Liste de (node_id, similarité)
        """
        if node_id not in self.embeddings:
            print(f"⚠️ Nœud {node_id} introuvable")
            return []
        
        # Embedding du nœud de référence
        ref_embedding = self.embeddings[node_id]
        
        # Calculer similarités avec tous les autres nœuds
        similarities = []
        
        for other_id, other_embedding in self.embeddings.items():
            if other_id == node_id:
                continue
            
            # Similarité cosine
            similarity = np.dot(ref_embedding, other_embedding) / (
                np.linalg.norm(ref_embedding) * np.linalg.norm(other_embedding)
            )
            
            similarities.append((other_id, similarity))
        
        # Trier par similarité décroissante
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_statistics(self) -> Dict:
        """
        Retourne des statistiques sur les embeddings.
        
        Returns:
            Dictionnaire de statistiques
        """
        if not self.embeddings:
            return {}
        
        embeddings_matrix = np.array(list(self.embeddings.values()))
        
        stats = {
            'num_nodes': len(self.embeddings),
            'dimensions': self.dimensions,
            'mean_norm': np.mean(np.linalg.norm(embeddings_matrix, axis=1)),
            'std_norm': np.std(np.linalg.norm(embeddings_matrix, axis=1)),
            'min_value': np.min(embeddings_matrix),
            'max_value': np.max(embeddings_matrix)
        }
        
        return stats