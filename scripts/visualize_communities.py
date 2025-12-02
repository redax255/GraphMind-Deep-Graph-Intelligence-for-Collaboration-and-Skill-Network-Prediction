"""
Visualisation des communautés détectées en 2D.

Affiche les profils colorés par communauté sur le graphe t-SNE.
"""

import sys
import json
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


def load_communities(filepath: str = "data/reports/communities.json"):
    """
    Charge les communautés depuis le fichier JSON.
    
    Returns:
        dict: Données des communautés
    """
    print(f"📂 Chargement communautés depuis : {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    n_communities = data['n_communities']
    assignments = data['assignments']
    community_data = data['communities']
    
    print(f"✅ {n_communities} communautés chargées")
    
    return assignments, community_data


def reduce_to_2d(embeddings: dict):
    """
    Réduit les embeddings de 128D vers 2D avec t-SNE.
    
    Args:
        embeddings: Dictionnaire {node_id: embedding}
    
    Returns:
        node_ids: Liste des IDs
        coords_2d: Array (n, 2) des coordonnées 2D
    """
    print(f"\n🔄 Réduction dimensionnelle avec t-SNE...")
    
    # Extraire IDs et vecteurs
    node_ids = list(embeddings.keys())
    vectors = np.array(list(embeddings.values()))
    
    print(f"   Shape initiale : {vectors.shape}")
    
    # t-SNE
    reducer = TSNE(
        n_components=2,
        random_state=42,
        perplexity=30,
        n_iter=1000,
        verbose=1
    )
    coords_2d = reducer.fit_transform(vectors)
    
    print(f"✅ Réduction terminée : {coords_2d.shape}")
    
    return node_ids, coords_2d


def plot_communities(
    node_ids,
    coords_2d,
    assignments,
    community_data,
    save_path: str = "data/reports/communities_2d.png"
):
    """
    Affiche un scatter plot 2D coloré par communauté.
    
    Args:
        node_ids: Liste des IDs de nœuds
        coords_2d: Coordonnées 2D (n, 2)
        assignments: Dict {node_id: community_id}
        community_data: Données des communautés
        save_path: Chemin de sauvegarde
    """
    print(f"\n📊 Création du graphique...")
    
    # Créer figure
    fig, ax = plt.subplots(figsize=(18, 14))
    
    # Extraire les community_ids pour chaque nœud (dans l'ordre)
    community_labels = []
    for node_id in node_ids:
        comm_id = assignments.get(node_id, -1)
        community_labels.append(comm_id)
    
    community_labels = np.array(community_labels)
    
    # Nombre de communautés
    n_communities = len(set(community_labels))
    
    # Palette de couleurs (une par communauté)
    # Filtrer les petites communautés (taille 1)
    large_communities = [
        int(comm_id) for comm_id, data in community_data.items() 
        if data['size'] > 1
    ]
    small_communities = [
        int(comm_id) for comm_id, data in community_data.items() 
        if data['size'] == 1
    ]
    
    # Couleurs distinctes pour grandes communautés
    colors_large = plt.cm.tab10(np.linspace(0, 1, len(large_communities)))
    colors_small = ['lightgray'] * len(small_communities)
    
    # Mapper communautés vers couleurs
    color_map = {}
    for i, comm_id in enumerate(large_communities):
        color_map[comm_id] = colors_large[i]
    for comm_id in small_communities:
        color_map[comm_id] = 'lightgray'
    
    # Affecter couleurs à chaque point
    point_colors = [color_map[comm_id] for comm_id in community_labels]
    
    # Scatter plot
    scatter = ax.scatter(
        coords_2d[:, 0],
        coords_2d[:, 1],
        c=point_colors,
        s=80,
        alpha=0.7,
        edgecolors='black',
        linewidth=0.5
    )
    
    # Légende
    from matplotlib.patches import Patch
    legend_elements = []
    
    # Trier communautés par taille
    sorted_communities = sorted(
        community_data.items(),
        key=lambda x: x[1]['size'],
        reverse=True
    )
    
    for comm_id_str, data in sorted_communities:
        comm_id = int(comm_id_str)
        
        if data['size'] > 1:
            # Grande communauté : afficher détails
            top_skills = ', '.join([s for s, _ in data['top_skills'][:2]])
            label = f"Comm. {comm_id} ({data['size']} profils) - {top_skills[:30]}"
            
            legend_elements.append(
                Patch(facecolor=color_map[comm_id], edgecolor='black', label=label)
            )
    
    # Petites communautés groupées
    n_small = sum(1 for data in community_data.values() if data['size'] == 1)
    if n_small > 0:
        legend_elements.append(
            Patch(facecolor='lightgray', edgecolor='black', label=f"Outliers ({n_small} profils)")
        )
    
    ax.legend(
        handles=legend_elements,
        loc='upper left',
        bbox_to_anchor=(1.02, 1),
        fontsize=10,
        framealpha=0.9
    )
    
    # Annotations pour quelques profils de chaque grande communauté
    import random
    random.seed(42)
    
    for comm_id in large_communities[:5]:  # Top 5 communautés
        # Indices des profils de cette communauté
        indices = [i for i, c in enumerate(community_labels) if c == comm_id]
        
        # Échantillonner 2 profils
        sample_indices = random.sample(indices, min(2, len(indices)))
        
        for idx in sample_indices:
            ax.annotate(
                node_ids[idx][:25],
                (coords_2d[idx, 0], coords_2d[idx, 1]),
                fontsize=8,
                alpha=0.7,
                xytext=(5, 5),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color_map[comm_id], alpha=0.3)
            )
    
    # Styling
    ax.set_title(
        f"Visualisation des Communautés - GraphMind\n({n_communities} communautés détectées)",
        fontsize=18,
        fontweight='bold',
        pad=20
    )
    ax.set_xlabel("Dimension 1", fontsize=14)
    ax.set_ylabel("Dimension 2", fontsize=14)
    ax.grid(True, alpha=0.3)
    
    # Sauvegarder
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Graphique sauvegardé : {save_path}")
    
    # Afficher
    plt.show()
    print("📊 Graphique affiché (fermer la fenêtre pour continuer)")


