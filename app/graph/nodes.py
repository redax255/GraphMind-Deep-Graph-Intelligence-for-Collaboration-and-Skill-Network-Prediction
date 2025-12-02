"""
Construction des nœuds du graphe Neo4j
"""
from typing import Dict, List
from app.config import settings
from app.services.neo4j_service import Neo4jService
from app.services.database import get_db_client
import logging

logger = logging.getLogger(__name__)

class GraphNodesBuilder:
    """Constructeur des nœuds du graphe"""
    
    def __init__(self, neo4j_service: Neo4jService):
        self.neo4j = neo4j_service
        # Créer un client avec la collection enrichie
        from app.services.database import MongoDBClient
        self.mongodb = MongoDBClient(collection_name=settings.mongodb_collection_enriched)
        self.mongodb.connect()
    
    def create_person_nodes(self) -> int:
        """
        Créer les nœuds Person depuis MongoDB
        
        Returns:
            Nombre de nœuds créés
        """
        logger.info("🔄 Création des nœuds Person...")
        
        # Récupérer les profils enrichis
        profiles = list(self.mongodb.get_all_profiles())
        
        count = 0
        for profile in profiles:
            try:
                # Préparer les propriétés
                properties = {
                    "id": str(profile["_id"]),
                    "first_name": profile.get("first_name", ""),
                    "last_name": profile.get("last_name", ""),
                    "name": f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
                    "location": profile.get("location", ""),
                    "position": profile.get("position", ""),
                    "linkedin_url": profile.get("linkedinUrl", "")
                }
                
                # Ajouter les stats si disponibles
                if "stats" in profile:
                    stats = profile["stats"]
                    properties.update({
                        "total_experience_years": stats.get("total_experience_years", 0),
                        "skills_count": stats.get("skills_count", 0),
                        "companies_count": stats.get("companies_count", 0),
                        "schools_count": stats.get("schools_count", 0)
                    })
                
                # Créer le nœud
                query = """
                MERGE (p:Person {id: $id})
                SET p += $properties
                """
                self.neo4j.execute_write(query, {
                    "id": properties["id"],
                    "properties": properties
                })
                
                count += 1
                if count % 50 == 0:
                    logger.info(f"   {count}/{len(profiles)} personnes créées")
                
            except Exception as e:
                logger.error(f"❌ Erreur création Person {profile.get('_id')}: {e}")
        
        logger.info(f"✅ {count} nœuds Person créés")
        return count
    
    def create_company_nodes(self) -> int:
        """
        Créer les nœuds Company depuis MongoDB
        
        Returns:
            Nombre de nœuds créés
        """
        logger.info("🔄 Création des nœuds Company...")
        
        # Récupérer toutes les entreprises uniques
        profiles = list(self.mongodb.get_all_profiles())
        companies = set()
        
        for profile in profiles:
            if "experience_enriched" in profile:
                for exp in profile["experience_enriched"]:
                    company_name = exp.get("company_normalized")
                    if company_name and isinstance(company_name, str):
                        companies.add(company_name)
        
        count = 0
        for company_name in companies:
            try:
                query = """
                MERGE (c:Company {normalized_name: $name})
                SET c.name = $name
                """
                self.neo4j.execute_write(query, {"name": company_name})
                count += 1
                
                if count % 50 == 0:
                    logger.info(f"   {count}/{len(companies)} entreprises créées")
                    
            except Exception as e:
                logger.error(f"❌ Erreur création Company {company_name}: {e}")
        
        logger.info(f"✅ {count} nœuds Company créés")
        return count
    
    def create_school_nodes(self) -> int:
        """
        Créer les nœuds School depuis MongoDB
        
        Returns:
            Nombre de nœuds créés
        """
        logger.info("🔄 Création des nœuds School...")
        
        # Récupérer toutes les écoles uniques
        profiles = list(self.mongodb.get_all_profiles())
        schools = set()
        
        for profile in profiles:
            if "education_enriched" in profile:
                for edu in profile["education_enriched"]:
                    # La normalisation peut être un dict ou une string
                    school_norm = edu.get("university_normalized")
                    if school_norm:
                        if isinstance(school_norm, dict):
                            # Reconstruire le nom depuis le dict
                            school_name = edu.get("university", "")
                        else:
                            school_name = school_norm
                        
                        if school_name:
                            schools.add(school_name)
        
        count = 0
        for school_name in schools:
            try:
                query = """
                MERGE (s:School {normalized_name: $name})
                SET s.name = $name
                """
                self.neo4j.execute_write(query, {"name": school_name})
                count += 1
                
                if count % 50 == 0:
                    logger.info(f"   {count}/{len(schools)} écoles créées")
                    
            except Exception as e:
                logger.error(f"❌ Erreur création School {school_name}: {e}")
        
        logger.info(f"✅ {count} nœuds School créés")
        return count
    
    def create_skill_nodes(self) -> int:
        """
        Créer les nœuds Skill depuis MongoDB
        
        Returns:
            Nombre de nœuds créés
        """
        logger.info("🔄 Création des nœuds Skill...")
        
        # Récupérer toutes les compétences uniques
        profiles = list(self.mongodb.get_all_profiles())
        skills = {}  # {skill_name: category}
        
        for profile in profiles:
            if "skills_extracted" in profile:
                for skill in profile["skills_extracted"]:
                    if isinstance(skill, str):
                        skills[skill] = "Unknown"
                    elif isinstance(skill, dict):
                        skill_name = skill.get("skill")
                        category = skill.get("category", "Unknown")
                        if skill_name:
                            skills[skill_name] = category
        
        count = 0
        for skill_name, category in skills.items():
            try:
                query = """
                MERGE (k:Skill {name: $name})
                SET k.category = $category
                """
                self.neo4j.execute_write(query, {
                    "name": skill_name,
                    "category": category
                })
                count += 1
                
                if count % 50 == 0:
                    logger.info(f"   {count}/{len(skills)} compétences créées")
                    
            except Exception as e:
                logger.error(f"❌ Erreur création Skill {skill_name}: {e}")
        
        logger.info(f"✅ {count} nœuds Skill créés")
        return count
    
    def build_all_nodes(self) -> Dict[str, int]:
        """
        Construire tous les nœuds du graphe
        
        Returns:
            Dictionnaire avec les compteurs
        """
        logger.info("\n" + "="*80)
        logger.info("🏗️  CONSTRUCTION DES NŒUDS DU GRAPHE")
        logger.info("="*80 + "\n")
        
        stats = {
            "persons": self.create_person_nodes(),
            "companies": self.create_company_nodes(),
            "schools": self.create_school_nodes(),
            "skills": self.create_skill_nodes()
        }
        
        total = sum(stats.values())
        
        logger.info("\n" + "="*80)
        logger.info("✅ NŒUDS CRÉÉS AVEC SUCCÈS")
        logger.info("="*80)
        logger.info(f"   Persons   : {stats['persons']}")
        logger.info(f"   Companies : {stats['companies']}")
        logger.info(f"   Schools   : {stats['schools']}")
        logger.info(f"   Skills    : {stats['skills']}")
        logger.info(f"   TOTAL     : {total}")
        logger.info("="*80 + "\n")
        
        return stats