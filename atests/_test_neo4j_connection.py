"""
Test de connexion à Neo4j
"""
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.neo4j_service import get_neo4j_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Tester la connexion à Neo4j"""
    print("\n" + "="*60)
    print("🧪 TEST DE CONNEXION NEO4J")
    print("="*60 + "\n")
    
    try:
        # Connexion
        logger.info("📡 Connexion à Neo4j...")
        neo4j = get_neo4j_service()
        logger.info("✅ Connexion réussie!")
        
        # Test simple
        logger.info("\n🧪 Test d'écriture...")
        query = """
        CREATE (test:Test {name: 'Hello Neo4j!', timestamp: datetime()})
        RETURN test
        """
        result = neo4j.execute_query(query)
        logger.info(f"✅ Nœud de test créé : {result}")
        
        # Lecture
        logger.info("\n🧪 Test de lecture...")
        query = "MATCH (test:Test) RETURN test"
        result = neo4j.execute_query(query)
        logger.info(f"✅ Nœud lu : {result}")
        
        # Nettoyage
        logger.info("\n🧹 Nettoyage...")
        query = "MATCH (test:Test) DELETE test"
        neo4j.execute_write(query)
        logger.info("✅ Nœud de test supprimé")
        
        # Statistiques
        logger.info("\n📊 Statistiques de la base...")
        stats = neo4j.get_statistics()
        for key, value in stats.items():
            logger.info(f"   {key:15s} : {value}")
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS RÉUSSIS !")
        print("="*60 + "\n")
        
        print("🌐 Neo4j Browser : http://localhost:7474")
        print("🔑 Username : neo4j")
        print("🔑 Password : Redax@255")
        print()
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERREUR DE CONNEXION")
        print("="*60)
        logger.error(f"\n{e}\n")
        print("🔧 Vérifications à faire :")
        print("   1. Neo4j Desktop est lancé ?")
        print("   2. Base 'linkedin_graph' est started ?")
        print("   3. Mot de passe correct (Redax@255) ?")
        print("   4. Port 7687 disponible ?")
        print()
    finally:
        if 'neo4j' in locals():
            neo4j.close()

if __name__ == "__main__":
    test_connection()