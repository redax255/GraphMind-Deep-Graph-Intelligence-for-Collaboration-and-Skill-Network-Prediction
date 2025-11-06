"""
Module de normalisation des entreprises avec Machine Learning.

Utilise Sentence-BERT pour embeddings et DBSCAN pour clustering automatique.
Gère français + anglais nativement.
"""

import re
import json
import pickle
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️  sentence-transformers non installé. Installez avec: pip install sentence-transformers")


# ============================================
# CONFIGURATION
# ============================================

# Modèle Sentence-BERT multilingue
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'

# Hyperparamètres DBSCAN (TRÈS STRICTS - FIXÉ)
DBSCAN_EPS = 0.03  # Similarité 97%+ pour grouper (TRÈS strict!)
DBSCAN_MIN_SAMPLES = 2  # Minimum 2 occurrences pour cluster

# Seuil similarité pour validation (AUGMENTÉ)
CLUSTER_COHERENCE_THRESHOLD = 0.90  # 90% de similarité moyenne minimum
CLUSTER_MIN_SIMILARITY = 0.75  # 75% de similarité minimale entre paires

# Seuil similarité pour cache lookup
SIMILARITY_THRESHOLD = 0.85

# Cache
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDINGS_CACHE_FILE = CACHE_DIR / "company_embeddings.pkl"
NORMALIZATION_CACHE_FILE = CACHE_DIR / "company_normalizations.json"

# Suffixes à supprimer (ORDRE IMPORTANT : plus longs d'abord)
COMPANY_SUFFIXES = [
    # Types de contrats (complets)
    "contrat en alternance", "apprentissage", "temps partiel", "temps plein", 
    "full-time", "part-time", "freelance", "internship",
    # Types de contrats courts
    "stage", "saisonnier", "contract",
    "cdi", "cdd",
    # Statuts
    "indépendant", "independent", "self-employed",
    # Formes juridiques
    "holding", "groupe", "group", "sa", "sarl", "sas", "sasu",
    "eurl", "sci", "scp", "scs", "sca", "snc",
    "inc", "ltd", "llc", "corp", "company", "co",
    # Géographiques
    "maroc", "morocco", "france", "casablanca", "rabat",
    "paris", "europe", "africa", "international",
    # Domaines
    "technologies", "technology", "solutions", "services",
    "consulting", "consultance", "digital",
]


# ============================================
# CLASSE PRINCIPALE
# ============================================

