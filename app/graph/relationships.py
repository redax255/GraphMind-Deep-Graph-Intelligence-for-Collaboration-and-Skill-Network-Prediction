"""
Construction des relations du graphe Neo4j
"""
from typing import Dict
from app.config import settings
from app.services.neo4j_service import Neo4jService
from app.services.database import get_db_client
import logging

logger = logging.getLogger(__name__)

class GraphRelationshipsBuilder:
    """Constructeur des relations du graphe"""
    
    def __init__(self, neo4j_service: Neo4jService):
        self.neo4j = neo4j_service
        # Créer un client avec la collection enrichie
        from app.services.database import MongoDBClient
        self.mongodb = MongoDBClient(collection_name=settings.mongodb_collection_enriched)
        self.mongodb.connect()
    
    def create_works_at_relationships(self) -> int:
        """
        Créer les relations WORKS_AT (Person → Company)
        
        Returns:
            Nombre de relations créées
        """
        logger.info("🔄 Création des relations WORKS_AT...")
        
        profiles = list(self.mongodb.get_all_profiles())
        count = 0
        
        for profile in profiles:
            person_id = str(profile["_id"])
            
            if "experience_enriched" in profile:
                for exp in profile["experience_enriched"]:
                    company_name = exp.get("company_normalized")
                    
                    if not company_name or not isinstance(company_name, str):
                        continue
                    
                    try:
                        # Propriétés de la relation
                        props = {
                            "position": exp.get("position", ""),
                            "start_date": exp.get("start_date"),
                            "end_date": exp.get("end_date"),
                            "duration_months": exp.get("duration_months", 0),
                            "is_current": exp.get("is_current", False),
                            "location": exp.get("location", "")
                        }
                        
                        query = """
                        MATCH (p:Person {id: $person_id})
                        MATCH (c:Company {normalized_name: $company_name})
                        MERGE (p)-[r:WORKS_AT]->(c)
                        SET r += $props
                        """
                        
                        self.neo4j.execute_write(query, {
                            "person_id": person_id,
                            "company_name": company_name,
                            "props": props
                        })
                        
                        count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur WORKS_AT {person_id} → {company_name}: {e}")
        
        logger.info(f"✅ {count} relations WORKS_AT créées")
        return count
    
    def create_has_skill_relationships(self) -> int:
        """
        Créer les relations HAS_SKILL (Person → Skill)
        
        Returns:
            Nombre de relations créées
        """
        logger.info("🔄 Création des relations HAS_SKILL...")
        
        profiles = list(self.mongodb.get_all_profiles())
        count = 0
        
        for profile in profiles:
            person_id = str(profile["_id"])
            
            if "skills_extracted" in profile:
                skills = profile["skills_extracted"]
                
                for skill in skills:
                    skill_name = skill if isinstance(skill, str) else skill.get("skill")
                    
                    if not skill_name:
                        continue
                    
                    try:
                        # Propriétés de la relation
                        props = {}
                        if isinstance(skill, dict):
                            props = {
                                "proficiency": skill.get("proficiency", "intermediate"),
                                "source": skill.get("source", "extracted")
                            }
                        
                        query = """
                        MATCH (p:Person {id: $person_id})
                        MATCH (k:Skill {name: $skill_name})
                        MERGE (p)-[r:HAS_SKILL]->(k)
                        SET r += $props
                        """
                        
                        self.neo4j.execute_write(query, {
                            "person_id": person_id,
                            "skill_name": skill_name,
                            "props": props
                        })
                        
                        count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur HAS_SKILL {person_id} → {skill_name}: {e}")
        
        logger.info(f"✅ {count} relations HAS_SKILL créées")
        return count
    
    def create_studied_at_relationships(self) -> int:
        """
        Créer les relations STUDIED_AT (Person → School)
        
        Returns:
            Nombre de relations créées
        """
        logger.info("🔄 Création des relations STUDIED_AT...")
        
        profiles = list(self.mongodb.get_all_profiles())
        count = 0
        
        for profile in profiles:
            person_id = str(profile["_id"])
            
            if "education_enriched" in profile:
                for edu in profile["education_enriched"]:
                    # Gérer la normalisation qui peut être dict ou string
                    school_norm = edu.get("university_normalized")
                    if school_norm:
                        if isinstance(school_norm, dict):
                            school_name = edu.get("university", "")
                        else:
                            school_name = school_norm
                    else:
                        school_name = edu.get("university", "")
                    
                    if not school_name:
                        continue
                    
                    try:
                        # Propriétés de la relation
                        props = {
                            "degree": edu.get("degree", ""),
                            "field": edu.get("field", ""),
                            "start_date": edu.get("start_date"),
                            "end_date": edu.get("end_date")
                        }
                        
                        query = """
                        MATCH (p:Person {id: $person_id})
                        MATCH (s:School {normalized_name: $school_name})
                        MERGE (p)-[r:STUDIED_AT]->(s)
                        SET r += $props
                        """
                        
                        self.neo4j.execute_write(query, {
                            "person_id": person_id,
                            "school_name": school_name,
                            "props": props
                        })
                        
                        count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur STUDIED_AT {person_id} → {school_name}: {e}")
        
        logger.info(f"✅ {count} relations STUDIED_AT créées")
        return count
    
    def build_all_relationships(self) -> Dict[str, int]:
        """
        Construire toutes les relations de base du graphe
        
        Returns:
            Dictionnaire avec les compteurs
        """
        logger.info("\n" + "="*80)
        logger.info("🔗 CONSTRUCTION DES RELATIONS DU GRAPHE")
        logger.info("="*80 + "\n")
        
        stats = {
            "works_at": self.create_works_at_relationships(),
            "has_skill": self.create_has_skill_relationships(),
            "studied_at": self.create_studied_at_relationships()
        }
        
        total = sum(stats.values())
        
        logger.info("\n" + "="*80)
        logger.info("✅ RELATIONS CRÉÉES AVEC SUCCÈS")
        logger.info("="*80)
        logger.info(f"   WORKS_AT   : {stats['works_at']}")
        logger.info(f"   HAS_SKILL  : {stats['has_skill']}")
        logger.info(f"   STUDIED_AT : {stats['studied_at']}")
        logger.info(f"   TOTAL      : {total}")
        logger.info("="*80 + "\n")
        
        return stats