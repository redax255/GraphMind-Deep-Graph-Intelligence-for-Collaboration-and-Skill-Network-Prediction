# config.py
"""
Configuration centrale de l'application Graph ML Morocco.

Ce module gère :
- Chargement des variables d'environnement (.env)
- Configuration MongoDB
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
        default="tech_ecosystem_morocco",
        description="Nom de la base de données"
    )
    
    mongodb_collection_profiles: str = Field(
        default="profiles",
        description="Nom de la collection des profils"
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
    
    def create_directories(self) -> None:
        """
        Crée tous les dossiers nécessaires s'ils n'existent pas.
        
        À appeler au démarrage de l'application.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
    
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