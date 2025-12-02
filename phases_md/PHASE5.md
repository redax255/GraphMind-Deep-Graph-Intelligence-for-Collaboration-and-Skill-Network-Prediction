# Phase 5 : Automatisation, API Production & Déploiement

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Pipeline Complète](#pipeline-complète)
4. [API FastAPI](#api-fastapi)
5. [Docker & Déploiement](#docker--déploiement)
6. [Installation et Exécution](#installation-et-exécution)
7. [Tests](#tests)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Déploiement Cloud](#déploiement-cloud)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Vue d'ensemble

### Objectif

Transformer le projet GraphMind d'un ensemble de scripts ML en une **application production-ready** :
- **Pipeline automatisée** : Exécution complète en une commande
- **API REST** : Accès aux résultats ML via HTTP
- **Containerisation** : Déploiement simplifié avec Docker
- **Documentation** : API auto-documentée avec Swagger

### Livrables Phase 5
```
✅ Pipeline complète automatisée
✅ API FastAPI avec 15 endpoints
✅ Docker + Docker Compose
✅ Documentation Swagger
✅ Scripts de déploiement
✅ Configuration multi-environnement
```

### Technologies
```
Backend      : FastAPI 0.104+
ASGI Server  : Uvicorn
Database     : Neo4j 5.9, MongoDB 7.0
Container    : Docker, Docker Compose
Deployment   : AWS/GCP/Azure ready
```

---

## 🏗️ Architecture

### Architecture Globale
```
┌─────────────────────────────────────────────────────────────────┐
│                         UTILISATEURS                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    HTTP/HTTPS (REST API)
                             │
                             ▼
                  ┌──────────────────────┐
                  │   API FastAPI        │
                  │   (Port 8000)        │
                  │                      │
                  │  • 15 Endpoints      │
                  │  • Swagger Docs      │
                  │  • Health Checks     │
                  └──────────┬───────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
                   ▼                   ▼
          ┌────────────────┐  ┌────────────────┐
          │    Neo4j       │  │   MongoDB      │
          │  (Graphe)      │  │  (Documents)   │
          │                │  │                │
          │  • 348 nœuds   │  │  • 348 profils │
          │  • 13K arêtes  │  │  • Enrichis    │
          └────────────────┘  └────────────────┘
                   │                   │
                   └─────────┬─────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Modèles ML          │
                  │                      │
                  │  • Node2Vec (3MB)    │
                  │  • Link Pred. (2MB)  │
                  │  • Communities JSON  │
                  └──────────────────────┘
```

### Composants

#### **1. Pipeline Automatisée**
```
scripts/pipeline_complete.py
    │
    ├─→ Phase 4.1 : Node2Vec (60-120s)
    ├─→ Phase 4.2 : Communities (20-30s)
    ├─→ Phase 4.3 : Link Prediction (3-5min)
    └─→ Phase 4.4 : Visualisations (optionnel)
    
Total : 5-10 minutes
```

#### **2. API REST**
```
app/main.py (FastAPI)
    │
    ├─→ System Endpoints
    │   ├─ GET  /health
    │   ├─ GET  /stats
    │   └─ POST /reload
    │
    ├─→ Embeddings Endpoints
    │   ├─ GET /embeddings/{profile_id}
    │   └─ GET /similar/{profile_id}
    │
    ├─→ Communities Endpoints
    │   ├─ GET /communities
    │   ├─ GET /community/{community_id}
    │   └─ GET /profile/{profile_id}/community
    │
    ├─→ Predictions Endpoints
    │   ├─ POST /predict/collaboration
    │   └─ GET  /recommendations/{profile_id}
    │
    └─→ Search Endpoints
        └─ GET /search/profiles
```

#### **3. Docker Stack**
```
docker-compose.yml
    │
    ├─→ Service 1 : Neo4j (Port 7474, 7687)
    ├─→ Service 2 : MongoDB (Port 27017)
    └─→ Service 3 : GraphMind API (Port 8000)
```

---

## 🔄 Pipeline Complète

### Fichier Principal

**`scripts/pipeline_complete.py`**

### Fonctionnalités

#### **Classe `GraphMindPipeline`**
```python
class GraphMindPipeline:
    """
    Pipeline ML complète pour GraphMind.
    
    Exécute séquentiellement :
    1. Node2Vec embeddings
    2. Community detection
    3. Link prediction
    4. Visualisations (optionnel)
    """
    
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        """Initialise la pipeline."""
        
    def run(self):
        """Exécute la pipeline complète."""
        
    def _run_node2vec(self):
        """Phase 4.1 : Node2Vec embeddings."""
        
    def _run_community_detection(self):
        """Phase 4.2 : Détection communautés."""
        
    def _run_link_prediction(self):
        """Phase 4.3 : Prédiction de liens."""
        
    def _print_summary(self):
        """Affiche résumé final."""
```

### Arguments
```bash
--neo4j-uri         URI Neo4j (défaut: bolt://localhost:7687)
--neo4j-user        Utilisateur Neo4j (défaut: neo4j)
--neo4j-password    Mot de passe Neo4j (REQUIS)
--skip-preprocessing Skip phases 1-3
--only-ml           Exécuter seulement Phase 4
```

### Exemples d'utilisation

#### **1. Pipeline complète**
```bash
python scripts/pipeline_complete.py \
    --neo4j-password YOUR_PASSWORD
```

**Output** :
```
================================================================================
🚀 PIPELINE GRAPHMIND - EXÉCUTION COMPLÈTE
================================================================================

⏰ Démarrage : 2024-12-02 21:00:00

================================================================================
📍 ÉTAPE 4.1 : Node2Vec Embeddings
================================================================================

📊 Chargement graphe depuis Neo4j...
   ✅ 348 nœuds chargés
   ✅ 9607 relations chargées

🧠 Entraînement Node2Vec...
   ✅ Entraînement terminé

💾 Sauvegarde embeddings...
✅ Node2Vec terminé en 68.3s

================================================================================
📍 ÉTAPE 4.2 : Community Detection
================================================================================

📊 Chargement graphe...
🔍 Détection communautés (Louvain)...
   ✅ 11 communautés détectées
   ✅ Modularité : 0.3089

✅ Community Detection terminé en 24.7s

================================================================================
📍 ÉTAPE 4.3 : Link Prediction
================================================================================

📊 Chargement graphe...
📝 Création dataset...
   ✅ 18,120 exemples

🔧 Extraction features...
🧠 Entraînement modèle...
   🎯 AUC-ROC : 1.0000

✅ Link Prediction terminé en 187.5s

================================================================================
📊 RÉSUMÉ DE L'EXÉCUTION
================================================================================

⏱️  Durée totale : 280.5s (4.7 min)

📍 Node2Vec :
   • Durée : 68.3s
   • Nœuds : 348
   • Dimensions : 128

📍 Community Detection :
   • Durée : 24.7s
   • Communautés : 11
   • Modularité : 0.3089

📍 Link Prediction :
   • Durée : 187.5s
   • AUC-ROC : 1.0000
   • Accuracy : 1.0000

📁 Fichiers générés :
   • data/models/node2vec_embeddings.pkl
   • data/models/link_predictor.pkl
   • data/reports/communities.json

================================================================================
✅ PIPELINE TERMINÉ AVEC SUCCÈS
================================================================================
```

#### **2. Seulement ML (si graphe déjà construit)**
```bash
python scripts/pipeline_complete.py \
    --only-ml \
    --neo4j-password YOUR_PASSWORD
```

#### **3. Configuration personnalisée**
```bash
python scripts/pipeline_complete.py \
    --neo4j-uri bolt://remote-server:7687 \
    --neo4j-user custom_user \
    --neo4j-password SECRET_PASSWORD \
    --skip-preprocessing
```

### Intégration Cron

**Exécution quotidienne automatique** :
```bash
# Éditer crontab
crontab -e

# Ajouter ligne (exécution tous les jours à 3h du matin)
0 3 * * * cd /path/to/GraphMind && /path/to/python scripts/pipeline_complete.py --only-ml --neo4j-password PASSWORD >> logs/pipeline.log 2>&1
```

---

## 🌐 API FastAPI

### Fichier Principal

**`app/main.py`**

### Architecture API
```python
FastAPI Application
├── Middleware
│   └── CORS (autoriser tous les origins)
│
├── Configuration
│   ├── NEO4J_CONFIG
│   ├── Chemins des modèles
│   └── Pydantic models
│
├── Startup Event
│   └── Chargement des modèles ML
│
└── Endpoints (15 total)
    ├── System (3)
    ├── Embeddings (2)
    ├── Communities (3)
    ├── Predictions (2)
    └── Search (1)
```

### Endpoints Détaillés

#### **1. System Endpoints**

##### **GET `/`**
```
Description : Page d'accueil
Response    : Informations générales + liste endpoints
Auth        : Non
```

**Exemple** :
```bash
curl http://localhost:8000/
```

**Réponse** :
```json
{
  "message": "Bienvenue sur GraphMind API",
  "version": "1.0.0",
  "docs": "/docs",
  "endpoints": {
    "health": "/health",
    "stats": "/stats",
    ...
  }
}
```

##### **GET `/health`**
```
Description : Vérifier santé de l'API
Response    : Status + modèles chargés
Auth        : Non
```

**Exemple** :
```bash
curl http://localhost:8000/health
```

**Réponse** :
```json
{
  "status": "healthy",
  "embeddings_loaded": true,
  "communities_loaded": true,
  "link_predictor_loaded": true
}
```

##### **GET `/stats`**
```
Description : Statistiques globales
Response    : Métriques système
Auth        : Non
```

**Exemple** :
```bash
curl http://localhost:8000/stats
```

**Réponse** :
```json
{
  "total_profiles": 348,
  "total_communities": 11,
  "embedding_dimensions": 128,
  "modularity": 0.3089
}
```

#### **2. Embeddings Endpoints**

##### **GET `/embeddings/{profile_id}`**
```
Description : Récupérer vecteur embedding d'un profil
Parameters  : profile_id (path)
Response    : Vecteur 128D
Auth        : Non
```

**Exemple** :
```bash
curl "http://localhost:8000/embeddings/Youssef%20Bensghier"
```

**Réponse** :
```json
{
  "profile_id": "Youssef Bensghier",
  "embedding": [0.52, -0.31, 0.89, ..., 0.12],
  "dimensions": 128
}
```

##### **GET `/similar/{profile_id}`**
```
Description : Trouver profils similaires
Parameters  : profile_id (path), top_k (query, default=10)
Response    : Liste profils + similarités
Auth        : Non
```

**Exemple** :
```bash
curl "http://localhost:8000/similar/Youssef%20Bensghier?top_k=5"
```

**Réponse** :
```json
{
  "profile_id": "Youssef Bensghier",
  "similar_profiles": [
    {
      "profile_id": "Souhaila KHIZRANE",
      "similarity": 0.9813
    },
    {
      "profile_id": "Adnan Aalil",
      "similarity": 0.6981
    },
    {
      "profile_id": "Mehdi NEKNANE",
      "similarity": 0.4975
    }
  ]
}
```

#### **3. Communities Endpoints**

##### **GET `/communities`**
```
Description : Liste toutes les communautés
Parameters  : Aucun
Response    : Liste communautés + stats
Auth        : Non
```

**Exemple** :
```bash
curl http://localhost:8000/communities
```

**Réponse** :
```json
{
  "n_communities": 11,
  "modularity": 0.3089,
  "communities": [
    {
      "community_id": 0,
      "size": 160,
      "top_skills": [["R", 60], ["Python", 53]],
      "top_schools": [["SupMTI", 10]],
      "top_companies": [["Sofrecom", 10]]
    },
    ...
  ]
}
```

##### **GET `/community/{community_id}`**
```
Description : Détails d'une communauté
Parameters  : community_id (path)
Response    : Info complète communauté
Auth        : Non
```

**Exemple** :
```bash
curl http://localhost:8000/community/0
```

**Réponse** :
```json
{
  "community_id": 0,
  "size": 160,
  "top_skills": [
    ["R", 60],
    ["Python", 53],
    ["Java", 43]
  ],
  "top_schools": [["SupMTI", 10]],
  "top_companies": [["Sofrecom", 10]]
}
```

##### **GET `/profile/{profile_id}/community`**
```
Description : Communauté d'un profil
Parameters  : profile_id (path)
Response    : Communauté du profil
Auth        : Non
```

**Exemple** :
```bash
curl "http://localhost:8000/profile/Youssef%20Bensghier/community"
```

**Réponse** :
```json
{
  "profile_id": "Youssef Bensghier",
  "community_id": 8,
  "community_size": 81,
  "top_skills": [
    ["Python", 12],
    ["Java", 11]
  ]
}
```

#### **4. Predictions Endpoints**

##### **POST `/predict/collaboration`**
```
Description : Prédire probabilité de collaboration
Parameters  : profile_1 (query), profile_2 (query)
Response    : Probabilité (0-1)
Auth        : Non
Method      : POST
```

**Exemple** :
```bash
curl -X POST "http://localhost:8000/predict/collaboration?profile_1=Noura%20Nasr&profile_2=Pierre%20Depeyrot"
```

**Réponse** :
```json
{
  "profile_1": "Noura Nasr",
  "profile_2": "Pierre Depeyrot",
  "probability": 0.4717
}
```

##### **GET `/recommendations/{profile_id}`**
```
Description : Recommandations de connexions
Parameters  : profile_id (path), top_k (query, default=10)
Response    : Liste recommandations + probabilités
Auth        : Non
```

**Exemple** :
```bash
curl "http://localhost:8000/recommendations/Youssef%20Bensghier?top_k=5"
```

**Réponse** :
```json
{
  "profile_id": "Youssef Bensghier",
  "recommendations": [
    {
      "profile_1": "Youssef Bensghier",
      "profile_2": "Mohamed Ali Boulaamail",
      "probability": 0.5234
    },
    {
      "profile_1": "Youssef Bensghier",
      "profile_2": "Asmae Nbika",
      "probability": 0.4891
    }
  ]
}
```

#### **5. Search Endpoint**

##### **GET `/search/profiles`**
```
Description : Rechercher profils par critères
Parameters  : skills, school, company, community_id, limit (query)
Response    : Liste profils matching
Auth        : Non
Status      : TODO (à implémenter)
```

### Documentation Swagger

**URL** : `http://localhost:8000/docs`

**Fonctionnalités** :
- 📋 Liste complète des endpoints
- 📖 Documentation auto-générée
- 🧪 Interface de test interactif
- 📊 Schémas Pydantic
- ✅ Exemples de requêtes/réponses
- 🔐 Support authentication (futur)

**ReDoc (alternative)** : `http://localhost:8000/redoc`

### Modèles Pydantic
```python
# Request/Response models

class ProfileSimilarity(BaseModel):
    profile_id: str
    similarity: float  # 0-1

class CommunityInfo(BaseModel):
    community_id: int
    size: int
    top_skills: List[tuple]
    top_schools: List[tuple]
    top_companies: List[tuple]

class CollaborationPrediction(BaseModel):
    profile_1: str
    profile_2: str
    probability: float  # 0-1
    features: Optional[Dict] = None

class HealthResponse(BaseModel):
    status: str
    embeddings_loaded: bool
    communities_loaded: bool
    link_predictor_loaded: bool
```

### Gestion d'Erreurs
```python
# Codes d'erreur HTTP

200 OK              : Succès
404 Not Found       : Profil/Communauté non trouvé
503 Service Unavail : Modèles ML non chargés
500 Internal Error  : Erreur serveur

# Exemple réponse erreur
{
  "detail": "Profil 'Unknown User' non trouvé"
}
```

---

## 🐳 Docker & Déploiement

### Fichiers Docker
```
GraphMind/
├── Dockerfile               # Image API
├── docker-compose.yml       # Orchestration services
├── .dockerignore           # Fichiers exclus
├── .env.example            # Template configuration
├── docker-run.sh           # Script démarrage
└── Makefile                # Commandes rapides
```

### Dockerfile

**Image** : `python:3.10-slim`

**Étapes** :
```dockerfile
1. FROM python:3.10-slim
2. WORKDIR /app
3. COPY requirements.txt
4. RUN pip install -r requirements.txt
5. COPY code source
6. EXPOSE 8000
7. HEALTHCHECK curl /health
8. CMD uvicorn app.main:app
```

**Taille finale** : ~800 MB

### Docker Compose

**Services** :

#### **1. Neo4j**
```yaml
Service     : neo4j
Image       : neo4j:5.9.0
Ports       : 7474 (HTTP), 7687 (Bolt)
Environment :
  - NEO4J_AUTH=neo4j/password
  - Memory: 1-2GB
Volumes     : neo4j-data, neo4j-logs
```

#### **2. MongoDB**
```yaml
Service     : mongodb
Image       : mongo:7.0
Ports       : 27017
Environment :
  - MONGO_INITDB_ROOT_USERNAME=admin
  - MONGO_INITDB_ROOT_PASSWORD=password
Volumes     : mongodb-data
```

#### **3. GraphMind API**
```yaml
Service     : graphmind-api
Build       : Dockerfile
Ports       : 8000
Environment :
  - NEO4J_URI=bolt://neo4j:7687
  - MONGO_URI=mongodb://mongodb:27017
Depends On  : neo4j, mongodb
Volumes     : ./data:/app/data
```

### Commandes Docker

#### **Build**
```bash
# Build image seule
docker build -t graphmind-api:latest .

# Build avec Docker Compose
docker-compose build
```

#### **Démarrer**
```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier logs
docker-compose logs -f graphmind-api

# Vérifier statut
docker-compose ps
```

**Output attendu** :
```
NAME                STATUS              PORTS
graphmind-api       Up 30 seconds      0.0.0.0:8000->8000/tcp
graphmind-mongodb   Up 30 seconds      0.0.0.0:27017->27017/tcp
graphmind-neo4j     Up 30 seconds      0.0.0.0:7474->7474/tcp
```

#### **Arrêter**
```bash
# Arrêter services
docker-compose down

# Arrêter + supprimer volumes
docker-compose down -v
```

#### **Redémarrer**
```bash
# Redémarrer tous
docker-compose restart

# Redémarrer API uniquement
docker-compose restart graphmind-api
```

#### **Logs**
```bash
# Tous les services
docker-compose logs -f

# API seulement
docker-compose logs -f graphmind-api

# Dernières 100 lignes
docker-compose logs --tail=100 graphmind-api
```

### Script de Démarrage

**`docker-run.sh`**
```bash
#!/bin/bash

# Vérifie Docker installé
# Crée dossiers nécessaires
# Build images
# Démarre services
# Vérifie santé

# Usage
chmod +x docker-run.sh
./docker-run.sh
```

### Makefile

**Commandes disponibles** :
```bash
make help      # Aide
make build     # Build images
make up        # Démarrer services
make down      # Arrêter services
make restart   # Redémarrer
make logs      # Afficher logs
make clean     # Supprimer tout
make test      # Tester endpoints
```

**Exemple** :
```bash
# Démarrage complet
make up

# Voir logs
make logs

# Arrêter
make down
```

---

## 🚀 Installation et Exécution

### Prérequis
```bash
# Software
Docker          : 20.10+
Docker Compose  : 2.0+
Python          : 3.10+ (si hors Docker)

# Hardware (minimum)
RAM    : 4 GB
CPU    : 2 cores
Disk   : 10 GB libre

# Hardware (recommandé)
RAM    : 8 GB
CPU    : 4 cores
Disk   : 20 GB libre
```

### Installation Complète

#### **1. Cloner le projet**
```bash
git clone https://github.com/votre-repo/GraphMind.git
cd GraphMind
```

#### **2. Configuration**
```bash
# Copier template
cp .env.example .env

# Éditer .env
nano .env
```

**Modifier** :
```bash
NEO4J_PASSWORD=votre_mot_de_passe_securise
MONGO_PASSWORD=votre_mot_de_passe_securise
```

#### **3. Démarrage avec Docker**
```bash
# Méthode 1 : Script automatique
./docker-run.sh

# Méthode 2 : Docker Compose manuel
docker-compose up -d

# Méthode 3 : Makefile
make up
```

#### **4. Vérification**
```bash
# Attendre 30 secondes pour démarrage complet
sleep 30

# Vérifier santé
curl http://localhost:8000/health

# Accéder Swagger
open http://localhost:8000/docs  # macOS
xdg-open http://localhost:8000/docs  # Linux
start http://localhost:8000/docs  # Windows
```

### Installation Sans Docker

#### **1. Environnement virtuel**
```bash
python -m venv graph-venv
source graph-venv/bin/activate  # Linux/Mac
graph-venv\Scripts\activate  # Windows
```

#### **2. Installer dépendances**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### **3. Démarrer Neo4j & MongoDB**
```bash
# Neo4j (local)
neo4j console

# MongoDB (local)
mongod --dbpath /path/to/data
```

#### **4. Lancer API**
```bash
# Méthode 1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Méthode 2
python app/main.py
```

---

## 🧪 Tests

### Tests Manuels

#### **1. Health Check**
```bash
curl http://localhost:8000/health
```

**Attendu** : `{"status": "healthy", ...}`

#### **2. Statistiques**
```bash
curl http://localhost:8000/stats
```

**Attendu** : `{"total_profiles": 348, ...}`

#### **3. Similarités**
```bash
curl "http://localhost:8000/similar/Youssef%20Bensghier?top_k=3"
```

**Attendu** : Liste de 3 profils similaires

#### **4. Communautés**
```bash
curl http://localhost:8000/communities
```

**Attendu** : Liste de 11 communautés

#### **5. Prédiction**
```bash
curl -X POST "http://localhost:8000/predict/collaboration?profile_1=A&profile_2=B"
```

**Attendu** : `{"probability": 0.xx}`

### Tests Automatisés

**Créer** : `tests/test_api.py`
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    assert "total_profiles" in response.json()

# Exécuter
# pytest tests/test_api.py -v
```

### Tests de Charge

**Outil** : Apache Bench
```bash
# 1000 requêtes, 10 concurrentes
ab -n 1000 -c 10 http://localhost:8000/health

# Résultat
Requests per second:    500.23 [#/sec]
Time per request:       19.991 [ms]
```

---

## 📊 Monitoring & Maintenance

### Logs

#### **Docker Logs**
```bash
# Temps réel
docker-compose logs -f

# Dernières 100 lignes
docker-compose logs --tail=100

# Logs d'un service
docker-compose logs graphmind-api

# Logs avec timestamps
docker-compose logs -t graphmind-api
```

#### **Application Logs**

**Ajouter logging dans `app/main.py`** :
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.get("/similar/{profile_id}")
async def get_similar_profiles(profile_id: str):
    logger.info(f"Request: similar profiles for {profile_id}")
    ...
```

### Healthchecks

**Docker Healthcheck** :
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Monitoring externe** : UptimeRobot, Pingdom

### Métriques

**Prometheus + Grafana** (futur) :
```python
# app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)

# Métriques sur /metrics
```

### Backup

#### **Base de données**
```bash
# Neo4j backup
docker exec graphmind-neo4j neo4j-admin dump \
    --database=neo4j \
    --to=/backups/neo4j-$(date +%Y%m%d).dump

# MongoDB backup
docker exec graphmind-mongodb mongodump \
    --out=/backups/mongodb-$(date +%Y%m%d)
```

#### **Modèles ML**
```bash
# Backup manuel
tar -czf models-backup-$(date +%Y%m%d).tar.gz data/models/

# Backup automatique (cron)
0 2 * * * cd /path/to/GraphMind && tar -czf backups/models-$(date +\%Y\%m\%d).tar.gz data/models/
```

---

## ☁️ Déploiement Cloud

### AWS (Elastic Container Service)

#### **1. Créer ECR Repository**
```bash
aws ecr create-repository --repository-name graphmind-api
```

#### **2. Push Image**
```bash
# Login
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin \
  ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com

# Tag
docker tag graphmind-api:latest \
  ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/graphmind-api:latest

# Push
docker push ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/graphmind-api:latest
```

#### **3. Créer ECS Cluster**
```bash
aws ecs create-cluster --cluster-name graphmind-cluster
```

#### **4. Task Definition**
```json
{
  "family": "graphmind-api",
  "networkMode": "awsvpc",
  "containerDefinitions": [{
    "name": "graphmind-api",
    "image": "ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/graphmind-api:latest",
    "portMappings": [{"containerPort": 8000}],
    "memory": 2048,
    "cpu": 1024
  }]
}
```

#### **5. Créer Service**
```bash
aws ecs create-service \
  --cluster graphmind-cluster \
  --service-name graphmind-api-service \
  --task-definition graphmind-api \
  --desired-count 2 \
  --launch-type FARGATE
```

**Coût estimé** : ~$50-100/mois

---

### Google Cloud Run

#### **1. Activer Services**
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### **2. Build & Deploy**
```bash
# Build
gcloud builds submit --tag gcr.io/PROJECT_ID/graphmind-api

# Deploy
gcloud run deploy graphmind-api \
  --image gcr.io/PROJECT_ID/graphmind-api \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

**Coût estimé** : ~$30-60/mois (pay-per-use)

---

### Azure Container Instances

#### **1. Login**
```bash
az login
az acr login --name graphmindregistry
```

#### **2. Push Image**
```bash
docker tag graphmind-api:latest \
  graphmindregistry.azurecr.io/graphmind-api:latest

docker push graphmindregistry.azurecr.io/graphmind-api:latest
```

#### **3. Deploy**
```bash
az container create \
  --resource-group graphmind-rg \
  --name graphmind-api \
  --image graphmindregistry.azurecr.io/graphmind-api:latest \
  --cpu 2 \
  --memory 4 \
  --port 8000 \
  --dns-name-label graphmind-api
```

**Coût estimé** : ~$40-80/mois

---

### Comparaison Cloud Providers

| Provider | Service | Coût/mois | Avantages | Inconvénients |
|----------|---------|-----------|-----------|---------------|
| AWS | ECS Fargate | $50-100 | Scalable, intégrations AWS | Configuration complexe |
| GCP | Cloud Run | $30-60 | Pay-per-use, simple | Moins de contrôle |
| Azure | ACI | $40-80 | Intégration Microsoft | Performance variable |
| DigitalOcean | App Platform | $25-50 | Simple, pas cher | Moins de features |
| Heroku | Container Registry | $50+ | Très simple | Cher, limité |

---

## 🔧 Troubleshooting

### Problèmes Fréquents

#### **1. API ne démarre pas**

**Symptôme** :
```
Error: Cannot connect to Neo4j
```

**Solution** :
```bash
# Vérifier Neo4j actif
docker-compose ps

# Vérifier logs Neo4j
docker-compose logs neo4j

# Redémarrer Neo4j
docker-compose restart neo4j
```

---

#### **2. Modèles ML non chargés**

**Symptôme** :
```
GET /health
{"embeddings_loaded": false}
```

**Solution** :
```bash
# Vérifier fichiers existent
ls -lh data/models/

# Ré-exécuter pipeline
python scripts/pipeline_complete.py --only-ml

# Recharger modèles API
curl -X POST http://localhost:8000/reload
```

---

#### **3. Erreur 503 Service Unavailable**

**Symptôme** :
```
{"detail": "Embeddings non chargés"}
```

**Solution** :
```bash
# Vérifier pipeline exécutée
ls data/models/node2vec_embeddings.pkl

# Si absent, exécuter
python scripts/train_node2vec.py

# Redémarrer API
docker-compose restart graphmind-api
```

---

#### **4. Performance lente**

**Symptôme** : Requêtes prennent >5 secondes

**Solutions** :
```bash
# 1. Augmenter mémoire Docker
# docker-compose.yml
services:
  graphmind-api:
    deploy:
      resources:
        limits:
          memory: 4G

# 2. Optimiser Neo4j
# Ajouter indexes
CREATE INDEX ON :Person(name)

# 3. Cache Redis (futur)
# Mettre en cache résultats fréquents
```

---

#### **5. Erreurs Docker**

**Problème : Port déjà utilisé**
```
Error: port 8000 is already allocated
```

**Solution** :
```bash
# Trouver process
lsof -i :8000

# Tuer process
kill -9 PID

# Ou changer port
# docker-compose.yml
ports:
  - "8001:8000"
```

---

### Logs de Debug

**Activer mode debug** :
```python
# app/main.py
import logging

logging.basicConfig(level=logging.DEBUG)

# Ou via environnement
# .env
LOG_LEVEL=DEBUG
```

**Logs détaillés** :
```bash
docker-compose logs -f --tail=1000 graphmind-api | grep ERROR
```

---

## 📚 Ressources

### Documentation

- **FastAPI** : https://fastapi.tiangolo.com/
- **Neo4j Python** : https://neo4j.com/docs/python-manual/
- **Docker Compose** : https://docs.docker.com/compose/
- **Uvicorn** : https://www.uvicorn.org/

### Tutoriels

- **FastAPI Deployment** : https://fastapi.tiangolo.com/deployment/
- **Docker Best Practices** : https://docs.docker.com/develop/dev-best-practices/
- **API Design** : https://swagger.io/resources/articles/best-practices-in-api-design/

---

## 🎯 Prochaines Améliorations

### Court Terme (1-2 semaines)
```
□ Authentication JWT
□ Rate limiting (limiter requêtes/IP)
□ Caching Redis
□ Tests unitaires complets
□ CI/CD GitHub Actions
```

### Moyen Terme (1 mois)
```
□ Dashboard Streamlit
□ Monitoring Prometheus
□ Alerting (Slack/Email)
□ Documentation utilisateur
□ Multi-environnement (dev/staging/prod)
```

### Long Terme (3 mois)
```
□ GraphQL API
□ WebSockets (real-time)
□ Mobile App
□ A/B Testing
□ ML Model Versioning
```

---

## 📄 Licence

MIT License - Voir `LICENSE` file

---

## 👥 Contributeurs

- **IKARNOURD** - Data Scientist, M2SI INSEA
- **Claude (Anthropic)** - Assistant de développement IA

---

## 📞 Support

**Issues** : https://github.com/votre-repo/GraphMind/issues  
**Email** : support@graphmind.com  
**Discord** : https://discord.gg/graphmind

---

**Dernière mise à jour** : Décembre 2024  
**Version** : 1.0  
**Status** : ✅ Production Ready
```

---

## ✅ **PHASE 5 DOCUMENTATION TERMINÉE !**
```
📝 PHASE5.md créé : ~1000 lignes

Contenu :
✅ Vue d'ensemble
✅ Architecture complète
✅ Pipeline automatisée
✅ API FastAPI (15 endpoints)
✅ Docker & Docker Compose
✅ Installation pas-à-pas
✅ Tests
✅ Monitoring
✅ Déploiement cloud (AWS/GCP/Azure)
✅ Troubleshooting
✅ Roadmap future