def plot_communities_interactive(
    node_ids,
    coords_2d,
    assignments,
    community_data,
    save_path: str = "data/reports/communities_2d_interactive.html"
):
    """
    Crée un graphique interactif avec Plotly coloré par communauté.
    
    Args:
        node_ids: Liste des IDs
        coords_2d: Coordonnées 2D
        assignments: Assignments communautés
        community_data: Données communautés
        save_path: Chemin HTML
    """
    try:
        import plotly.graph_objects as go
        
        print(f"\n📊 Création du graphique interactif...")
        
        # Extraire community labels
        community_labels = []
        community_names = []
        
        for node_id in node_ids:
            comm_id = assignments.get(node_id, -1)
            community_labels.append(comm_id)
            
            # Nom de la communauté (avec top skills)
            if str(comm_id) in community_data:
                data = community_data[str(comm_id)]
                if data['size'] > 1 and data['top_skills']:
                    top_skill = data['top_skills'][0][0]
                    comm_name = f"Comm. {comm_id} ({data['size']} profils) - {top_skill}"
                else:
                    comm_name = f"Outlier {comm_id}"
            else:
                comm_name = f"Community {comm_id}"
            
            community_names.append(comm_name)
        
        # Créer scatter interactif
        fig = go.Figure()
        
        # Ajouter un trace par communauté
        unique_communities = sorted(set(community_labels))
        
        for comm_id in unique_communities:
            # Indices de cette communauté
            mask = np.array(community_labels) == comm_id
            indices = np.where(mask)[0]
            
            # Nom de la communauté
            if str(comm_id) in community_data:
                data = community_data[str(comm_id)]
                if data['size'] > 1 and data['top_skills']:
                    top_skills = ', '.join([s for s, _ in data['top_skills'][:2]])
                    trace_name = f"Comm. {comm_id} ({data['size']}) - {top_skills[:40]}"
                else:
                    trace_name = f"Outlier {comm_id}"
            else:
                trace_name = f"Comm. {comm_id}"
            
            # Extraire noms des profils de cette communauté
            names = [node_ids[i] for i in indices]
            
            fig.add_trace(go.Scatter(
                x=coords_2d[indices, 0],
                y=coords_2d[indices, 1],
                mode='markers',
                name=trace_name,
                marker=dict(
                    size=10,
                    line=dict(width=0.5, color='black')
                ),
                text=names,
                hovertemplate='<b>%{text}</b><br>Communauté: ' + trace_name + '<extra></extra>'
            ))
        
        # Layout
        fig.update_layout(
            title=dict(
                text=f"Visualisation Interactive des Communautés (GraphMind)<br>{len(unique_communities)} communautés détectées",
                font=dict(size=20, color='#2c3e50')
            ),
            xaxis_title="Dimension 1",
            yaxis_title="Dimension 2",
            width=1600,
            height=1000,
            hovermode='closest',
            template='plotly_white',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.01
            )
        )
        
        # Sauvegarder
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(save_path)
        print(f"✅ Graphique interactif sauvegardé : {save_path}")
        print("   → Ouvrir dans navigateur pour explorer")
        
    except ImportError:
        print("⚠️  Plotly non installé, graphique interactif ignoré")


