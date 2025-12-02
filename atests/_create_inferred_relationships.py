"""
Script pour créer les relations inférées dans le graphe Neo4j

Relations créées :
- KNOWS : Personnes ayant travaillé dans la même entreprise
- SIMILAR_TO : Personnes avec compétences communes
- STUDIED_TOGETHER : Personnes ayant étudié dans la même école
"""
import logging
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.services.neo4j_service import get_neo4j_service

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_knows_relationships(neo4j) -> int:
    """
    Créer les relations KNOWS via entreprises communes
    
    Principe : Si 2 personnes ont travaillé dans la même entreprise,
    elles se connaissent probablement.
    
    Returns:
        Nombre de relations créées
    """
    logger.info("🔄 Création des relations KNOWS (entreprises communes)...")
    
    query = """
    MATCH (p1:Person)-[:WORKS_AT]->(c:Company)<-[:WORKS_AT]-(p2:Person)
    WHERE p1 <> p2 AND id(p1) < id(p2)
    MERGE (p1)-[r:KNOWS]->(p2)
    SET r.context = 'same_company',
        r.company = c.name,
        r.strength = 0.7
    RETURN COUNT(r) as count
    """
    
    result = neo4j.execute_query(query)
    count = result[0]['count'] if result else 0
    
    logger.info(f"✅ {count} relations KNOWS créées")
    return count

def create_similar_to_relationships(neo4j, min_common_skills: int = 3) -> int:
    """
    Créer les relations SIMILAR_TO via compétences communes
    
    Principe : Si 2 personnes ont ≥ min_common_skills compétences communes,
    elles sont similaires.
    
    Args:
        min_common_skills: Nombre minimum de compétences communes (défaut: 3)
    
    Returns:
        Nombre de relations créées
    """
    logger.info(f"🔄 Création des relations SIMILAR_TO (≥{min_common_skills} compétences communes)...")
    
    query = """
    MATCH (p1:Person)-[:HAS_SKILL]->(k:Skill)<-[:HAS_SKILL]-(p2:Person)
    WHERE p1 <> p2 AND id(p1) < id(p2)
    WITH p1, p2, COUNT(DISTINCT k) as common_skills, COLLECT(DISTINCT k.name) as skills
    WHERE common_skills >= $min_skills
    MERGE (p1)-[r:SIMILAR_TO]->(p2)
    SET r.similarity_score = toFloat(common_skills) / 10.0,
        r.common_skills = common_skills,
        r.common_skill_names = skills
    RETURN COUNT(r) as count
    """
    
    result = neo4j.execute_query(query, {"min_skills": min_common_skills})
    count = result[0]['count'] if result else 0
    
    logger.info(f"✅ {count} relations SIMILAR_TO créées")
    return count

def create_studied_together_relationships(neo4j) -> int:
    """
    Créer les relations STUDIED_TOGETHER via écoles communes
    
    Principe : Si 2 personnes ont étudié dans la même école,
    elles se sont peut-être rencontrées.
    
    Returns:
        Nombre de relations créées
    """
    logger.info("🔄 Création des relations STUDIED_TOGETHER (écoles communes)...")
    
    query = """
    MATCH (p1:Person)-[:STUDIED_AT]->(s:School)<-[:STUDIED_AT]-(p2:Person)
    WHERE p1 <> p2 AND id(p1) < id(p2)
    MERGE (p1)-[r:STUDIED_TOGETHER]->(p2)
    SET r.context = 'same_school',
        r.school = s.name,
        r.strength = 0.6
    RETURN COUNT(r) as count
    """
    
    result = neo4j.execute_query(query)
    count = result[0]['count'] if result else 0
    
    logger.info(f"✅ {count} relations STUDIED_TOGETHER créées")
    return count

def get_inferred_stats(neo4j) -> dict:
    """
    Obtenir les statistiques des relations inférées
    
    Returns:
        Dictionnaire avec les compteurs
    """
    stats = {}
    
    queries = {
        "knows": "MATCH ()-[r:KNOWS]->() RETURN COUNT(r) as count",
        "similar_to": "MATCH ()-[r:SIMILAR_TO]->() RETURN COUNT(r) as count",
        "studied_together": "MATCH ()-[r:STUDIED_TOGETHER]->() RETURN COUNT(r) as count"
    }
    
    for key, query in queries.items():
        result = neo4j.execute_query(query)
        stats[key] = result[0]["count"] if result else 0
    
    return stats

