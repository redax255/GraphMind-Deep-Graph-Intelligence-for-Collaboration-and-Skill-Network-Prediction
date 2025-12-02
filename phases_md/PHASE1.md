GraphMind-Deep-Graph-Intelligence-for-Collaboration-and-Skill-Network-Prediction

# 🇲🇦 Graph ML Morocco - Écosystème Tech Marocain

Système de Graph Machine Learning pour analyser le réseau professionnel tech au Maroc, prédire les collaborations futures et recommander des connexions pertinentes.

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-5.0+-green.svg)](https://www.mongodb.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1-red.svg)](https://pytorch.org/)

---

## 🎯 Objectifs

- 📊 Cartographier le réseau professionnel tech marocain
- 🔗 Construire un graphe de connaissances (profils, entreprises, compétences, écoles)
- 🤖 Prédire les collaborations futures avec Graph ML
- 💡 Recommander des connexions professionnelles pertinentes

---

## 📊 Données

- **67 profils** LinkedIn (Data Scientists, ML Engineers, Software Engineers)
- **100% resume** riche en compétences techniques
- **Focus géographique** : Rabat (58%), Casablanca, Kénitra
- **Technologies** : Python, SQL, TensorFlow, Docker, Spark, React, etc.

---

## 🏗️ Architecture

### Stack Technique

**Backend & API**
- FastAPI + Uvicorn (API REST asynchrone)
- Pydantic (validation données)
- Motor + PyMongo (MongoDB async/sync)

**Graph & Machine Learning**
- NetworkX (construction graphe)
- PyTorch Geometric (Graph Neural Networks)
- node2vec (embeddings)
- XGBoost (link prediction)

**Data Science**
- pandas, numpy (manipulation données)
- scikit-learn (ML classique)
- matplotlib, plotly, seaborn (visualisation)

### Structure du Projet

```
├── app/
│   ├── config.py              # Configuration centrale
│   ├── main.py                # FastAPI entry point
│   ├── api/routes.py          # Endpoints REST
│   ├── models/schemas.py      # Modèles Pydantic
│   ├── services/
│   │   ├── database.py        # MongoDB
│   │   ├── graph_service.py   # Graphe NetworkX
│   │   ├── ml_service.py      # Embeddings & ML
│   │   └── prediction_service.py
│   └── utils/
│       └── text_processing.py # Extraction compétences
├── data/
│   ├── processed/             # Données nettoyées
│   └── models/                # Modèles ML entraînés
├── scripts/
│   ├── train_graph.py         # Construction graphe
│   └── train_ml.py            # Entraînement modèles
└── .env                       # Configuration
```

---

## 🚀 Installation

### Prérequis

- Python 3.10+
- MongoDB 5.0+ (local ou Atlas)
- 8 GB RAM minimum

### Installation

```bash
# Cloner le projet
git clone https://github.com/votre-repo/graph-ml-morocco.git
cd graph-ml-morocco

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
.\venv\Scripts\Activate.ps1  # Windows

# Installer dépendances
pip install torch torchvision torchaudio
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.1.0+cpu.html
pip install -r requirements.txt

# Configurer .env
cp .env.example .env
# Éditer .env avec vos paramètres MongoDB
```

### Configuration `.env`

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=linkedin_profiles
MONGODB_COLLECTION_PROFILES=profiles
ENVIRONMENT=development
APP_PORT=8001
EMBEDDING_DIM=128
```

---

## 💻 Utilisation

### Lancer l'API

```bash
uvicorn app.main:app --reload --port 8001
```

**Accès** :
- API : http://localhost:8001
- Documentation : http://localhost:8001/docs
- Health Check : http://localhost:8001/health

### Tester la connexion MongoDB

```bash
python test_mongodb_connection.py
```

### Endpoints disponibles

```
GET  /                           Accueil
GET  /health                     Health check
GET  /docs                       Documentation Swagger

GET  /api/v1/profiles            Liste profils
GET  /api/v1/profiles/count      Nombre de profils
GET  /api/v1/profiles/search     Recherche profils

GET  /api/v1/graph/stats         Stats graphe
GET  /api/v1/status              État du projet

POST /api/v1/predict/recommend   Recommandations (Phase 5)
POST /api/v1/predict/collaboration Prédire collaboration (Phase 5)

GET  /api/v1/admin/data-quality  Qualité données
GET  /api/v1/admin/locations     Distribution géographique
```

---

## 📋 Roadmap

### ✅ Phase 1 - Exploration & Architecture (Semaine 1)
- [x] Setup infrastructure FastAPI + MongoDB
- [x] Exploration des 67 profils
- [x] API opérationnelle avec endpoints de base
- [x] Tests de connexion MongoDB

### ⏳ Phase 2 - Preprocessing (Semaines 2-3)
- [ ] Extraction compétences depuis resume et experience
- [ ] Normalisation dates françaises
- [ ] Détection entreprises et écoles
- [ ] Génération profiles_cleaned.json

### ⏳ Phase 3 - Construction Graphe (Semaine 4)
- [ ] Créer graphe NetworkX (profils, entreprises, compétences, écoles)
- [ ] Inférer collaborations (chevauchements temporels)
- [ ] Statistiques graphe (~2500 nœuds, ~8000 edges)

### ⏳ Phase 4 - Graph ML (Semaines 5-6)
- [ ] Entraîner node2vec (embeddings 128D)
- [ ] Visualisation t-SNE/UMAP des clusters
- [ ] Tester GraphSAGE (optionnel)

### ⏳ Phase 5 - Link Prediction (Semaine 7)
- [ ] Feature engineering (embeddings + features structurales)
- [ ] Entraîner XGBoost pour prédiction liens
- [ ] Objectif : AUC-ROC > 0.70

### ⏳ Phase 6 - Finalisation (Semaines 8-9)
- [ ] Compléter API avec recommandations
- [ ] Tests et optimisations
- [ ] Documentation finale

---

## 🎯 Métriques attendues

Avec 67 profils de qualité :

| Métrique | Estimation |
|----------|------------|
| Compétences extraites | 500-800 |
| Entreprises uniques | 150-200 |
| Écoles uniques | 50-80 |
| Nœuds (graphe) | 2500-3000 |
| Relations (edges) | 8000-10000 |
| AUC-ROC Link Prediction | 0.70-0.78 |
| Precision@10 | 0.60-0.70 |

---

## 📚 Documentation

- **PHASE1_BRIEF.md** - Documentation Phase 1 (terminée)
- **API Documentation** - http://localhost:8001/docs (Swagger interactif)
- **Roadmap complète** - Voir fichier roadmap initial du projet

---

## 🛠️ Développement

### Tests

```bash
# Test connexion MongoDB
python test_mongodb_connection.py

# Tester l'API
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/profiles/count
```

### Structure MongoDB

```json
{
  "linkedinUrl": "https://linkedin.com/in/...",
  "first_name": "Ahmed",
  "last_name": "Benali",
  "position": "Data Scientist @ OCP",
  "location": "Rabat, Maroc",
  "resume": "Expert Python, SQL, TensorFlow...",
  "experience": [
    {
      "position": "Data Scientist",
      "company": "OCP",
      "period": "janv. 2023 - aujourd'hui",
      "description": ["Python · SQL · Spark"]
    }
  ],
  "formation": [...],
  "skills": []  // Vide → à extraire en Phase 2
}
```

---

## 🤝 Contribution

Ce projet est un POC (Proof of Concept) pour l'analyse de l'écosystème tech marocain.

---

## 📄 Licence

MIT License

---

## 👤 Auteur

Votre Nom - [LinkedIn](https://linkedin.com/in/votre-profil)

---

## 🙏 Remerciements

- LinkedIn pour les données profils
- Communauté tech marocaine (ENSIAS, EMI, INPT, UM6P)
- Entreprises tech au Maroc (OCP, SQLI, Capgemini, etc.)

---

**Status** : Phase 1 ✅ | Phase 2-6 ⏳  
**Dernière mise à jour** : Octobre 2025