def print_community_summary(community_data):
    """Affiche résumé des communautés."""
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES COMMUNAUTÉS")
    print("="*80)
    
    # Trier par taille
    sorted_comms = sorted(
        community_data.items(),
        key=lambda x: x[1]['size'],
        reverse=True
    )
    
    for comm_id, data in sorted_comms[:5]:  # Top 5
        print(f"\n🏘️  Communauté {comm_id} : {data['size']} profils")
        
        if data['top_skills']:
            top_3_skills = ', '.join([s for s, _ in data['top_skills'][:3]])
            print(f"   💡 Compétences : {top_3_skills}")
        
        if data['top_schools']:
            top_school = data['top_schools'][0][0]
            print(f"   🎓 École dominante : {top_school}")


def main():
    print_separator()
    print("🎨 VISUALISATION DES COMMUNAUTÉS - GRAPHMIND")
    print_separator()
    print()
    
    # ============================================
    # CHARGEMENT
    # ============================================
    
    embeddings_file = "data/models/node2vec_embeddings.pkl"
    communities_file = "data/reports/communities.json"
    
    try:
        embeddings = load_embeddings(embeddings_file)
        assignments, community_data = load_communities(communities_file)
    except FileNotFoundError as e:
        print(f"❌ Fichier introuvable : {e}")
        print("   Exécutez d'abord :")
        print("   1. python scripts/train_node2vec.py")
        print("   2. python scripts/detect_communities.py")
        return
    
    # ============================================
    # RÉDUCTION DIMENSIONNELLE
    # ============================================
    
    print_separator()
    print("🔄 RÉDUCTION DIMENSIONNELLE (128D → 2D)")
    print_separator()
    
    node_ids, coords_2d = reduce_to_2d(embeddings)
    
    # ============================================
    # RÉSUMÉ
    # ============================================
    
    print_separator()
    print_community_summary(community_data)
    
    # ============================================
    # VISUALISATION STATIQUE
    # ============================================
    
    print()
    print_separator()
    print("📊 GRAPHIQUE STATIQUE (Matplotlib)")
    print_separator()
    
    plot_communities(node_ids, coords_2d, assignments, community_data)
    
    # ============================================
    # VISUALISATION INTERACTIVE
    # ============================================
    
    print_separator()
    print("🌐 GRAPHIQUE INTERACTIF (Plotly)")
    print_separator()
    
    plot_communities_interactive(node_ids, coords_2d, assignments, community_data)
    
    # ============================================
    # RÉSUMÉ FINAL
    # ============================================
    
    print()
    print_separator()
    print("✅ VISUALISATION TERMINÉE")
    print_separator()
    print()
    print("📊 Fichiers générés :")
    print("   1. data/reports/communities_2d.png")
    print("   2. data/reports/communities_2d_interactive.html")
    print()
    print("🎯 Prochaine étape : Link Prediction")
    print("   → python scripts/train_link_predictor.py")
    print()
    print_separator()


if __name__ == "__main__":
    main()