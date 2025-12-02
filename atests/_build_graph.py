"""
Script principal pour construire le graphe Neo4j à partir des données enrichies MongoDB
"""
import logging
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.services.neo4j_service import get_neo4j_service
from app.graph.nodes import GraphNodesBuilder
from app.graph.relationships import GraphRelationshipsBuilder

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Construire le graphe complet"""
    start_time = time.time()
    
    print("\n" + "="*80)
    print("🚀 CONSTRUCTION DU GRAPHE NEO4J")
    print("="*80 + "\n")
    
    try:
        # Connexion Neo4j
        logger.info("📡 Connexion à Neo4j...")
        neo4j = get_neo4j_service()
        
        # Choix : vider la base ou non
        response = input("\n⚠️  Voulez-vous vider la base Neo4j avant l'import ? (o/N) : ")
        if response.lower() == 'o':
            logger.info("🗑️  Vidage de la base Neo4j...")
            nodes_deleted = neo4j.clear_database()
            logger.info(f"✅ {nodes_deleted} nœuds supprimés")
        
        # Créer les contraintes et index
        logger.info("\n📋 Création des contraintes et index...")
        neo4j.create_constraints()
        neo4j.create_indexes()
        logger.info("✅ Contraintes et index créés")
        
        # Construction des nœuds
        logger.info("\n" + "="*80)
        logger.info("ÉTAPE 1/2 : CONSTRUCTION DES NŒUDS")
        logger.info("="*80)
        
        nodes_builder = GraphNodesBuilder(neo4j)
        nodes_stats = nodes_builder.build_all_nodes()
        
        # Construction des relations
        logger.info("\n" + "="*80)
        logger.info("ÉTAPE 2/2 : CONSTRUCTION DES RELATIONS")
        logger.info("="*80)
        
        rels_builder = GraphRelationshipsBuilder(neo4j)
        rels_stats = rels_builder.build_all_relationships()
        
        # Statistiques finales
        logger.info("\n" + "="*80)
        logger.info("📊 STATISTIQUES FINALES NEO4J")
        logger.info("="*80)
        
        final_stats = neo4j.get_statistics()
        
        logger.info("\n🎯 NŒUDS :")
        logger.info(f"   Persons   : {final_stats['persons']}")
        logger.info(f"   Companies : {final_stats['companies']}")
        logger.info(f"   Schools   : {final_stats['schools']}")
        logger.info(f"   Skills    : {final_stats['skills']}")
        logger.info(f"   TOTAL     : {sum([final_stats['persons'], final_stats['companies'], final_stats['schools'], final_stats['skills']])}")
        
        logger.info("\n🔗 RELATIONS :")
        logger.info(f"   WORKS_AT   : {final_stats['works_at']}")
        logger.info(f"   HAS_SKILL  : {final_stats['has_skill']}")
        logger.info(f"   STUDIED_AT : {final_stats['studied_at']}")
        logger.info(f"   TOTAL      : {final_stats['works_at'] + final_stats['has_skill'] + final_stats['studied_at']}")
        
        # Temps d'exécution
        duration = time.time() - start_time
        logger.info(f"\n⏱️  Durée totale : {duration:.1f}s")
        
        # Accès Neo4j Browser
        print("\n" + "="*80)
        print("✅ GRAPHE CONSTRUIT AVEC SUCCÈS !")
        print("="*80)
        print("\n🌐 Accédez à Neo4j Browser : http://localhost:7474")
        print("\n📊 Requêtes de test :")
        print("""
        // Voir quelques personnes
        MATCH (p:Person) RETURN p LIMIT 10
        
        // Voir le graphe complet (attention si > 100 nœuds)
        MATCH (n) RETURN n LIMIT 100
        
        // Qui travaille où ?
        MATCH (p:Person)-[:WORKS_AT]->(c:Company)
        RETURN p.name, c.name LIMIT 20
        
        // Qui a quelles compétences ?
        MATCH (p:Person)-[:HAS_SKILL]->(k:Skill)
        RETURN p.name, COLLECT(k.name) as skills LIMIT 10
        
        // Statistiques
        CALL db.schema.visualization()
        """)
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ ERREUR : {e}")
        raise
    finally:
        # Fermer la connexion
        if 'neo4j' in locals():
            neo4j.close()

if __name__ == "__main__":
    main()