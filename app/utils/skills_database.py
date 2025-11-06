# skills_database.py

"""
Base de données de compétences techniques.

Liste exhaustive de compétences tech pour l'extraction depuis les profils.
Organisée par catégories pour faciliter l'analyse.
"""

from typing import Dict, List, Set


# ============================================
# LANGAGES DE PROGRAMMATION
# ============================================

PROGRAMMING_LANGUAGES = {
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "C",
    "Go", "Golang", "Rust", "Ruby", "PHP", "Swift", "Kotlin",
    "Scala", "R", "MATLAB", "Julia", "Perl", "Shell", "Bash",
    "PowerShell", "Dart", "Elixir", "Haskell", "Lua", "Groovy"
}

# ============================================
# FRAMEWORKS WEB & BACKEND
# ============================================

WEB_FRAMEWORKS = {
    # Python
    "Django", "Flask", "FastAPI", "Pyramid", "Tornado", "Bottle",
    
    # JavaScript/TypeScript
    "React", "ReactJS", "React.js", "Angular", "AngularJS", "Vue", "Vue.js",
    "Next.js", "Nuxt.js", "Svelte", "Ember.js", "Backbone.js",
    "Node.js", "NodeJS", "Express", "Express.js", "Nest.js", "NestJS",
    "Koa", "Fastify",
    
    # Java
    "Spring", "Spring Boot", "Hibernate", "Struts", "JSF", "Play Framework",
    
    # Autres
    "ASP.NET", ".NET", "Ruby on Rails", "Laravel", "Symfony", "CodeIgniter"
}

# ============================================
# BASES DE DONNÉES
# ============================================

DATABASES = {
    # SQL
    "SQL", "MySQL", "PostgreSQL", "Oracle", "SQL Server", "SQLite",
    "MariaDB", "DB2",
    
    # NoSQL
    "MongoDB", "Redis", "Cassandra", "CouchDB", "Neo4j", "DynamoDB",
    "Elasticsearch", "Solr", "InfluxDB", "TimescaleDB",
    
    # Graph DB
    "Neo4j", "ArangoDB", "OrientDB"
}

# ============================================
# DATA SCIENCE & ML
# ============================================

DATA_SCIENCE_ML = {
    # ML Frameworks
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost", "LightGBM",
    "CatBoost", "H2O", "MLlib", "Caffe", "Theano", "MXNet",
    
    # DL & Computer Vision
    "YOLO", "OpenCV", "CNN", "RNN", "LSTM", "GAN", "Transformer",
    
    # NLP
    "NLTK", "spaCy", "Hugging Face", "BERT", "GPT", "LLM",
    
    # Data Analysis
    "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly",
    "Jupyter", "Jupyter Notebook", "JupyterLab",
    
    # Big Data
    "Spark", "Apache Spark", "PySpark", "Hadoop", "Hive", "Pig",
    "Flink", "Storm", "Kafka", "Apache Kafka"
}

# ============================================
# CLOUD & DEVOPS
# ============================================

CLOUD_DEVOPS = {
    # Cloud Providers
    "AWS", "Azure", "GCP", "Google Cloud", "IBM Cloud", "Oracle Cloud",
    
    # AWS Services
    "EC2", "S3", "Lambda", "RDS", "DynamoDB", "CloudWatch", "SageMaker",
    "EMR", "Redshift", "Kinesis",
    
    # Azure Services
    "Azure DevOps", "Azure ML", "Azure Data Factory",
    
    # GCP Services
    "BigQuery", "Cloud Functions", "Cloud Run", "Dataflow", "Dataproc",
    
    # Containers & Orchestration
    "Docker", "Kubernetes", "K8s", "OpenShift", "Rancher", "Helm",
    
    # CI/CD
    "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI",
    "Bamboo", "TeamCity", "ArgoCD",
    
    # Infrastructure as Code
    "Terraform", "Ansible", "Puppet", "Chef", "CloudFormation",
    
    # Monitoring
    "Prometheus", "Grafana", "Datadog", "New Relic", "Splunk", "ELK",
    "Elasticsearch", "Logstash", "Kibana"
}

# ============================================
# OUTILS & VERSIONNING
# ============================================

TOOLS = {
    # Version Control
    "Git", "GitHub", "GitLab", "Bitbucket", "SVN",
    
    # Project Management
    "Jira", "Confluence", "Trello", "Asana", "Monday",
    
    # IDE
    "VS Code", "PyCharm", "IntelliJ", "Eclipse", "NetBeans",
    
    # Testing
    "Pytest", "Jest", "Selenium", "Cypress", "JUnit", "TestNG",
    "Postman", "SoapUI"
}

# ============================================
# MÉTHODOLOGIES & CONCEPTS
# ============================================

