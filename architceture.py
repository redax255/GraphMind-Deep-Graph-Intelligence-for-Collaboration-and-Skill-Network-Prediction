import os

# Nom du dossier racine du projet
base_dir = "."

# Liste complète des chemins à créer
structure = [
    # --- App ---
    "app/__init__.py",
    "app/main.py",
    "app/config.py",

    # --- API ---
    "app/api/__init__.py",
    "app/api/routes.py",

    # --- Models ---
    "app/models/__init__.py",
    "app/models/schemas.py",

    # --- Services ---
    "app/services/__init__.py",
    "app/services/database.py",
    "app/services/graph_service.py",
    "app/services/ml_service.py",
    "app/services/prediction_service.py",

    # --- Utils ---
    "app/utils/__init__.py",
    "app/utils/text_processing.py",

    # --- Data ---
    "data/processed/.gitkeep",
    "data/models/.gitkeep",

    # --- Scripts ---
    "scripts/train_graph.py",
    "scripts/train_ml.py",

    # --- Root files ---
    ".env",
    ".gitignore",
    "requirements.txt"
]

# Création des dossiers et fichiers
for path in structure:
    file_path = os.path.join(base_dir, path)
    dir_path = os.path.dirname(file_path)
    os.makedirs(dir_path, exist_ok=True)

    # Crée le fichier s’il n’existe pas encore
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            # Contenu minimal selon le type de fichier
            if file_path.endswith(".py"):
                f.write(f"# {os.path.basename(file_path)}\n")
            elif file_path.endswith(".env"):
                f.write("# Environment variables\nMONGO_URI=\n")
            elif file_path.endswith(".gitignore"):
                f.write("__pycache__/\n.env\n*.pyc\n/data/\n")
            elif file_path.endswith("requirements.txt"):
                f.write("fastapi\nuvicorn\npymongo\nnetworkx\nscikit-learn\npandas\nnumpy\n")
            elif file_path.endswith("README.md"):
                f.write("# Graph-ML-Morocco\n\nGraph Machine Learning API for collaboration and skill analysis.\n")
            else:
                f.write("")

print(f"✅ Structure complète créée sous: {os.path.abspath(base_dir)}")
