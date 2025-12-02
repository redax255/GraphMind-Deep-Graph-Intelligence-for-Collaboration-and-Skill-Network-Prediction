"""
Link Prediction pour GraphMind.

Prédit les collaborations futures entre profils.
"""

import pickle
import random
from typing import List, Tuple, Dict
from pathlib import Path

import numpy as np
import networkx as nx
from neo4j import GraphDatabase
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

from app.config import settings

class LinkPredictor:
    """
    Prédit les liens futurs dans le graphe.
    
    Pipeline :
    1. Charger graphe + embeddings
    2. Créer dataset (positifs + négatifs)
    3. Extraire features
    4. Entraîner Random Forest
    5. Prédire nouvelles connexions
    """
    
    def __init__(
        self,
        uri: str = settings.neo4j_uri,
        user: str = settings.neo4j_user,
        password: str = settings.neo4j_password
    ):
        """Initialise le prédicteur."""
        self.uri = uri
        self.user = user
        self.password = password
        
        self.graph = None
        self.embeddings = None
        self.model = None
        
        print("✅ LinkPredictor initialisé")
    
    def load_graph_from_neo4j(self) -> nx.Graph:
        """Charge le graphe depuis Neo4j."""
        print("🔄 Chargement graphe depuis Neo4j...")
        
        driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        G = nx.Graph()
        
        with driver.session() as session:
            # Nœuds
            result = session.run("""
                MATCH (p:Person)
                OPTIONAL MATCH (p)-[:HAS_SKILL]->(s:Skill)
                OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company)
                OPTIONAL MATCH (p)-[:STUDIED_AT]->(sc:School)
                RETURN COALESCE(p.linkedin_id, p.name) as id,
                       p.name as name,
                       collect(DISTINCT s.name) as skills,
                       collect(DISTINCT c.name) as companies,
                       collect(DISTINCT sc.name) as schools
            """)
            
            for record in result:
                node_id = record["id"]
                G.add_node(
                    node_id,
                    name=record["name"],
                    skills=record["skills"],
                    companies=record["companies"],
                    schools=record["schools"]
                )
            
            # Relations
            result = session.run("""
                MATCH (p1:Person)-[r]->(p2:Person)
                RETURN COALESCE(p1.linkedin_id, p1.name) as source,
                       COALESCE(p2.linkedin_id, p2.name) as target
            """)
            
            for record in result:
                source = record["source"]
                target = record["target"]
                if source in G.nodes and target in G.nodes:
                    G.add_edge(source, target)
        
        driver.close()
        
        self.graph = G
        print(f"✅ Graphe chargé : {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes")
        
        return G
    
    def load_embeddings(self, filepath: str = "data/models/node2vec_embeddings.pkl"):
        """Charge les embeddings Node2Vec."""
        print(f"📂 Chargement embeddings depuis : {filepath}")
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.embeddings = data['embeddings']
        print(f"✅ {len(self.embeddings)} embeddings chargés")
        
        return self.embeddings
    
    def create_dataset(
        self,
        n_negative_samples: int = None
    ) -> Tuple[List[Tuple], List[int]]:
        """
        Crée le dataset d'entraînement.
        
        Args:
            n_negative_samples: Nombre d'exemples négatifs (None = autant que positifs)
        
        Returns:
            pairs: Liste de tuples (node1, node2)
            labels: Liste de labels (1 = connexion, 0 = pas de connexion)
        """
        print("\n🔄 Création du dataset...")
        
        nodes = list(self.graph.nodes())
        edges = list(self.graph.edges())
        
        # Exemples POSITIFS (connexions existantes)
        positive_pairs = edges
        positive_labels = [1] * len(positive_pairs)
        
        print(f"   ✅ {len(positive_pairs)} exemples positifs")
        
        # Exemples NÉGATIFS (pas de connexion)
        if n_negative_samples is None:
            n_negative_samples = len(positive_pairs)
        
        negative_pairs = []
        
        # Créer set pour vérification rapide
        edge_set = set(edges)
        edge_set.update((b, a) for a, b in edges)  # Ajouter inverses
        
        while len(negative_pairs) < n_negative_samples:
            # Échantillonner 2 nœuds aléatoires
            node1, node2 = random.sample(nodes, 2)
            
            # Vérifier qu'ils ne sont pas connectés
            if (node1, node2) not in edge_set and (node2, node1) not in edge_set:
                negative_pairs.append((node1, node2))
        
        negative_labels = [0] * len(negative_pairs)
        
        print(f"   ✅ {len(negative_pairs)} exemples négatifs")
        
        # Combiner
        all_pairs = positive_pairs + negative_pairs
        all_labels = positive_labels + negative_labels
        
        # Mélanger
        combined = list(zip(all_pairs, all_labels))
        random.shuffle(combined)
        all_pairs, all_labels = zip(*combined)
        
        print(f"✅ Dataset créé : {len(all_pairs)} exemples")
        
        return list(all_pairs), list(all_labels)
    
    def extract_features(self, pairs: List[Tuple]) -> np.ndarray:
        """
        Extrait les features pour chaque paire.
        
        Features :
        1. Amis communs (Jaccard)
        2. Adamic-Adar index
        3. Preferential attachment
        4. Cosine similarity (embeddings)
        5. Même école (0/1)
        6. Même entreprise (0/1)
        7. Compétences communes (count)
        
        Args:
            pairs: Liste de tuples (node1, node2)
        
        Returns:
            Feature matrix (n_pairs, n_features)
        """
        print("\n🔄 Extraction des features...")
        
        features = []
        
        for i, (node1, node2) in enumerate(pairs):
            if i % 1000 == 0:
                print(f"   Progression : {i}/{len(pairs)}")
            
            feat = []
            
            # 1. Amis communs (Jaccard)
            neighbors1 = set(self.graph.neighbors(node1))
            neighbors2 = set(self.graph.neighbors(node2))
            
            if len(neighbors1) > 0 or len(neighbors2) > 0:
                jaccard = len(neighbors1 & neighbors2) / len(neighbors1 | neighbors2)
            else:
                jaccard = 0
            
            feat.append(jaccard)
            
            # 2. Adamic-Adar
            common_neighbors = neighbors1 & neighbors2
            adamic_adar = sum(1 / np.log(self.graph.degree(n)) for n in common_neighbors if self.graph.degree(n) > 1)
            feat.append(adamic_adar)
            
            # 3. Preferential attachment
            pref_attach = len(neighbors1) * len(neighbors2)
            feat.append(pref_attach)
            
            # 4. Cosine similarity (embeddings)
            if node1 in self.embeddings and node2 in self.embeddings:
                emb1 = self.embeddings[node1]
                emb2 = self.embeddings[node2]
                
                cos_sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                feat.append(cos_sim)
            else:
                feat.append(0)
            
            # 5. Même école
            schools1 = set(self.graph.nodes[node1].get('schools', []))
            schools2 = set(self.graph.nodes[node2].get('schools', []))
            same_school = 1 if len(schools1 & schools2) > 0 else 0
            feat.append(same_school)
            
            # 6. Même entreprise
            companies1 = set(self.graph.nodes[node1].get('companies', []))
            companies2 = set(self.graph.nodes[node2].get('companies', []))
            same_company = 1 if len(companies1 & companies2) > 0 else 0
            feat.append(same_company)
            
            # 7. Compétences communes
            skills1 = set(self.graph.nodes[node1].get('skills', []))
            skills2 = set(self.graph.nodes[node2].get('skills', []))
            common_skills = len(skills1 & skills2)
            feat.append(common_skills)
            
            features.append(feat)
        
        features = np.array(features)
        
        print(f"✅ Features extraites : shape {features.shape}")
        
        return features
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2
    ) -> Dict:
        """
        Entraîne le modèle Random Forest.
        
        Args:
            X: Feature matrix
            y: Labels
            test_size: Proportion test set
        
        Returns:
            Métriques d'évaluation
        """
        print("\n🔄 Entraînement du modèle...")
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y
        )
        
        print(f"   Train set : {len(X_train)}")
        print(f"   Test set  : {len(X_test)}")
        
        # Entraîner Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        self.model.fit(X_train, y_train)
        
        print("✅ Entraînement terminé")
        
        # Évaluation
        print("\n📊 Évaluation sur test set...")
        
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Métriques
        auc = roc_auc_score(y_test, y_proba)
        
        print(f"\n🎯 AUC-ROC : {auc:.4f}")
        
        print("\n📋 Classification Report :")
        print(classification_report(y_test, y_pred, target_names=['No Link', 'Link']))
        
        print("\n📊 Confusion Matrix :")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        
        # Importance des features
        feature_names = [
            'Jaccard',
            'Adamic-Adar',
            'Pref. Attach.',
            'Cosine Sim.',
            'Same School',
            'Same Company',
            'Common Skills'
        ]
        
        importances = self.model.feature_importances_
        
        print("\n💡 Feature Importances :")
        for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True):
            print(f"   {name:<20} : {imp:.4f}")
        
        return {
            'auc': auc,
            'accuracy': (y_pred == y_test).mean(),
            'feature_importances': dict(zip(feature_names, importances))
        }
    
    def predict_new_links(self, top_k: int = 20) -> List[Tuple]:
        """
        Prédit les top K nouvelles connexions probables.
        
        Args:
            top_k: Nombre de prédictions
        
        Returns:
            Liste de (node1, node2, probability)
        """
        print(f"\n🔄 Prédiction des top {top_k} nouvelles connexions...")
        
        nodes = list(self.graph.nodes())
        
        # Générer toutes les paires non connectées (échantillon)
        n_samples = min(10000, len(nodes) * (len(nodes) - 1) // 2)
        
        candidate_pairs = []
        edge_set = set(self.graph.edges())
        edge_set.update((b, a) for a, b in self.graph.edges())
        
        while len(candidate_pairs) < n_samples:
            node1, node2 = random.sample(nodes, 2)
            
            if (node1, node2) not in edge_set:
                candidate_pairs.append((node1, node2))
        
        print(f"   {len(candidate_pairs)} paires candidates")
        
        # Extraire features
        X_candidates = self.extract_features(candidate_pairs)
        
        # Prédire probabilités
        probas = self.model.predict_proba(X_candidates)[:, 1]
        
        # Top K
        top_indices = np.argsort(probas)[-top_k:][::-1]
        
        predictions = [
            (candidate_pairs[i][0], candidate_pairs[i][1], probas[i])
            for i in top_indices
        ]
        
        print(f"✅ Top {top_k} prédictions générées")
        
        return predictions
    
    def save_model(self, filepath: str = "data/models/link_predictor.pkl"):
        """Sauvegarde le modèle."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(self.model, f)
        
        print(f"\n✅ Modèle sauvegardé : {filepath}")