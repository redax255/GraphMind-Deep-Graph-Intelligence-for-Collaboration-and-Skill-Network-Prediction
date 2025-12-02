# config.py
"""
Configuration centrale de l'application GraphMind.

Ce module gère :
- Chargement des variables d'environnement (.env)
- Configuration MongoDB
- Configuration Neo4j
- Chemins des fichiers et dossiers
- Paramètres Machine Learning
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """
    Configuration de l'application.
    
    Les valeurs sont chargées depuis le fichier .env
    """
    
    # ============================================
    # MONGODB CONFIGURATION
    # ============================================
    
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="URI de connexion MongoDB"
    )
    
    mongodb_db_name: str = Field(
        default="linkedin_scraper",
        description="Nom de la base de données"
    )
    
    mongodb_collection_profiles: str = Field(
        default="linkedin_profiles",
        description="Nom de la collection des profils bruts"
    )
    
    mongodb_collection_enriched: str = Field(
        default="linkedin_profiles_enriched",
        description="Nom de la collection des profils enrichis"
    )
    
    # ============================================
    # NEO4J CONFIGURATION
    # ============================================
    
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="URI de connexion Neo4j"
    )
    
    neo4j_user: str = Field(
        default="neo4j",
        description="Nom d'utilisateur Neo4j"
    )
    
    neo4j_password: str = Field(
        default="Redax@255",
        description="Mot de passe Neo4j"
    )
    
    # ============================================
    # APPLICATION CONFIGURATION
    # ============================================
    
    environment: str = Field(
        default="development",
        description="Environnement (development/production)"
    )
    
    app_host: str = Field(
        default="0.0.0.0",
        description="Hôte de l'application FastAPI"
    )
    
    app_port: int = Field(
        default=8000,
        description="Port de l'application FastAPI"
    )
    
    # ============================================
    # MACHINE LEARNING CONFIGURATION
    # ============================================
    
    embedding_dim: int = Field(
        default=128,
        description="Dimension des embeddings (node2vec, GraphSAGE)"
    )
    
    node2vec_num_walks: int = Field(
        default=10,
        description="Nombre de random walks par nœud"
    )
    
    node2vec_walk_length: int = Field(
        default=80,
        description="Longueur de chaque random walk"
    )
    
    node2vec_p: float = Field(
        default=1.0,
        description="Paramètre p de node2vec (return parameter)"
    )
    
    node2vec_q: float = Field(
        default=1.0,
        description="Paramètre q de node2vec (in-out parameter)"
    )
    
    # ============================================
    # SENTENCE-BERT CONFIGURATION
    # ============================================
    
    sentence_bert_model: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2",
        description="Modèle Sentence-BERT pour embeddings"
    )
    
    embedding_dimension: int = Field(
        default=384,
        description="Dimension des embeddings Sentence-BERT"
    )
    
    # ============================================
    # DBSCAN CONFIGURATION
    # ============================================
    
    dbscan_eps: float = Field(
        default=0.03,
        description="DBSCAN eps (similarité 97%+)"
    )
    
    dbscan_min_samples: int = Field(
        default=2,
        description="DBSCAN min_samples"
    )
    
    cluster_coherence_threshold: float = Field(
        default=0.90,
        description="Seuil de cohérence des clusters"
    )
    
    cluster_min_similarity: float = Field(
        default=0.75,
        description="Similarité minimale dans un cluster"
    )
    
    # ============================================
    # FILE PATHS
    # ============================================
    
    data_dir: Path = Field(
        default=Path("./data"),
        description="Dossier racine des données"
    )
    
    models_dir: Path = Field(
        default=Path("./data/models"),
        description="Dossier des modèles ML"
    )
    
    processed_data_dir: Path = Field(
        default=Path("./data/processed"),
        description="Dossier des données traitées"
    )
    
    cache_dir: Path = Field(
        default=Path("./data/cache"),
        description="Dossier du cache"
    )
    
    reports_dir: Path = Field(
        default=Path("./data/reports"),
        description="Dossier des rapports"
    )
    
    # ============================================
    # PYDANTIC SETTINGS CONFIG
    # ============================================
    
    class Config:
        """Configuration Pydantic"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    # ============================================
    # PROPERTIES & HELPERS
    # ============================================
    
    @property
    def graph_path(self) -> Path:
        """Chemin du fichier graphe NetworkX sauvegardé"""
        return self.processed_data_dir / "graph.pkl"
    
    @property
    def embeddings_path(self) -> Path:
        """Chemin du fichier embeddings node2vec"""
        return self.models_dir / "node2vec_embeddings.pkl"
    
    @property
    def link_predictor_path(self) -> Path:
        """Chemin du modèle de link prediction"""
        return self.models_dir / "link_predictor.pkl"
    
    @property
    def cleaned_profiles_path(self) -> Path:
        """Chemin du fichier JSON des profils nettoyés"""
        return self.processed_data_dir / "profiles_cleaned.json"
    
    @property
    def company_embeddings_cache(self) -> Path:
        """Chemin du cache des embeddings entreprises"""
        return self.cache_dir / "company_embeddings.pkl"
    
    @property
    def company_normalizations_cache(self) -> Path:
        """Chemin du cache des normalisations entreprises"""
        return self.cache_dir / "company_normalizations.json"
    
    @property
    def school_embeddings_cache(self) -> Path:
        """Chemin du cache des embeddings écoles"""
        return self.cache_dir / "school_embeddings.pkl"
    
    @property
    def school_normalizations_cache(self) -> Path:
        """Chemin du cache des normalisations écoles"""
        return self.cache_dir / "school_normalizations.json"
    
    def create_directories(self) -> None:
        """
        Crée tous les dossiers nécessaires s'ils n'existent pas.
        
        À appeler au démarrage de l'application.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def is_production(self) -> bool:
        """Vérifie si on est en environnement de production"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Vérifie si on est en environnement de développement"""
        return self.environment.lower() == "development"


# ============================================
# INSTANCE GLOBALE
# ============================================

# Instance unique de la configuration (singleton)
settings = Settings()

# Créer les dossiers au chargement du module
settings.create_directories()


# ============================================
# EXPORT
# ============================================

__all__ = ["settings", "Settings"]