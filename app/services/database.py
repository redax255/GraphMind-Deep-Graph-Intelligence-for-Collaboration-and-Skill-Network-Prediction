# database.py
"""
Service de gestion de la base de données MongoDB.

Ce module gère :
- Connexion à MongoDB (sync et async)
- Opérations CRUD sur les profils
- Requêtes d'analyse et statistiques
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
import logging

from app.config import settings
from app.models.schemas import Profile

# Import conditionnel pour éviter les warnings de type
if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
else:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================
# CLIENT MONGODB SYNCHRONE (pour scripts)
# ============================================

class MongoDBClient:
    """
    Client MongoDB synchrone.
    
    Utilisé pour :
    - Scripts d'entraînement (train_graph.py, train_ml.py)
    - Notebooks d'exploration
    - Opérations batch
    """
    
    def __init__(self, collection_name: Optional[str] = None):
        """Initialise la connexion MongoDB"""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection_name = collection_name or settings.mongodb_collection_profiles
        self.collection: Optional[Collection] = None
        self.profiles_collection: Optional[Collection] = None
    
    def connect(self) -> None:
        """
        Établit la connexion à MongoDB.
        
        Raises:
            Exception: Si la connexion échoue
        """
        try:
            self.client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000  # Timeout de 5 secondes
            )
            
            # Test de connexion
            self.client.server_info()
            
            # Sélectionner la base de données et collection
            self.db = self.client[settings.mongodb_db_name]
            self.collection = self.db[self.collection_name]
            self.profiles_collection = self.collection
            
            logger.info(f"✅ Connexion MongoDB réussie : {settings.mongodb_db_name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur de connexion MongoDB : {e}")
            raise
    
    def disconnect(self) -> None:
        """Ferme la connexion MongoDB"""
        if self.client:
            self.client.close()
            logger.info("🔌 Connexion MongoDB fermée")
    
    # ============================================
    # LECTURE (READ)
    # ============================================
    
    def get_all_profiles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère tous les profils.
        
        Args:
            limit: Nombre maximum de profils (None = tous)
        
        Returns:
            Liste de profils (dictionnaires)
        """
        try:
            query = self.profiles_collection.find()
            
            if limit:
                query = query.limit(limit)
            
            profiles = list(query)
            logger.info(f"📊 {len(profiles)} profils récupérés")
            return profiles
            
        except Exception as e:
            logger.error(f"❌ Erreur get_all_profiles : {e}")
            return []
    
    def get_profile_by_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un profil par son ID MongoDB.
        
        Args:
            profile_id: ID du profil (_id)
        
        Returns:
            Profil ou None si non trouvé
        """
        try:
            from bson import ObjectId
            profile = self.profiles_collection.find_one({"_id": ObjectId(profile_id)})
            return profile
        except Exception as e:
            logger.error(f"❌ Erreur get_profile_by_id : {e}")
            return None
    
    def get_profile_by_linkedin_url(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un profil par son URL LinkedIn.
        
        Args:
            linkedin_url: URL LinkedIn du profil
        
        Returns:
            Profil ou None si non trouvé
        """
        try:
            profile = self.profiles_collection.find_one({"linkedinUrl": linkedin_url})
            return profile
        except Exception as e:
            logger.error(f"❌ Erreur get_profile_by_linkedin_url : {e}")
            return None
    
    def search_profiles(
        self, 
        query: Dict[str, Any], 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Recherche de profils avec requête personnalisée.
        
        Args:
            query: Requête MongoDB (ex: {"location": "Casablanca"})
            limit: Nombre maximum de résultats
        
        Returns:
            Liste de profils correspondants
        
        Example:
            >>> db.search_profiles({"location": {"$regex": "Maroc", "$options": "i"}})
        """
        try:
            profiles = list(self.profiles_collection.find(query).limit(limit))
            logger.info(f"🔍 {len(profiles)} profils trouvés pour la requête")
            return profiles
        except Exception as e:
            logger.error(f"❌ Erreur search_profiles : {e}")
            return []
    
    # ============================================
    # STATISTIQUES
    # ============================================
    
    def get_total_profiles_count(self) -> int:
        """
        Compte le nombre total de profils.
        
        Returns:
            Nombre de profils
        """
        try:
            count = self.profiles_collection.count_documents({})
            return count
        except Exception as e:
            logger.error(f"❌ Erreur get_total_profiles_count : {e}")
            return 0
    
    def get_profiles_by_location(self) -> Dict[str, int]:
        """
        Compte les profils par localisation.
        
        Returns:
            Dictionnaire {location: count}
        """
        try:
            pipeline = [
                {"$group": {"_id": "$location", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            results = list(self.profiles_collection.aggregate(pipeline))
            return {r["_id"]: r["count"] for r in results if r["_id"]}
        except Exception as e:
            logger.error(f"❌ Erreur get_profiles_by_location : {e}")
            return {}
    
    def get_data_quality_stats(self) -> Dict[str, Any]:
        """
        Analyse la qualité des données.
        
        Returns:
            Statistiques sur la complétude des champs
        """
        try:
            total = self.get_total_profiles_count()
            
            if total == 0:
                return {}
            
            stats = {
                "total_profiles": total,
                "with_resume": self.profiles_collection.count_documents(
                    {"resume": {"$exists": True, "$ne": None, "$ne": ""}}
                ),
                "with_experience": self.profiles_collection.count_documents(
                    {"experience": {"$exists": True, "$ne": []}}
                ),
                "with_formation": self.profiles_collection.count_documents(
                    {"formation": {"$exists": True, "$ne": []}}
                ),
                "with_skills": self.profiles_collection.count_documents(
                    {"skills": {"$exists": True, "$ne": []}}
                ),
                "with_location": self.profiles_collection.count_documents(
                    {"location": {"$exists": True, "$ne": None, "$ne": ""}}
                ),
            }
            
            # Calculer les pourcentages dans un dictionnaire séparé
            percentages = {}
            for key in stats:
                if key != "total_profiles":
                    percentages[f"{key}_percent"] = round((stats[key] / total) * 100, 1)
            
            # Fusionner les deux dictionnaires
            stats.update(percentages)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erreur get_data_quality_stats : {e}")
            return {}
    
    # ============================================
    # CONTEXTE MANAGER (with statement)
    # ============================================
    
    def __enter__(self):
        """Permet d'utiliser 'with MongoDBClient()'"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme automatiquement la connexion"""
        self.disconnect()


# ============================================
# CLIENT MONGODB ASYNCHRONE (pour FastAPI)
# ============================================

class AsyncMongoDBClient:
    """
    Client MongoDB asynchrone.
    
    Utilisé pour :
    - API FastAPI (endpoints async)
    - Opérations en temps réel
    """
    
    def __init__(self):
        """Initialise le client async"""
        self.client: Optional[Any] = None  # AsyncIOMotorClient
        self.db: Optional[Any] = None  # AsyncIOMotorDatabase
    
    async def connect(self) -> None:
        """Établit la connexion asynchrone à MongoDB"""
        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[settings.mongodb_db_name]
            
            # Test de connexion
            await self.client.server_info()
            
            logger.info(f"✅ Connexion async MongoDB réussie : {settings.mongodb_db_name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion async MongoDB : {e}")
            raise
    
    async def disconnect(self) -> None:
        """Ferme la connexion asynchrone"""
        if self.client:
            self.client.close()
            logger.info("🔌 Connexion async MongoDB fermée")
    
    async def get_all_profiles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère tous les profils (async).
        
        Args:
            limit: Nombre maximum de profils
        
        Returns:
            Liste de profils
        """
        try:
            collection = self.db[settings.mongodb_collection_profiles]
            cursor = collection.find()
            
            if limit:
                cursor = cursor.limit(limit)
            
            profiles = await cursor.to_list(length=limit or 1000)
            return profiles
            
        except Exception as e:
            logger.error(f"❌ Erreur async get_all_profiles : {e}")
            return []
    
    async def get_profile_count(self) -> int:
        """Compte le nombre de profils (async)"""
        try:
            collection = self.db[settings.mongodb_collection_profiles]
            count = await collection.count_documents({})
            return count
        except Exception as e:
            logger.error(f"❌ Erreur async get_profile_count : {e}")
            return 0


# ============================================
# INSTANCES GLOBALES
# ============================================

# Instance synchrone (pour scripts)
mongo_client = MongoDBClient()

# Instance asynchrone (pour FastAPI)
async_mongo_client = AsyncMongoDBClient()


# ============================================
# FONCTIONS HELPER
# ============================================

def get_db_client() -> MongoDBClient:
    """
    Retourne le client MongoDB synchrone.
    
    Usage:
        >>> db = get_db_client()
        >>> db.connect()
        >>> profiles = db.get_all_profiles()
    """
    return mongo_client


async def get_async_db_client() -> AsyncMongoDBClient:
    """
    Dépendance FastAPI pour obtenir le client async.
    
    Usage dans FastAPI:
        >>> @app.get("/profiles")
        >>> async def get_profiles(db = Depends(get_async_db_client)):
        >>>     return await db.get_all_profiles()
    """
    return async_mongo_client


# ============================================
# EXPORT
# ============================================

__all__ = [
    "MongoDBClient",
    "AsyncMongoDBClient",
    "mongo_client",
    "async_mongo_client",
    "get_db_client",
    "get_async_db_client",
]