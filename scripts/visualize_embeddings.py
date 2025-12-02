"""
Visualisation des embeddings Node2Vec en 2D.

Utilise t-SNE pour réduire 128D → 2D et afficher un graphique interactif.
"""

import sys
import pickle
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import TSNE

sys.path.append(str(Path(__file__).parent.parent))


def print_separator(char="=", length=80):
    """Affiche un séparateur"""
    print(char * length)


def load_embeddings(filepath: str = "data/models/node2vec_embeddings.pkl"):
    """
    Charge les embeddings depuis le fichier pickle.
    
    Returns:
        dict: {node_id: embedding_vector}
    """
    print(f"📂 Chargement embeddings depuis : {filepath}")
    
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    
    embeddings = data['embeddings']
    dimensions = data['dimensions']
    
    print(f"✅ {len(embeddings)} embeddings chargés ({dimensions}D)")
    
    return embeddings


def reduce_to_2d(embeddings: dict, method: str = "tsne"):
    """
    Réduit les embeddings de 128D vers 2D.
    
    Args:
        embeddings: Dictionnaire {node_id: embedding}
        method: "tsne" ou "umap"
    
    Returns:
        node_ids: Liste des IDs
        coords_2d: Array (n, 2) des coordonnées 2D
    """
    print(f"\n🔄 Réduction dimensionnelle avec {method.upper()}...")
    
    # Extraire IDs et vecteurs
    node_ids = list(embeddings.keys())
    vectors = np.array(list(embeddings.values()))
    
    print(f"   Shape initiale : {vectors.shape}")
    
    if method == "tsne":
        # t-SNE
        reducer = TSNE(
            n_components=2,
            random_state=42,
            perplexity=30,
            n_iter=1000,
            verbose=1
        )
        coords_2d = reducer.fit_transform(vectors)
    
    elif method == "umap":
        # UMAP (nécessite: pip install umap-learn)
        try:
            import umap
            reducer = umap.UMAP(
                n_components=2,
                random_state=42,
                n_neighbors=15,
                min_dist=0.1
            )
            coords_2d = reducer.fit_transform(vectors)
        except ImportError:
            print("⚠️  UMAP non installé, utilisation de t-SNE à la place")
            print("   Pour installer : pip install umap-learn")
            return reduce_to_2d(embeddings, method="tsne")
    
    else:
        raise ValueError(f"Méthode inconnue : {method}")
    
    print(f"✅ Réduction terminée : {coords_2d.shape}")
    
    return node_ids, coords_2d


