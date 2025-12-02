"""
Community Detection pour GraphMind.

Détecte les communautés de profils similaires en utilisant l'algorithme Louvain.
"""

from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict

import networkx as nx
from neo4j import GraphDatabase
import numpy as np


class CommunityDetector:
    """
    Détecte et analyse les communautés dans le graphe.
    
    Architecture :
    1. Charger graphe depuis Neo4j
    2. Appliquer algorithme Louvain
    3. Analyser caractéristiques de chaque communauté
    4. Sauvegarder résultats
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "your_password"
    ):
        """
        Initialise le détecteur de communautés.
        
        Args:
            uri: URI Neo4j
            user: Utilisateur Neo4j
            password: Mot de passe Neo4j
        """
        self.uri = uri
        self.user = user
        self.password = password
        
        self.graph = None
        self.communities = {}  # {node_id: community_id}
        self.community_data = {}  # Métadonnées des communautés
        
        print("✅ CommunityDetector initialisé")
    
    def load_graph_from_neo4j(self) -> nx.Graph:
        """
        Charge le graphe depuis Neo4j.
        
        Returns:
            Graphe NetworkX
        """
        print("🔄 Chargement graphe depuis Neo4j...")
        
        driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        G = nx.Graph()
        
        with driver.session() as session:
            # Charger nœuds Person avec métadonnées
            result = session.run("""
                MATCH (p:Person)
                OPTIONAL MATCH (p)-[:HAS_SKILL]->(s:Skill)
                OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company)
                OPTIONAL MATCH (p)-[:STUDIED_AT]->(sc:School)
                RETURN p.name as name,
                       COALESCE(p.linkedin_id, p.name) as id,
                       p.position as position,
                       collect(DISTINCT s.name) as skills,
                       collect(DISTINCT c.name) as companies,
                       collect(DISTINCT sc.name) as schools
            """)
            
            nodes_count = 0
            for record in result:
                node_id = record["id"]
                if node_id:
                    G.add_node(
                        node_id,
                        name=record["name"],
                        position=record["position"],
                        skills=record["skills"],
                        companies=record["companies"],
                        schools=record["schools"]
                    )
                    nodes_count += 1
            
            print(f"   ✅ {nodes_count} nœuds chargés")
            
            # Charger relations Person-Person
            result = session.run("""
                MATCH (p1:Person)-[r]->(p2:Person)
                RETURN COALESCE(p1.linkedin_id, p1.name) as source,
                       COALESCE(p2.linkedin_id, p2.name) as target,
                       type(r) as rel_type
            """)
            
            edges_count = 0
            for record in result:
                source = record["source"]
                target = record["target"]
                rel_type = record["rel_type"]
                
                if source in G.nodes and target in G.nodes:
                    # Ajouter poids selon type de relation
                    weight = self._get_relation_weight(rel_type)
                    
                    if G.has_edge(source, target):
                        # Cumuler les poids si plusieurs relations
                        G[source][target]['weight'] += weight
                    else:
                        G.add_edge(source, target, weight=weight, relation=rel_type)
                    
                    edges_count += 1
            
            print(f"   ✅ {edges_count} relations chargées")
        
        driver.close()
        
        self.graph = G
        
        print(f"✅ Graphe chargé : {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes")
        
        return G
    
    def _get_relation_weight(self, rel_type: str) -> float:
        """
        Retourne le poids d'une relation selon son type.
        
        Args:
            rel_type: Type de relation
        
        Returns:
            Poids (float)
        """
        weights = {
            'SIMILAR_TO': 5.0,       # Forte similarité (compétences)
            'STUDIED_TOGETHER': 3.0,  # Même école
            'KNOWS': 0.5              # Même entreprise
        }
        
        return weights.get(rel_type, 1.0)
    
    def detect_communities(self, algorithm: str = "louvain") -> Dict[str, int]:
        """
        Détecte les communautés avec l'algorithme spécifié.
        
        Args:
            algorithm: "louvain", "label_propagation", ou "greedy_modularity"
        
        Returns:
            Dictionnaire {node_id: community_id}
        """
        if self.graph is None:
            raise ValueError("⚠️ Chargez d'abord le graphe avec load_graph_from_neo4j()")
        
        print(f"\n🔄 Détection de communautés avec {algorithm.upper()}...")
        
        if algorithm == "louvain":
            # Louvain (nécessite python-louvain)
            try:
                import community as community_louvain
                
                self.communities = community_louvain.best_partition(
                    self.graph,
                    weight='weight',
                    random_state=42
                )
            except ImportError:
                print("⚠️  python-louvain non installé")
                print("   Installation : pip install python-louvain")
                print("   Utilisation de greedy_modularity à la place...")
                return self.detect_communities(algorithm="greedy_modularity")
        
        elif algorithm == "label_propagation":
            # Label Propagation
            communities_generator = nx.algorithms.community.label_propagation_communities(self.graph)
            communities_list = list(communities_generator)
            
            self.communities = {}
            for comm_id, members in enumerate(communities_list):
                for node in members:
                    self.communities[node] = comm_id
        
        elif algorithm == "greedy_modularity":
            # Greedy Modularity
            communities_generator = nx.algorithms.community.greedy_modularity_communities(
                self.graph,
                weight='weight'
            )
            communities_list = list(communities_generator)
            
            self.communities = {}
            for comm_id, members in enumerate(communities_list):
                for node in members:
                    self.communities[node] = comm_id
        
        else:
            raise ValueError(f"Algorithme inconnu : {algorithm}")
        
        # Compter communautés
        n_communities = len(set(self.communities.values()))
        
        print(f"✅ {n_communities} communautés détectées")
        
        # Calculer modularité
        modularity = self._calculate_modularity()
        print(f"✅ Modularité : {modularity:.4f}")
        
        return self.communities
    
    def _calculate_modularity(self) -> float:
        """
        Calcule la modularité du partitionnement.
        
        Returns:
            Score de modularité (0-1, plus élevé = meilleur)
        """
        # Créer liste de sets pour chaque communauté
        communities_list = defaultdict(set)
        for node, comm_id in self.communities.items():
            communities_list[comm_id].add(node)
        
        communities_sets = list(communities_list.values())
        
        modularity = nx.algorithms.community.modularity(
            self.graph,
            communities_sets,
            weight='weight'
        )
        
        return modularity
    
    def analyze_communities(self) -> Dict:
        """
        Analyse les caractéristiques de chaque communauté.
        
        Returns:
            Dictionnaire avec stats par communauté
        """
        if not self.communities:
            raise ValueError("⚠️ Détectez d'abord les communautés avec detect_communities()")
        
        print("\n🔄 Analyse des communautés...")
        
        # Regrouper nœuds par communauté
        community_members = defaultdict(list)
        for node, comm_id in self.communities.items():
            community_members[comm_id].append(node)
        
        # Analyser chaque communauté
        for comm_id, members in community_members.items():
            
            # Collecter métadonnées
            all_skills = []
            all_companies = []
            all_schools = []
            positions = []
            
            for node in members:
                node_data = self.graph.nodes[node]
                
                all_skills.extend(node_data.get('skills', []))
                all_companies.extend(node_data.get('companies', []))
                all_schools.extend(node_data.get('schools', []))
                
                position = node_data.get('position')
                if position:
                    positions.append(position)
            
            # Compter fréquences
            skill_counts = Counter(all_skills)
            company_counts = Counter(all_companies)
            school_counts = Counter(all_schools)
            
            # Stocker analyse
            self.community_data[comm_id] = {
                'size': len(members),
                'members': members[:10],  # Sauvegarder que 10 premiers
                'top_skills': skill_counts.most_common(10),
                'top_companies': company_counts.most_common(5),
                'top_schools': school_counts.most_common(5),
                'sample_positions': positions[:5]
            }
        
        print(f"✅ {len(self.community_data)} communautés analysées")
        
        return self.community_data
    
    def print_community_summary(self):
        """Affiche un résumé des communautés."""
        if not self.community_data:
            print("⚠️ Analysez d'abord les communautés avec analyze_communities()")
            return
        
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DES COMMUNAUTÉS")
        print("="*80)
        
        # Trier par taille décroissante
        sorted_communities = sorted(
            self.community_data.items(),
            key=lambda x: x[1]['size'],
            reverse=True
        )
        
        for comm_id, data in sorted_communities:
            print(f"\n{'='*80}")
            print(f"🏘️  COMMUNAUTÉ {comm_id}")
            print(f"{'='*80}")
            
            print(f"\n📊 Taille : {data['size']} profils")
            
            # Top compétences
            print(f"\n💡 Top 5 Compétences :")
            for skill, count in data['top_skills'][:5]:
                pct = (count / data['size']) * 100
                print(f"   • {skill:<20} : {count:>3} profils ({pct:.1f}%)")
            
            # Top écoles
            if data['top_schools']:
                print(f"\n🎓 Top 3 Écoles :")
                for school, count in data['top_schools'][:3]:
                    pct = (count / data['size']) * 100
                    print(f"   • {school:<30} : {count:>3} profils ({pct:.1f}%)")
            
            # Top entreprises
            if data['top_companies']:
                print(f"\n🏢 Top 3 Entreprises :")
                for company, count in data['top_companies'][:3]:
                    pct = (count / data['size']) * 100
                    print(f"   • {company:<30} : {count:>3} profils ({pct:.1f}%)")
            
            # Exemples de postes
            if data['sample_positions']:
                print(f"\n💼 Exemples de postes :")
                for position in data['sample_positions'][:3]:
                    print(f"   • {position}")
    
    def save_results(self, filepath: str = "data/reports/communities.json"):
        """
        Sauvegarde les résultats.
        
        Args:
            filepath: Chemin du fichier JSON
        """
        import json
        from pathlib import Path
        
        # Créer dossier
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Préparer données
        data = {
            'n_communities': len(set(self.communities.values())),
            'modularity': self._calculate_modularity(),
            'communities': self.community_data,
            'assignments': self.communities
        }
        
        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Résultats sauvegardés : {filepath}")