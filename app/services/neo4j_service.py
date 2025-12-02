"""
Service Neo4j - Gestion de la connexion et opérations de base
"""
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class Neo4jService:
    """Service pour interagir avec Neo4j"""
    
    def __init__(self):
        """Initialiser la connexion Neo4j"""
        self.driver = None
        self.connect()
    
    def connect(self):
        """Établir la connexion avec Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            # Test de connexion
            self.driver.verify_connectivity()
            logger.info("✅ Connexion Neo4j réussie")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Neo4j : {e}")
            raise
    
    def close(self):
        """Fermer la connexion"""
        if self.driver:
            self.driver.close()
            logger.info("🔌 Connexion Neo4j fermée")
    
    def execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        Exécuter une requête Cypher
        
        Args:
            query: Requête Cypher
            parameters: Paramètres de la requête
            
        Returns:
            Liste des résultats
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def execute_write(self, query: str, parameters: Dict = None) -> Dict:
        """
        Exécuter une requête d'écriture
        
        Args:
            query: Requête Cypher
            parameters: Paramètres de la requête
            
        Returns:
            Résumé de l'exécution
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            summary = result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "properties_set": summary.counters.properties_set
            }
    
    def clear_database(self):
        """Vider complètement la base de données (ATTENTION !)"""
        query = "MATCH (n) DETACH DELETE n"
        with self.driver.session() as session:
            result = session.run(query)
            summary = result.consume()
            logger.warning(f"🗑️ Base vidée : {summary.counters.nodes_deleted} nœuds supprimés")
            return summary.counters.nodes_deleted
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Obtenir les statistiques de la base
        
        Returns:
            Dictionnaire avec les compteurs
        """
        queries = {
            "persons": "MATCH (p:Person) RETURN COUNT(p) as count",
            "companies": "MATCH (c:Company) RETURN COUNT(c) as count",
            "schools": "MATCH (s:School) RETURN COUNT(s) as count",
            "skills": "MATCH (k:Skill) RETURN COUNT(k) as count",
            "works_at": "MATCH ()-[r:WORKS_AT]->() RETURN COUNT(r) as count",
            "has_skill": "MATCH ()-[r:HAS_SKILL]->() RETURN COUNT(r) as count",
            "studied_at": "MATCH ()-[r:STUDIED_AT]->() RETURN COUNT(r) as count",
            "knows": "MATCH ()-[r:KNOWS]->() RETURN COUNT(r) as count",
            "similar_to": "MATCH ()-[r:SIMILAR_TO]->() RETURN COUNT(r) as count"
        }
        
        stats = {}
        for key, query in queries.items():
            result = self.execute_query(query)
            stats[key] = result[0]["count"] if result else 0
        
        return stats
    
    def create_constraints(self):
        """Créer les contraintes d'unicité sur la base"""
        constraints = [
            "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.normalized_name IS UNIQUE",
            "CREATE CONSTRAINT school_name IF NOT EXISTS FOR (s:School) REQUIRE s.normalized_name IS UNIQUE",
            "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (k:Skill) REQUIRE k.name IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                self.execute_write(constraint)
                logger.info(f"✅ Contrainte créée")
            except Exception as e:
                logger.warning(f"⚠️ Contrainte déjà existante ou erreur : {e}")
    
    def create_indexes(self):
        """Créer les index pour optimiser les requêtes"""
        indexes = [
            "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
            "CREATE INDEX skill_category IF NOT EXISTS FOR (k:Skill) ON (k.category)"
        ]
        
        for index in indexes:
            try:
                self.execute_write(index)
                logger.info(f"✅ Index créé")
            except Exception as e:
                logger.warning(f"⚠️ Index déjà existant ou erreur : {e}")
    
    def __enter__(self):
        """Support du context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fermer la connexion à la sortie du context"""
        self.close()


# Instance globale
_neo4j_service = None

def get_neo4j_service() -> Neo4jService:
    """Obtenir l'instance du service Neo4j (singleton)"""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    return _neo4j_service