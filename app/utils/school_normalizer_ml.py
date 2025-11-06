"""
Normalisation des écoles/universités avec Machine Learning.
Utilise Sentence-BERT + DBSCAN pour détecter et grouper automatiquement
les variantes d'une même école.

VALIDATION INTELLIGENTE : Utilise moroccan_cities.json pour éviter de grouper
des écoles de villes différentes (ex: ENSA Fès ≠ ENSA Marrakech).

Adapté de company_normalizer_ml.py pour les établissements d'enseignement.
"""

import pickle
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set
from collections import defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity


# Configuration
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'  # Support français + anglais
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

EMBEDDINGS_CACHE = CACHE_DIR / "school_embeddings.pkl"
NORMALIZATIONS_CACHE = CACHE_DIR / "school_normalizations.json"

# Fichier des villes marocaines
CITIES_JSON = Path("data") / "moroccan_cities.json"

# Hyperparamètres DBSCAN (PLUS STRICT)
DBSCAN_EPS = 0.025  # Similarité 97.5%+ pour grouper (plus strict que 0.03)
DBSCAN_MIN_SAMPLES = 2

# Validation cohérence cluster
CLUSTER_COHERENCE_THRESHOLD = 0.90  # 90% similarité moyenne minimum
CLUSTER_MIN_SIMILARITY = 0.75  # 75% similarité minimale entre paires


