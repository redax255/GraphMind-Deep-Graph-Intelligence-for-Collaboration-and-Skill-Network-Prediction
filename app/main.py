"""
Point d'entrée principal de l'application FastAPI.

Application Graph ML pour l'écosystème tech marocain.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.services.database import async_mongo_client
from app.api.routes import router

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# LIFESPAN - GESTION DU CYCLE DE VIE
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    
    Exécuté au démarrage et à l'arrêt de l'application.
    """
    # STARTUP
    logger.info("🚀 Démarrage de l'application Graph ML Morocco")
    logger.info(f"📊 Environnement: {settings.environment}")
    logger.info(f"🔗 MongoDB: {settings.mongodb_uri}")
    
    # Connexion à MongoDB
    try:
        await async_mongo_client.connect()
        logger.info("✅ Connexion MongoDB établie")
    except Exception as e:
        logger.error(f"❌ Erreur connexion MongoDB: {e}")
    
    yield
    
    # SHUTDOWN
    logger.info("🛑 Arrêt de l'application")
    await async_mongo_client.disconnect()
    logger.info("✅ Application arrêtée proprement")


# ============================================
# APPLICATION FASTAPI
# ============================================

app = FastAPI(
    title="Graph ML Morocco API",
    description="""
    # 🇲🇦 API Graph Machine Learning - Écosystème Tech Marocain
    
    Cette API permet de :
    - 📊 Analyser les profils professionnels tech au Maroc
    - 🔗 Explorer le graphe de connaissances (profils, entreprises, compétences)
    - 🎯 Prédire les collaborations futures entre professionnels
    - 💡 Obtenir des recommandations de connexions personnalisées
    
    ## Technologies
    - **Graph ML**: node2vec, GraphSAGE, PyTorch Geometric
    - **Link Prediction**: XGBoost
    - **Database**: MongoDB
    - **Framework**: FastAPI
    
    ## Données
    - ~67+ profils professionnels
    - Focus sur l'écosystème tech marocain (Rabat, Casablanca, etc.)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ============================================
# MIDDLEWARE CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development() else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# ROUTES
# ============================================

# Inclure les routes de l'API
app.include_router(router, prefix="/api/v1", tags=["API v1"])


# ============================================
# ROUTE RACINE
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """
    Page d'accueil de l'API.
    
    Returns:
        Message de bienvenue et informations de base
    """
    return {
        "message": "🇲🇦 Graph ML Morocco API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "docs": "/docs",
        "description": "API d'analyse du réseau professionnel tech marocain"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Vérification de l'état de l'application.
    
    Returns:
        État de santé de l'API et de MongoDB
    """
    # Vérifier la connexion MongoDB
    mongo_status = "connected"
    try:
        count = await async_mongo_client.get_profile_count()
        mongo_status = f"connected ({count} profils)"
    except Exception as e:
        mongo_status = f"error: {str(e)}"
        logger.error(f"❌ Health check MongoDB failed: {e}")
    
    return {
        "status": "healthy",
        "mongodb": mongo_status,
        "environment": settings.environment
    }


# ============================================
# GESTION DES ERREURS
# ============================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Gestion des erreurs 404"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Route non trouvée",
            "details": f"La route {request.url.path} n'existe pas"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Gestion des erreurs 500"""
    logger.error(f"Erreur interne: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Erreur interne du serveur",
            "details": str(exc) if settings.is_development() else None
        }
    )


# ============================================
# POINT D'ENTRÉE (si lancé directement)
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development(),
        log_level="info"
    )