class CompanyNormalizerML:
    """
    Normaliseur d'entreprises avec Machine Learning.
    
    Utilise Sentence-BERT + DBSCAN pour normalisation automatique.
    """
    
    def __init__(self, model_name: str = MODEL_NAME):
        """
        Initialise le normaliseur.
        
        Args:
            model_name: Nom du modèle Sentence-BERT
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers requis. Installez: pip install sentence-transformers")
        
        print(f"📥 Chargement modèle {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("✅ Modèle chargé")
        
        # Cache en mémoire
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self.normalization_cache: Dict[str, str] = {}
        self.clusters: Optional[np.ndarray] = None
        
        # Charger cache depuis disque
        self._load_cache()
    
    def _load_cache(self):
        """Charge le cache depuis disque avec traçage."""
        print(f"🟡 [DEBUG] _load_cache() → {EMBEDDINGS_CACHE_FILE} / {NORMALIZATION_CACHE_FILE}")
        # Charger embeddings
        if EMBEDDINGS_CACHE_FILE.exists():
            try:
                with open(EMBEDDINGS_CACHE_FILE, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
                print(f"✅ {len(self.embeddings_cache)} embeddings chargés depuis cache")
            except Exception as e:
                print(f"⚠️  Erreur chargement embeddings cache: {e}")
        else:
            print("🔴 Aucun fichier embeddings cache trouvé")
        
        # Charger normalizations
        if NORMALIZATION_CACHE_FILE.exists():
            try:
                with open(NORMALIZATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.normalization_cache = json.load(f)
                print(f"✅ {len(self.normalization_cache)} normalisations chargées depuis cache")
            except Exception as e:
                print(f"⚠️  Erreur chargement normalizations cache: {e}")
        else:
            print("🔴 Aucun fichier normalizations cache trouvé")
    
    def clear_cache(self):
        """Vide complètement le cache (mémoire + disque)."""
        # Vider mémoire
        self.embeddings_cache.clear()
        self.normalization_cache.clear()
        
        # Vider disque
        if EMBEDDINGS_CACHE_FILE.exists():
            EMBEDDINGS_CACHE_FILE.unlink()
        if NORMALIZATION_CACHE_FILE.exists():
            NORMALIZATION_CACHE_FILE.unlink()
        
        print("✅ Cache complètement vidé (mémoire + disque)")
    
    def _save_cache(self):
        """Sauvegarde le cache sur disque avec traçage."""
        import traceback
        print(f"🟣 [DEBUG] _save_cache() → {len(self.embeddings_cache)} embeddings, {len(self.normalization_cache)} normalisations")
        traceback.print_stack(limit=2)
        # Sauvegarder embeddings
        try:
            with open(EMBEDDINGS_CACHE_FILE, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
        except Exception as e:
            print(f"⚠️  Erreur sauvegarde embeddings cache: {e}")
        
        # Sauvegarder normalizations
        try:
            with open(NORMALIZATION_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.normalization_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Erreur sauvegarde normalizations cache: {e}")
    
    def reset_cache_for_global_test(self):
        """
        Supprime le cache avant le test global pour éviter
        que les tests précédents polluent les résultats.
        """
        print("🧹 [DEBUG] Réinitialisation cache pour test global")
        self.clear_cache()
    
    def clean_company_name(self, company: str) -> str:
        """
        Nettoie le nom d'une entreprise.
        
        ORDRE CRITIQUE (FIXÉ) :
        1. Supprimer emojis
        2. Supprimer "@" patterns  
        3. Supprimer suffixes AVEC "·" (ex: " · Stage")
        4. Supprimer suffixes SANS "·" (ex: " Stage")
        5. PUIS supprimer "·" restants
        6. Normaliser espaces
        
        Args:
            company: Nom brut
        
        Returns:
            Nom nettoyé
        """
        if not company or not isinstance(company, str):
            return ""
        
        # 1. Supprimer emojis et caractères spéciaux
        text = re.sub(r'[👷‍♂️🏢💼📊🎯✨⚡🚀]+', '', company)
        
        # 2. Supprimer tirets et underscores multiples
        text = re.sub(r'[-_]+', ' ', text)
        
        # 3. Supprimer @ et texte avant
        if " @ " in text:
            text = text.split(" @ ")[-1]
        
        # 4. SUPPRIMER SUFFIXES (FIXÉ !)
        text_lower = text.lower().strip()
        
        # Étape 4a : Supprimer suffixes AVEC "·" EN PREMIER
        for suffix in COMPANY_SUFFIXES:
            # Pattern 1 : " · suffix" (espace avant ·)
            pattern1 = f" · {suffix}"
            if pattern1 in text_lower:
                idx = text_lower.find(pattern1)
                text = text[:idx]
                text_lower = text.lower().strip()
                continue
            
            # Pattern 2 : "· suffix" (pas d'espace avant ·)
            pattern2 = f"· {suffix}"
            if pattern2 in text_lower:
                idx = text_lower.find(pattern2)
                text = text[:idx]
                text_lower = text.lower().strip()
                continue
            
            # Pattern 3 : "·suffix" (pas d'espaces)
            pattern3 = f"·{suffix}"
            if pattern3 in text_lower:
                idx = text_lower.find(pattern3)
                text = text[:idx]
                text_lower = text.lower().strip()
                continue
        
        # Étape 4b : Supprimer suffixes SANS "·" (fin de chaîne uniquement)
        for suffix in COMPANY_SUFFIXES:
            pattern = f" {suffix}"
            if text_lower.endswith(pattern):
                text = text[:-(len(pattern))]
                text_lower = text.lower().strip()
        
        # 5. MAINTENANT supprimer "·" restants
        text = text.replace(" ·", "").replace("· ", "").replace("·", "")
        
        # 6. Supprimer espaces multiples et trim
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def encode_company(self, company: str) -> np.ndarray:
        """
        Encode une entreprise en embedding.
        
        Args:
            company: Nom d'entreprise (nettoyé)
        
        Returns:
            Embedding [384D]
        """
        # Normaliser case pour améliorer similarité
        company_normalized = company.lower().strip()
        
        # Vérifier cache
        if company_normalized in self.embeddings_cache:
            return self.embeddings_cache[company_normalized]
        
        # Encoder (utiliser version normalisée)
        embedding = self.model.encode(company_normalized, convert_to_numpy=True)
        
        # Mettre en cache
        self.embeddings_cache[company_normalized] = embedding
        
        return embedding
    
    def validate_cluster_coherence(self, cluster_companies: List[str], 
                                   cluster_embeddings: np.ndarray,
                                   coherence_threshold: float = 0.90,  # Augmenté à 90%
                                   min_similarity_threshold: float = 0.75) -> bool:  # Nouveau seuil minimal
        """
        Valide la cohérence sémantique d'un cluster (VERSION STRICTE).
        
        Args:
            cluster_companies: Entreprises du cluster
            cluster_embeddings: Embeddings du cluster
            coherence_threshold: Seuil de similarité moyenne (0.90 = 90%)
            min_similarity_threshold: Seuil de similarité minimale (0.75 = 75%)
        
        Returns:
            True si cluster cohérent, False sinon
        """
        if len(cluster_companies) < 2:
            return True
        
        # Calculer similarité moyenne intra-cluster
        similarity_matrix = cosine_similarity(cluster_embeddings)
        np.fill_diagonal(similarity_matrix, 0)  # Exclure auto-similarité
        
        # Moyenne des similarités
        avg_similarity = np.mean(similarity_matrix[similarity_matrix > 0])
        
        # Similarité minimale (pire paire)
        min_similarity = np.min(similarity_matrix[similarity_matrix > 0])
        
        # Cluster cohérent si similarité moyenne ET minimale élevées
        is_coherent = (avg_similarity >= coherence_threshold and 
                      min_similarity >= min_similarity_threshold)
        
        if not is_coherent:
            print(f"⚠️  Cluster incohérent détecté ({len(cluster_companies)} entreprises)")
            print(f"    Similarité moyenne: {avg_similarity:.3f}, minimale: {min_similarity:.3f}")
            print(f"    Exemples : {cluster_companies[:3]}")
        
        return is_coherent
    
    def refine_cluster_hierarchical(self, cluster_companies: List[str], 
                                    cluster_embeddings: np.ndarray,
                                    threshold: float = 0.80) -> List[List[str]]:
        """
        Affine un cluster incohérent avec clustering hiérarchique.
        
        Args:
            cluster_companies: Entreprises du cluster
            cluster_embeddings: Embeddings du cluster
            threshold: Seuil de similarité pour sous-clusters
        
        Returns:
            Liste de sous-clusters
        """
        from sklearn.cluster import AgglomerativeClustering
        
        if len(cluster_companies) <= 2:
            return [cluster_companies]
        
        # Clustering hiérarchique
        hierarchical = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1 - threshold,  # Convert similarity to distance
            affinity='cosine',
            linkage='average'
        )
        
        sub_labels = hierarchical.fit_predict(cluster_embeddings)
        
        # Grouper par sous-cluster
        sub_clusters = {}
        for i, label in enumerate(sub_labels):
            if label not in sub_clusters:
                sub_clusters[label] = []
            sub_clusters[label].append(cluster_companies[i])
        
        result = list(sub_clusters.values())
        
        print(f"    → Divisé en {len(result)} sous-clusters")
        
        return result
    
    def fit_clusters(self, companies: List[str], eps: float = DBSCAN_EPS, 
                     min_samples: int = DBSCAN_MIN_SAMPLES,
                     validate_coherence: bool = True,
                     coherence_threshold: float = 0.90) -> np.ndarray:  # Augmenté à 90%
        """
        Applique DBSCAN clustering avec validation et raffinement automatique.
        
        Args:
            companies: Liste d'entreprises (nettoyées)
            eps: Rayon epsilon pour DBSCAN (0.03 = 97% similarité)
            min_samples: Minimum de samples pour cluster
            validate_coherence: Si True, valide et raffine les clusters
            coherence_threshold: Seuil de cohérence intra-cluster (0.90 = 90%)
        
        Returns:
            Labels des clusters (-1 = bruit)
        """
        if not companies:
            return np.array([])
        
        print(f"\n🔄 Encoding {len(companies)} entreprises...")
        
        # Encoder toutes les entreprises
        embeddings = np.array([self.encode_company(c) for c in companies])
        
        print(f"✅ {len(companies)} embeddings générés")
        print(f"🔄 Clustering DBSCAN (eps={eps}, min_samples={min_samples})...")
        
        # DBSCAN clustering initial
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = clustering.fit_predict(embeddings)
        
        # Statistiques initiales
        n_clusters_initial = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_initial = list(labels).count(-1)
        
        print(f"✅ {n_clusters_initial} clusters trouvés (initial)")
        print(f"✅ {n_noise_initial} entreprises uniques (bruit)")
        
        # Validation et raffinement
        if validate_coherence and n_clusters_initial > 0:
            print(f"\n🔍 Validation de cohérence des clusters...")
            
            refined_labels = labels.copy()
            next_cluster_id = labels.max() + 1
            refined_count = 0
            
            for cluster_id in range(n_clusters_initial):
                # Indices du cluster
                cluster_mask = labels == cluster_id
                cluster_indices = np.where(cluster_mask)[0]
                
                if len(cluster_indices) < 2:
                    continue
                
                cluster_companies = [companies[i] for i in cluster_indices]
                cluster_embeddings = embeddings[cluster_indices]
                
                # Valider cohérence
                is_coherent = self.validate_cluster_coherence(
                    cluster_companies, 
                    cluster_embeddings,
                    coherence_threshold
                )
                
                # Si incohérent, raffiner
                if not is_coherent:
                    sub_clusters = self.refine_cluster_hierarchical(
                        cluster_companies,
                        cluster_embeddings,
                        threshold=0.80
                    )
                    
                    # Réassigner labels
                    if len(sub_clusters) > 1:
                        refined_count += 1
                        for sub_idx, sub_cluster in enumerate(sub_clusters):
                            for company in sub_cluster:
                                # Trouver l'indice global
                                global_idx = cluster_indices[cluster_companies.index(company)]
                                
                                if sub_idx == 0:
                                    # Garder cluster ID original
                                    refined_labels[global_idx] = cluster_id
                                else:
                                    # Nouveau cluster ID
                                    refined_labels[global_idx] = next_cluster_id
                                    next_cluster_id += 1
            
            if refined_count > 0:
                labels = refined_labels
                n_clusters_final = len(set(labels)) - (1 if -1 in labels else 0)
                print(f"\n✅ Raffinement terminé : {refined_count} cluster(s) divisé(s)")
                print(f"✅ {n_clusters_final} clusters finaux (vs {n_clusters_initial} initial)")
            else:
                print(f"\n✅ Tous les clusters sont cohérents")
        
        self.clusters = labels
        return labels
    
    def get_cluster_representative(self, cluster_companies: List[str]) -> str:
        """
        Choisit le représentant d'un cluster.
        
        Stratégie : Le nom le plus fréquent et le plus propre.
        
        Args:
            cluster_companies: Liste des entreprises du cluster
        
        Returns:
            Nom représentatif
        """
        if not cluster_companies:
            return ""
        
        if len(cluster_companies) == 1:
            return cluster_companies[0]
        
        # Compter fréquences (case-insensitive)
        counter = Counter([c.lower() for c in cluster_companies])
        most_common_lower = counter.most_common(1)[0][0]
        
        # Trouver la version originale la plus propre
        candidates = [c for c in cluster_companies if c.lower() == most_common_lower]
        
        # Préférer version sans ponctuation excessive
        def score_cleanliness(name):
            score = 0
            if name[0].isupper():  # Commence par majuscule
                score += 1
            if '·' not in name and '•' not in name:  # Pas de bullet points
                score += 1
            if len(name.split()) <= 3:  # Pas trop long
                score += 1
            return score
        
        best = max(candidates, key=score_cleanliness)
        
        # Title case
        words = best.split()
        normalized_words = []
        for word in words:
            # Garder acronymes en majuscules (2-4 lettres)
            if word.isupper() and 2 <= len(word) <= 4:
                normalized_words.append(word)
            else:
                normalized_words.append(word.capitalize())
        
        return ' '.join(normalized_words)
    
    def normalize_companies_batch(self, companies: List[str]) -> Dict[str, str]:
        """
        Normalise un batch d'entreprises.
        
        Args:
            companies: Liste d'entreprises brutes
        
        Returns:
            Dict {entreprise_brute: entreprise_normalisée}
        """
        if not companies:
            return {}
        
        print(f"\n{'='*70}")
        print(f"🔄 NORMALISATION DE {len(companies)} ENTREPRISES")
        print(f"{'='*70}")
        
        # 1. Nettoyer
        print("\n1️⃣  Nettoyage...")
        cleaned = {}
        for company in companies:
            clean = self.clean_company_name(company)
            if clean and clean.lower() not in ["", "n/a", "na", "none"]:
                cleaned[company] = clean
        
        print(f"✅ {len(cleaned)} entreprises valides après nettoyage")
        
        if not cleaned:
            return {}
        
        # 2. Vérifier cache
        print("\n2️⃣  Vérification cache...")
        normalized = {}
        to_process = []
        
        for raw, clean in cleaned.items():
            if clean in self.normalization_cache:
                normalized[raw] = self.normalization_cache[clean]
            else:
                to_process.append((raw, clean))
        
        print(f"✅ {len(normalized)} entreprises trouvées dans cache")
        print(f"🔄 {len(to_process)} entreprises à traiter")
        
        if not to_process:
            return normalized
        
        # 3. Clustering sur nouvelles entreprises
        print("\n3️⃣  Clustering...")
        unique_cleaned = list(set([clean for _, clean in to_process]))
        labels = self.fit_clusters(unique_cleaned)
        
        # 4. Normaliser par cluster
        print("\n4️⃣  Normalisation par cluster...")
        cluster_map = {}
        
        for cluster_id in set(labels):
            if cluster_id == -1:
                # Bruit : garder tel quel
                continue
            
            # Entreprises du cluster
            cluster_companies = [unique_cleaned[i] for i, label in enumerate(labels) if label == cluster_id]
            
            # Choisir représentant
            representative = self.get_cluster_representative(cluster_companies)
            
            # Mapper toutes les variations
            for company in cluster_companies:
                cluster_map[company] = representative
        
        # Bruit : garder tel quel
        for i, label in enumerate(labels):
            if label == -1:
                cluster_map[unique_cleaned[i]] = unique_cleaned[i]
        
        # 5. Appliquer normalisation
        for raw, clean in to_process:
            norm = cluster_map.get(clean, clean)
            normalized[raw] = norm
            self.normalization_cache[clean] = norm
        
        # 6. Sauvegarder cache
        print("\n5️⃣  Sauvegarde cache...")
        self._save_cache()
        
        print(f"\n✅ Normalisation terminée : {len(normalized)} entreprises")
        print(f"{'='*70}\n")
        
        return normalized
    
    def normalize_company(self, company: str) -> str:
        """
        Normalise une seule entreprise.
        
        Args:
            company: Nom brut
        
        Returns:
            Nom normalisé
        """
        result = self.normalize_companies_batch([company])
        return result.get(company, company)


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def extract_all_companies_from_profiles(profiles: List[Dict], filter_outliers: bool = True, 
                                         outlier_threshold: float = 0.5) -> List[str]:
    """
    Extrait TOUTES les entreprises brutes de TOUS les profils.
    
    Args:
        profiles: Liste de profils
        filter_outliers: Si True, filtre les entreprises statistiquement anormales
        outlier_threshold: Seuil % au-delà duquel une entreprise est considérée outlier
    
    Returns:
        Liste de toutes les entreprises brutes (avec doublons)
    """
    # Liste noire d'entreprises invalides
    INVALID_COMPANIES = {
        # Placeholders scraping
        "henceforth",
        # Invalides génériques
        "n/a",
        "none",
        "unknown",
        "undefined",
        "null",
    }
    
    # Patterns suspects (institutions gouvernementales, etc.)
    SUSPICIOUS_PATTERNS = [
        "tribunal",
        "secrétaire général",
        "ministère",
        "gouvernement",
    ]
    
    all_companies = []
    
    for profile in profiles:
        for exp in profile.get('experience', []):
            company = exp.get('company')
            if company:
                company_lower = company.lower().strip()
                
                # Vérifier liste noire
                if company_lower in INVALID_COMPANIES:
                    continue
                
                # Vérifier patterns suspects (optionnel selon contexte)
                # Commenté pour garder institutions gouvernementales légitimes
                # is_suspicious = any(pattern in company_lower for pattern in SUSPICIOUS_PATTERNS)
                # if is_suspicious:
                #     continue
                
                all_companies.append(company)
    
    # Filtrage statistique des outliers
    if filter_outliers and len(all_companies) > 0:
        from collections import Counter
        company_counts = Counter(all_companies)
        total = len(profiles)
        
        # Filtrer entreprises avec >50% des profils (outliers)
        filtered_companies = []
        outliers_detected = []
        
        for company in all_companies:
            count = company_counts[company]
            percentage = count / total
            
            if percentage > outlier_threshold:
                outliers_detected.append((company, count, percentage))
            else:
                filtered_companies.append(company)
        
        # Log outliers
        if outliers_detected:
            print(f"\n⚠️  Outliers détectés et filtrés (>{outlier_threshold*100}% des profils) :")
            for company, count, pct in outliers_detected:
                print(f"   - {company} : {count} profils ({pct*100:.1f}%)")
            print()
        
        return filtered_companies
    
    return all_companies


def normalize_all_companies_global(profiles: List[Dict], normalizer: CompanyNormalizerML) -> Dict[str, str]:
    """
    Normalise TOUTES les entreprises de TOUS les profils en une seule fois (clustering global).
    
    Args:
        profiles: Liste de profils
        normalizer: Instance CompanyNormalizerML
    
    Returns:
        Dictionnaire {entreprise_brute: entreprise_normalisée}
    """
    print("\n" + "="*80)
    print("🌍 NORMALISATION GLOBALE - TOUS LES PROFILS")
    print("="*80)
    
    # 1. Extraire toutes les entreprises
    all_companies_raw = extract_all_companies_from_profiles(profiles)
    
    print(f"\n✅ {len(all_companies_raw)} entreprises extraites depuis {len(profiles)} profils")
    print(f"✅ {len(set(all_companies_raw))} entreprises uniques (brutes)")
    
    # 2. Normaliser en un seul batch (clustering global)
    normalized_map = normalizer.normalize_companies_batch(all_companies_raw)
    
    print(f"\n✅ Normalisation globale terminée")
    print("="*80 + "\n")
    
    return normalized_map


def normalize_companies_from_profile(profile: Dict, normalizer: CompanyNormalizerML) -> Set[str]:
    """
    Extrait et normalise les entreprises d'un profil.
    
    Args:
        profile: Profil MongoDB
        normalizer: Instance CompanyNormalizerML
    
    Returns:
        Set d'entreprises normalisées
    """
    companies_raw = []
    
    # Extraire depuis experience
    for exp in profile.get('experience', []):
        company = exp.get('company')
        if company:
            companies_raw.append(company)
    
    if not companies_raw:
        return set()
    
    # Normaliser
    normalized_dict = normalizer.normalize_companies_batch(companies_raw)
    
    return set(normalized_dict.values())


def get_company_statistics(profiles: List[Dict], normalizer: CompanyNormalizerML, 
                           use_global_clustering: bool = True,
                           post_filter_threshold: float = 0.15) -> Dict:
    """
    Calcule des statistiques sur les entreprises.
    
    Args:
        profiles: Liste de profils
        normalizer: Instance CompanyNormalizerML
        use_global_clustering: Si True, fait un clustering global. Sinon, profil par profil.
        post_filter_threshold: Seuil post-normalisation pour détecter anomalies (0.15 = 15%)
    
    Returns:
        Statistiques
    """
    if use_global_clustering:
        # Clustering global (recommandé)
        normalized_map = normalize_all_companies_global(profiles, normalizer)
        
        # Extraire entreprises normalisées pour chaque profil
        all_companies = []
        for profile in profiles:
            for exp in profile.get('experience', []):
                company = exp.get('company')
                if company and company in normalized_map:
                    all_companies.append(normalized_map[company])
    else:
        # Clustering par profil (ancien comportement)
        all_companies = []
        for profile in profiles:
            companies = normalize_companies_from_profile(profile, normalizer)
            all_companies.extend(companies)
    
    company_counts = Counter(all_companies)
    total_profiles = len(profiles)
    
    # Post-filtrage : détecter les anomalies
    suspicious_companies = []
    filtered_companies = []
    
    for company, count in company_counts.items():
        percentage = count / total_profiles
        
        if percentage > post_filter_threshold:
            suspicious_companies.append((company, count, percentage))
            print(f"⚠️  Entreprise suspecte détectée : '{company}' ({count} profils, {percentage*100:.1f}%)")
        else:
            filtered_companies.append(company)
    
    # Recalculer sans les suspects si demandé
    if suspicious_companies:
        print(f"\n⚠️  {len(suspicious_companies)} entreprise(s) suspecte(s) détectée(s)")
        print("   Continuant avec toutes les entreprises (incluant suspectes)...")
    
    return {
        "total_profiles": len(profiles),
        "unique_companies": len(company_counts),
        "top_20_companies": company_counts.most_common(20),
        "companies_with_1_profile": sum(1 for count in company_counts.values() if count == 1),
        "companies_with_5plus_profiles": sum(1 for count in company_counts.values() if count >= 5),
        "companies_with_10plus_profiles": sum(1 for count in company_counts.values() if count >= 10),
        "suspicious_companies": suspicious_companies  # Nouvelle métrique
    }


# ============================================
# EXPORT
# ============================================

__all__ = [
    "CompanyNormalizerML",
    "normalize_companies_from_profile",
    "normalize_all_companies_global",
    "extract_all_companies_from_profiles",
    "get_company_statistics"
]