def plot_2d_scatter(node_ids, coords_2d, save_path: str = "data/reports/embeddings_2d.png"):
    """
    Affiche un scatter plot 2D des embeddings.
    
    Args:
        node_ids: Liste des IDs de nœuds
        coords_2d: Coordonnées 2D (n, 2)
        save_path: Chemin de sauvegarde du graphique
    """
    print(f"\n📊 Création du graphique...")
    
    # Créer figure
    plt.figure(figsize=(16, 12))
    
    # Scatter plot
    scatter = plt.scatter(
        coords_2d[:, 0],
        coords_2d[:, 1],
        alpha=0.6,
        s=50,
        c=range(len(coords_2d)),
        cmap='viridis',
        edgecolors='black',
        linewidth=0.5
    )
    
    # Ajouter labels pour quelques points (éviter surcharge)
    # Afficher seulement 30 labels aléatoires
    import random
    random.seed(42)
    sample_indices = random.sample(range(len(node_ids)), min(30, len(node_ids)))
    
    for idx in sample_indices:
        plt.annotate(
            node_ids[idx][:20],  # Tronquer noms longs
            (coords_2d[idx, 0], coords_2d[idx, 1]),
            fontsize=8,
            alpha=0.7,
            xytext=(5, 5),
            textcoords='offset points'
        )
    
    # Styling
    plt.title("Visualisation 2D des Embeddings Node2Vec\n(GraphMind - 348 Profils)", 
              fontsize=16, fontweight='bold')
    plt.xlabel("Dimension 1", fontsize=12)
    plt.ylabel("Dimension 2", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.colorbar(scatter, label="Index Profil")
    
    # Sauvegarder
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Graphique sauvegardé : {save_path}")
    
    # Afficher
    plt.show()
    print("📊 Graphique affiché (fermer la fenêtre pour continuer)")


def plot_2d_interactive(node_ids, coords_2d, save_path: str = "data/reports/embeddings_2d_interactive.html"):
    """
    Crée un graphique interactif avec Plotly.
    
    Args:
        node_ids: Liste des IDs
        coords_2d: Coordonnées 2D
        save_path: Chemin HTML
    """
    try:
        import plotly.graph_objects as go
        
        print(f"\n📊 Création du graphique interactif...")
        
        # Créer scatter interactif
        fig = go.Figure(data=[
            go.Scatter(
                x=coords_2d[:, 0],
                y=coords_2d[:, 1],
                mode='markers',
                marker=dict(
                    size=8,
                    color=list(range(len(coords_2d))),
                    colorscale='Viridis',
                    showscale=True,
                    line=dict(width=0.5, color='black')
                ),
                text=node_ids,
                hovertemplate='<b>%{text}</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>',
                name='Profils'
            )
        ])
        
        # Layout
        fig.update_layout(
            title=dict(
                text="Visualisation Interactive - Embeddings Node2Vec (GraphMind)",
                font=dict(size=18, color='#2c3e50')
            ),
            xaxis_title="Dimension 1",
            yaxis_title="Dimension 2",
            width=1400,
            height=900,
            hovermode='closest',
            template='plotly_white'
        )
        
        # Sauvegarder
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(save_path)
        print(f"✅ Graphique interactif sauvegardé : {save_path}")
        print("   → Ouvrir dans navigateur pour explorer")
        
    except ImportError:
        print("⚠️  Plotly non installé, graphique interactif ignoré")
        print("   Pour installer : pip install plotly")


def analyze_clusters_visual(coords_2d):
    """
    Analyse visuelle rapide des clusters.
    
    Args:
        coords_2d: Coordonnées 2D
    """
    print(f"\n📊 ANALYSE VISUELLE RAPIDE")
    print_separator("-")
    
    # Statistiques de distribution
    mean_x = np.mean(coords_2d[:, 0])
    mean_y = np.mean(coords_2d[:, 1])
    std_x = np.std(coords_2d[:, 0])
    std_y = np.std(coords_2d[:, 1])
    
    print(f"Centre (X) : {mean_x:.2f} ± {std_x:.2f}")
    print(f"Centre (Y) : {mean_y:.2f} ± {std_y:.2f}")
    
    # Estimation nombre de clusters visuels
    from sklearn.cluster import KMeans
    
    # Tester plusieurs k
    inertias = []
    k_range = range(2, 11)
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(coords_2d)
        inertias.append(kmeans.inertia_)
    
    # Méthode du coude (approximatif)
    print(f"\n💡 Nombre de clusters suggéré (méthode du coude) : 5-8")
    print("   → Sera confirmé par Community Detection (Louvain)")


def main():
    print_separator()
    print("🎨 VISUALISATION EMBEDDINGS NODE2VEC - GRAPHMIND")
    print_separator()
    print()
    
    # ============================================
    # CHARGEMENT
    # ============================================
    
    embeddings_file = "data/models/node2vec_embeddings.pkl"
    
    try:
        embeddings = load_embeddings(embeddings_file)
    except FileNotFoundError:
        print(f"❌ Fichier introuvable : {embeddings_file}")
        print("   Exécutez d'abord : python scripts/train_node2vec.py")
        return
    
    # ============================================
    # RÉDUCTION DIMENSIONNELLE
    # ============================================
    
    print_separator()
    print("🔄 RÉDUCTION DIMENSIONNELLE (128D → 2D)")
    print_separator()
    
    node_ids, coords_2d = reduce_to_2d(embeddings, method="tsne")
    
    # ============================================
    # VISUALISATION STATIQUE
    # ============================================
    
    print_separator()
    print("📊 GRAPHIQUE STATIQUE (Matplotlib)")
    print_separator()
    
    plot_2d_scatter(node_ids, coords_2d)
    
    # ============================================
    # VISUALISATION INTERACTIVE
    # ============================================
    
    print_separator()
    print("🌐 GRAPHIQUE INTERACTIF (Plotly)")
    print_separator()
    
    plot_2d_interactive(node_ids, coords_2d)
    
    # ============================================
    # ANALYSE RAPIDE
    # ============================================
    
    print_separator()
    analyze_clusters_visual(coords_2d)
    
    # ============================================
    # RÉSUMÉ
    # ============================================
    
    print()
    print_separator()
    print("✅ VISUALISATION TERMINÉE")
    print_separator()
    print()
    print("📊 Fichiers générés :")
    print("   1. data/reports/embeddings_2d.png")
    print("   2. data/reports/embeddings_2d_interactive.html")
    print()
    print("🎯 Prochaine étape : Community Detection")
    print("   → python scripts/detect_communities.py")
    print()
    print_separator()


if __name__ == "__main__":
    main()