METHODOLOGIES = {
    # Agile
    "Agile", "Scrum", "Kanban", "SAFe", "Lean",
    
    # Architecture
    "Microservices", "REST", "REST API", "GraphQL", "gRPC", "SOAP",
    "API", "ETL", "CI/CD", "DevOps", "MLOps",
    
    # Design Patterns
    "MVC", "MVVM", "DDD", "TDD", "BDD",
    
    # Security
    "OAuth", "JWT", "SSL", "TLS", "HTTPS"
}

# ============================================
# DATA ENGINEERING
# ============================================

DATA_ENGINEERING = {
    "ETL", "Data Pipeline", "Data Warehouse", "Data Lake",
    "Airflow", "Apache Airflow", "Luigi", "Prefect", "Dagster",
    "dbt", "Snowflake", "Databricks", "Fivetran", "Airbyte",
    "Talend", "Informatica", "SSIS"
}

# ============================================
# MOBILE
# ============================================

MOBILE = {
    "Android", "iOS", "React Native", "Flutter", "Xamarin",
    "Ionic", "Cordova", "SwiftUI", "Jetpack Compose"
}

# ============================================
# AUTRES TECHNOLOGIES
# ============================================

OTHER_TECH = {
    "Linux", "Unix", "Windows Server", "Apache", "Nginx",
    "Tableau", "Power BI", "Looker", "Metabase", "Superset",
    "Blockchain", "Ethereum", "Solidity", "Web3"
}

# ============================================
# VARIATIONS & ALIAS
# ============================================

SKILL_VARIATIONS = {
    # Normalisation des variations
    "reactjs": "React",
    "react.js": "React",
    "nodejs": "Node.js",
    "node": "Node.js",
    "nestjs": "NestJS",
    "nest.js": "NestJS",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "angular": "Angular",
    "angularjs": "Angular",
    "next": "Next.js",
    "nextjs": "Next.js",
    "nuxt": "Nuxt.js",
    "nuxtjs": "Nuxt.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "k8s": "Kubernetes",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongo": "MongoDB",
    "tf": "TensorFlow",
    "sklearn": "Scikit-learn",
    "scikit": "Scikit-learn",
    "cv2": "OpenCV",
    "opencv": "OpenCV",
    "jupyter": "Jupyter Notebook",
    "aws": "AWS",
    "gcp": "GCP",
    "google cloud platform": "GCP",
    "microsoft azure": "Azure",
}

# ============================================
# COMBINAISON COMPLÈTE
# ============================================

def get_all_skills() -> Set[str]:
    """
    Retourne l'ensemble complet de toutes les compétences.
    
    Returns:
        Set de toutes les compétences
    """
    all_skills = set()
    
    all_skills.update(PROGRAMMING_LANGUAGES)
    all_skills.update(WEB_FRAMEWORKS)
    all_skills.update(DATABASES)
    all_skills.update(DATA_SCIENCE_ML)
    all_skills.update(CLOUD_DEVOPS)
    all_skills.update(TOOLS)
    all_skills.update(METHODOLOGIES)
    all_skills.update(DATA_ENGINEERING)
    all_skills.update(MOBILE)
    all_skills.update(OTHER_TECH)
    
    return all_skills


def get_skills_by_category() -> Dict[str, Set[str]]:
    """
    Retourne les compétences organisées par catégorie.
    
    Returns:
        Dictionnaire {catégorie: set de compétences}
    """
    return {
        "Programming Languages": PROGRAMMING_LANGUAGES,
        "Web Frameworks": WEB_FRAMEWORKS,
        "Databases": DATABASES,
        "Data Science & ML": DATA_SCIENCE_ML,
        "Cloud & DevOps": CLOUD_DEVOPS,
        "Tools": TOOLS,
        "Methodologies": METHODOLOGIES,
        "Data Engineering": DATA_ENGINEERING,
        "Mobile": MOBILE,
        "Other": OTHER_TECH
    }


def normalize_skill(skill: str) -> str:
    """
    Normalise une compétence (gère les variations).
    
    Args:
        skill: Compétence à normaliser
    
    Returns:
        Compétence normalisée
    
    Example:
        >>> normalize_skill("reactjs")
        "React"
        >>> normalize_skill("k8s")
        "Kubernetes"
    """
    skill_lower = skill.lower().strip()
    
    # Vérifier les variations connues
    if skill_lower in SKILL_VARIATIONS:
        return SKILL_VARIATIONS[skill_lower]
    
    # Sinon, retourner avec première lettre majuscule
    return skill.strip()


# ============================================
# STATISTIQUES
# ============================================

if __name__ == "__main__":
    all_skills = get_all_skills()
    categories = get_skills_by_category()
    
    print("=" * 60)
    print("📊 STATISTIQUES - BASE DE COMPÉTENCES")
    print("=" * 60)
    print(f"\n✅ Total compétences : {len(all_skills)}")
    print(f"✅ Total variations : {len(SKILL_VARIATIONS)}")
    print(f"\n📋 Répartition par catégorie :")
    
    for category, skills in categories.items():
        print(f"   • {category}: {len(skills)} compétences")
    
    print("\n" + "=" * 60)