class SchoolNormalizerML:
    """
    Normalise les noms d'écoles avec Machine Learning.
    
    Architecture :
    1. Preprocessing : Nettoyer suffixes/préfixes
    2. Embedding : Sentence-BERT (384D)
    3. Clustering : DBSCAN (eps=0.03)
    4. Validation : Cohérence sémantique
    5. Normalisation : Choisir représentant propre
    """
    
    def __init__(self, use_cache: bool = True):
        """
        Args:
            use_cache: Si True, charge/sauvegarde embeddings en cache
        """
        self.use_cache = use_cache
        self.model = None
        self.embeddings_cache = {}
        self.normalizations = {}
        
        # Charger les villes marocaines
        self.moroccan_cities = self._load_moroccan_cities()
        
        # Charger cache si disponible
        if use_cache:
            self._load_cache()
    
    def _load_moroccan_cities(self) -> Dict[str, Set[str]]:
        """
        Charge le fichier JSON des villes marocaines.
        
        Returns:
            Dict avec {nom_ville: set(variations)}
        """
        if not CITIES_JSON.exists():
            print(f"⚠️  Fichier {CITIES_JSON} introuvable, validation ville désactivée")
            return {}
        
        try:
            with open(CITIES_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Créer dictionnaire {ville: variations}
            cities_dict = {}
            for city_info in data.get('cities', []):
                name = city_info['name']
                variations = set(city_info['variations'])
                cities_dict[name] = variations
            
            print(f"✅ {len(cities_dict)} villes marocaines chargées")
            return cities_dict
            
        except Exception as e:
            print(f"⚠️  Erreur chargement villes : {e}")
            return {}
    
    def _extract_city_from_school(self, school: str) -> str:
        """
        Extrait la ville d'un nom d'école.
        
        Args:
            school: Nom de l'école
        
        Returns:
            Nom de la ville standardisé, ou "" si aucune ville détectée
        
        Exemples:
            "ENSA Fès" → "Fès"
            "Université Ibn Tofail - Kénitra" → "Kénitra"
            "ENSIAS" → ""
        """
        if not self.moroccan_cities:
            return ""
        
        school_lower = school.lower()
        
        # Chercher chaque ville
        for city_name, variations in self.moroccan_cities.items():
            for variation in variations:
                if variation.lower() in school_lower:
                    return city_name  # Retourner nom standardisé
        
        return ""
    
    def _are_same_school(self, school_a: str, school_b: str) -> bool:
        """
        Vérifie si 2 écoles sont vraiment identiques (même établissement).
        
        RÈGLE CRITIQUE : Si elles contiennent des villes différentes,
        ce sont des écoles différentes, même si sémantiquement similaires.
        
        Exemples:
            "ENSA Fès" vs "ENSA Marrakech" → False (villes différentes)
            "Université Ibn Tofail" vs "Ibn tofail university" → True (même ville ou pas de ville)
        
        Args:
            school_a, school_b: Noms des écoles
        
        Returns:
            True si même école, False si écoles différentes
        """
        city_a = self._extract_city_from_school(school_a)
        city_b = self._extract_city_from_school(school_b)
        
        # Si les 2 ont des villes ET elles sont différentes → écoles différentes
        if city_a and city_b and city_a != city_b:
            return False
        
        # Sinon, elles peuvent être groupées
        return True
    
    def _load_cache(self):
        """Charge le cache des embeddings et normalisations."""
        # Embeddings
        if EMBEDDINGS_CACHE.exists():
            try:
                with open(EMBEDDINGS_CACHE, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
                print(f"✅ Cache embeddings chargé : {len(self.embeddings_cache)} écoles")
            except Exception as e:
                print(f"⚠️  Erreur chargement cache embeddings : {e}")
        
        # Normalizations
        if NORMALIZATIONS_CACHE.exists():
            try:
                with open(NORMALIZATIONS_CACHE, 'r', encoding='utf-8') as f:
                    self.normalizations = json.load(f)
                print(f"✅ Cache normalizations chargé : {len(self.normalizations)} mappings")
            except Exception as e:
                print(f"⚠️  Erreur chargement cache normalizations : {e}")
    
    def _save_cache(self):
        """Sauvegarde le cache."""
        # Embeddings
        try:
            with open(EMBEDDINGS_CACHE, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            print(f"✅ Cache embeddings sauvegardé : {len(self.embeddings_cache)} écoles")
        except Exception as e:
            print(f"⚠️  Erreur sauvegarde cache embeddings : {e}")
        
        # Normalizations
        try:
            with open(NORMALIZATIONS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(self.normalizations, f, ensure_ascii=False, indent=2)
            print(f"✅ Cache normalizations sauvegardé : {len(self.normalizations)} mappings")
        except Exception as e:
            print(f"⚠️  Erreur sauvegarde cache normalizations : {e}")
    
    def _preprocess_school_name(self, school: str) -> str:
        """
        Nettoie le nom d'école en supprimant suffixes/préfixes inutiles.
        
        Exemples :
            "ENSIAS · Licence" → "ENSIAS"
            "Université Ibn Tofail - Kénitra" → "Université Ibn Tofail"
            "École Nationale (ENSA)" → "École Nationale ENSA"
            "Ibn tofaïl university - Kénitra" → "Ibn tofaïl university"
        """
        if not school:
            return ""
        
        # Supprimer espaces multiples
        school = " ".join(school.split())
        
        # Suffixes à supprimer (diplômes, types de cursus)
        suffixes_to_remove = [
            '· Bachelor', '· Master', '· PhD', '· Doctorat',
            '· Licence', '· Ingénieur', '· DUT', '· BTS',
            '· Stage', '· Temps plein', '· Temps partiel',
            '· CDI', '· CDD', '· Alternance',
            ', Bachelor', ', Master', ', PhD', ', Doctorat'
        ]
        
        for suffix in suffixes_to_remove:
            if suffix in school:
                school = school.replace(suffix, '').strip()
        
        # Supprimer suffixes géographiques (villes marocaines)
        # Pattern : " - Ville" ou " de Ville" ou ", Ville"
        cities = [
            'Kénitra', 'Kenitra', 'Rabat', 'Casablanca', 'Fès', 'Fes',
            'Marrakech', 'Tanger', 'Agadir', 'Meknès', 'Oujda', 'Settat',
            'Salé', 'Sale', 'Mohammedia', 'Tétouan', 'El Jadida'
        ]
        
        for city in cities:
            patterns = [
                f' - {city}',
                f' de {city}',
                f', {city}',
                f' {city}',  # En dernier (plus agressif)
            ]
            for pattern in patterns:
                # Vérifier que le pattern est en fin de chaîne
                if school.endswith(pattern):
                    school = school[:-len(pattern)].strip()
                    break
        
        # Supprimer tirets isolés en fin (ex: "École - ")
        school = school.rstrip('- ').strip()
        
        # Remplacer tirets par espaces dans certains cas
        # "Université Ibn Tofail - Autre" → "Université Ibn Tofail Autre"
        if ' - ' in school:
            school = school.replace(' - ', ' ')
        
        # Remplacer parenthèses par espaces
        # "École Nationale (ENSA)" → "École Nationale ENSA"
        school = school.replace('(', ' ').replace(')', ' ')
        
        # Supprimer caractères spéciaux isolés
        school = school.replace('·', ' ')
        school = school.replace('[', ' ').replace(']', ' ')
        school = school.replace(':', ' ')
        
        # Nettoyer espaces multiples
        school = " ".join(school.split())
        
        return school.strip()
    
    def _get_embedding(self, school: str) -> np.ndarray:
        """
        Génère ou récupère embedding d'une école.
        Utilise cache si disponible.
        """
        # Préprocessing
        clean_school = self._preprocess_school_name(school)
        
        # Utiliser nom original comme clé (pas le préprocessé !)
        # Pour éviter "ecole" vs "école" dans le cache
        cache_key = school.strip()
        
        # Vérifier cache
        if cache_key in self.embeddings_cache:
            return self.embeddings_cache[cache_key]
        
        # Charger modèle si besoin
        if self.model is None:
            print("🔄 Chargement Sentence-BERT...")
            self.model = SentenceTransformer(MODEL_NAME)
            print("✅ Modèle chargé")
        
        # Générer embedding
        embedding = self.model.encode(clean_school, convert_to_numpy=True)
        
        # Sauvegarder dans cache
        if self.use_cache:
            self.embeddings_cache[cache_key] = embedding
        
        return embedding
    
    def _validate_cluster_coherence(self, schools: List[str], embeddings: np.ndarray) -> bool:
        """
        Valide qu'un cluster est cohérent (écoles vraiment similaires).
        
        Critères :
        1. CRITIQUE : Toutes les écoles doivent être de la même ville (ou sans ville)
        2. Similarité moyenne ≥ CLUSTER_COHERENCE_THRESHOLD (90%)
        3. Similarité minimale ≥ CLUSTER_MIN_SIMILARITY (75%)
        """
        if len(schools) < 2:
            return True
        
        # 1. Validation VILLE (CRITIQUE)
        # Vérifier que toutes les écoles du cluster sont compatibles (même ville)
        for i in range(len(schools)):
            for j in range(i + 1, len(schools)):
                if not self._are_same_school(schools[i], schools[j]):
                    print(f"⚠️  Cluster rejeté (villes différentes) :")
                    print(f"   - {schools[i]}")
                    print(f"   - {schools[j]}")
                    return False
        
        # 2. Validation SÉMANTIQUE
        # Calculer matrice similarité
        similarities = cosine_similarity(embeddings)
        
        # Extraire triangle supérieur (paires uniques)
        n = len(similarities)
        upper_triangle = similarities[np.triu_indices(n, k=1)]
        
        if len(upper_triangle) == 0:
            return True
        
        # Similarité moyenne
        avg_similarity = np.mean(upper_triangle)
        
        # Similarité minimale
        min_similarity = np.min(upper_triangle)
        
        # Validation
        is_coherent = (avg_similarity >= CLUSTER_COHERENCE_THRESHOLD and 
                      min_similarity >= CLUSTER_MIN_SIMILARITY)
        
        if not is_coherent:
            print(f"⚠️  Cluster rejeté (similarité faible) : avg={avg_similarity:.3f}, min={min_similarity:.3f}")
            print(f"   Écoles : {schools}")
        
        return is_coherent
    
    def _choose_representative(self, schools: List[str]) -> str:
        """
        Choisit le meilleur représentant d'un cluster.
        
        Critères (ordre de priorité) :
        1. Nom le plus propre (pas de suffixes, parenthèses)
        2. Nom le plus court (moins verbeux)
        3. Commence par majuscule
        4. Plus fréquent dans les données
        """
        # Scorer chaque école
        def score_school(school: str) -> Tuple[int, int, bool, int]:
            clean = self._preprocess_school_name(school)
            
            # 1. Propreté : Pas de caractères spéciaux
            cleanliness = sum([
                '·' not in school,
                '(' not in school,
                ')' not in school,
                '-' not in school or school.count('-') == 1,  # Tiret OK si unique
            ])
            
            # 2. Longueur (inversée pour tri)
            length = len(school)
            
            # 3. Commence par majuscule
            starts_upper = school[0].isupper() if school else False
            
            # 4. Fréquence (on ne l'a pas ici, utiliser longueur comme proxy)
            frequency = 0
            
            return (-cleanliness, length, not starts_upper, frequency)
        
        # Trier par score
        best = min(schools, key=score_school)
        return best
    
    def normalize_schools(self, schools: List[str]) -> Dict[str, str]:
        """
        Normalise une liste d'écoles avec ML.
        
        Args:
            schools: Liste des noms d'écoles bruts
        
        Returns:
            Dictionnaire {école_brute: école_normalisée}
        """
        print("="*80)
        print("🎓 NORMALISATION DES ÉCOLES (ML)")
        print("="*80)
        print()
        
        # Dédupliquer
        unique_schools = sorted(set(school.strip() for school in schools if school.strip()))
        
        print(f"📊 Écoles uniques à traiter : {len(unique_schools)}")
        print()
        
        # 1. Générer embeddings
        print("🔄 Génération des embeddings...")
        embeddings = []
        for school in unique_schools:
            emb = self._get_embedding(school)
            embeddings.append(emb)
        embeddings = np.array(embeddings)
        print(f"✅ {len(embeddings)} embeddings générés (384D)")
        print()
        
        # 2. Clustering DBSCAN
        print(f"🔄 Clustering DBSCAN (eps={DBSCAN_EPS}, min_samples={DBSCAN_MIN_SAMPLES})...")
        clustering = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES, metric='cosine')
        labels = clustering.fit_predict(embeddings)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        print(f"✅ {n_clusters} clusters formés")
        print(f"✅ {n_noise} écoles isolées (pas de doublon détecté)")
        print()
        
        # 3. Créer mappings
        print("🔄 Création des mappings...")
        normalizations = {}
        clusters_formed = []
        
        for cluster_id in set(labels):
            if cluster_id == -1:
                # Noise : pas de cluster, garder tel quel
                indices = np.where(labels == -1)[0]
                for idx in indices:
                    school = unique_schools[idx]
                    normalizations[school] = school
            else:
                # Cluster : grouper variantes
                indices = np.where(labels == cluster_id)[0]
                cluster_schools = [unique_schools[idx] for idx in indices]
                cluster_embeddings = embeddings[indices]
                
                # Valider cohérence
                if not self._validate_cluster_coherence(cluster_schools, cluster_embeddings):
                    # Cluster incohérent : garder tel quel
                    for school in cluster_schools:
                        normalizations[school] = school
                    continue
                
                # Choisir représentant
                representative = self._choose_representative(cluster_schools)
                
                # Mapper toutes les variantes
                for school in cluster_schools:
                    normalizations[school] = representative
                
                # Sauvegarder cluster
                if len(cluster_schools) > 1:
                    clusters_formed.append({
                        'representative': representative,
                        'variations': cluster_schools
                    })
        
        print(f"✅ {len(normalizations)} mappings créés")
        print(f"✅ {len(clusters_formed)} clusters valides")
        print()
        
        # 4. Statistiques
        print("="*80)
        print("📊 RÉSULTATS")
        print("="*80)
        print()
        
        unique_normalized = len(set(normalizations.values()))
        reduction = (1 - unique_normalized / len(unique_schools)) * 100
        
        print(f"✅ Écoles uniques (avant) : {len(unique_schools)}")
        print(f"✅ Écoles uniques (après) : {unique_normalized}")
        print(f"✅ Réduction : {reduction:.1f}%")
        print()
        
        # Top clusters
        if clusters_formed:
            print("📋 Top 10 clusters formés :")
            clusters_sorted = sorted(clusters_formed, 
                                    key=lambda x: len(x['variations']), 
                                    reverse=True)
            
            for i, cluster in enumerate(clusters_sorted[:10], 1):
                rep = cluster['representative']
                vars = cluster['variations']
                print(f"\n{i}. '{rep}' ← {len(vars)} variations :")
                for var in sorted(vars):
                    if var != rep:
                        print(f"      - {var}")
        
        print()
        
        # 5. Sauvegarder cache
        if self.use_cache:
            self.normalizations = normalizations
            self._save_cache()
        
        return normalizations
    
    def get_normalized_name(self, school: str) -> str:
        """
        Retourne le nom normalisé d'une école.
        Utilise cache si disponible.
        """
        school = school.strip()
        
        # Vérifier cache
        if school in self.normalizations:
            return self.normalizations[school]
        
        # Pas en cache : retourner tel quel
        return school


def main():
    """Test du normalizer."""
    # Exemples
    test_schools = [
        "Université Ibn Tofail",
        "université ibn tofail",
        "Universite ibn tofail",
        "École Nationale des Sciences Appliquées de Fès",
        "École Nationale des Sciences Appliquées de Fes",
        "ENSIAS · Licence",
        "ENSIAS",
        "Ecole Marocaine des Sciences de l'ingénieur",
    ]
    
    print("🧪 TEST DU NORMALIZER")
    print("="*80)
    print()
    
    normalizer = SchoolNormalizerML(use_cache=True)
    normalizations = normalizer.normalize_schools(test_schools)
    
    print()
    print("📋 Résultats :")
    for original, normalized in normalizations.items():
        if original != normalized:
            print(f"   {original:<50} → {normalized}")
    
    print()
    print("✅ Test terminé")


if __name__ == "__main__":
    main()