def main():
    """Créer toutes les relations inférées"""
    start_time = time.time()
    
    print("\n" + "="*80)
    print("🧠 CRÉATION DES RELATIONS INFÉRÉES")
    print("="*80 + "\n")
    
    try:
        # Connexion Neo4j
        logger.info("📡 Connexion à Neo4j...")
        neo4j = get_neo4j_service()
        
        # Statistiques avant
        logger.info("\n📊 Statistiques AVANT :")
        stats_before = neo4j.get_statistics()
        total_relations_before = (
            stats_before['works_at'] + 
            stats_before['has_skill'] + 
            stats_before['studied_at']
        )
        logger.info(f"   Relations de base : {total_relations_before}")
        
        print("\n" + "="*80)
        print("ÉTAPE 1/3 : Relations KNOWS")
        print("="*80)
        knows_count = create_knows_relationships(neo4j)
        
        print("\n" + "="*80)
        print("ÉTAPE 2/3 : Relations SIMILAR_TO")
        print("="*80)
        similar_count = create_similar_to_relationships(neo4j, min_common_skills=3)
        
        print("\n" + "="*80)
        print("ÉTAPE 3/3 : Relations STUDIED_TOGETHER")
        print("="*80)
        studied_count = create_studied_together_relationships(neo4j)
        
        # Statistiques finales
        logger.info("\n" + "="*80)
        logger.info("📊 STATISTIQUES FINALES")
        logger.info("="*80)
        
        inferred_stats = get_inferred_stats(neo4j)
        total_inferred = sum(inferred_stats.values())
        
        logger.info("\n🧠 RELATIONS INFÉRÉES :")
        logger.info(f"   KNOWS              : {inferred_stats['knows']}")
        logger.info(f"   SIMILAR_TO         : {inferred_stats['similar_to']}")
        logger.info(f"   STUDIED_TOGETHER   : {inferred_stats['studied_together']}")
        logger.info(f"   TOTAL INFÉRÉES     : {total_inferred}")
        
        stats_after = neo4j.get_statistics()
        total_relations_after = sum([
            stats_after['works_at'],
            stats_after['has_skill'],
            stats_after['studied_at'],
            stats_after['knows'],
            stats_after['similar_to']
        ])
        
        logger.info(f"\n📊 TOTAL GÉNÉRAL :")
        logger.info(f"   Relations de base  : {total_relations_before}")
        logger.info(f"   Relations inférées : {total_inferred}")
        logger.info(f"   TOTAL              : {total_relations_after}")
        
        # Temps d'exécution
        duration = time.time() - start_time
        logger.info(f"\n⏱️  Durée totale : {duration:.1f}s")
        
        # Requêtes de test
        print("\n" + "="*80)
        print("✅ RELATIONS INFÉRÉES CRÉÉES AVEC SUCCÈS !")
        print("="*80)
        print("\n🌐 Accédez à Neo4j Browser : http://localhost:7474")
        print("\n📊 Requêtes de test :")
        print("""
        // Voir les relations KNOWS
        MATCH (p1:Person)-[r:KNOWS]->(p2:Person)
        RETURN p1.name, r.company, p2.name
        LIMIT 20
        
        // Voir les relations SIMILAR_TO
        MATCH (p1:Person)-[r:SIMILAR_TO]->(p2:Person)
        WHERE r.similarity_score > 0.5
        RETURN p1.name, p2.name, r.common_skills, r.similarity_score
        ORDER BY r.similarity_score DESC
        LIMIT 20
        
        // Voir les relations STUDIED_TOGETHER
        MATCH (p1:Person)-[r:STUDIED_TOGETHER]->(p2:Person)
        RETURN p1.name, r.school, p2.name
        LIMIT 20
        
        // Statistiques complètes
        MATCH ()-[r]->()
        RETURN type(r) as relation_type, COUNT(r) as count
        ORDER BY count DESC
        
        // Réseau complet d'une personne
        MATCH (p:Person {name: "Belkacem Lahouel"})-[r]-(n)
        RETURN p, r, n
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