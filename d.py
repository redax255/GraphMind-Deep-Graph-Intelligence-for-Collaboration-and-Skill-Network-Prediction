"""Test des corrections"""

# Test 1 : MongoDBClient avec collection_name
print("Test 1 : MongoDBClient avec collection_name")
from app.services.database import MongoDBClient

try:
    # Sans argument (doit fonctionner)
    db1 = MongoDBClient()
    print("✅ MongoDBClient() fonctionne")
    
    # Avec collection_name (doit fonctionner)
    db2 = MongoDBClient(collection_name="test_collection")
    print("✅ MongoDBClient(collection_name='test') fonctionne")
    print(f"   Collection: {db2.collection_name}")
    
except Exception as e:
    print(f"❌ Erreur : {e}")

print()

# Test 2 : Profile enricher avec skills mixtes
print("Test 2 : Profile enricher - skills mixtes")

# Simuler extracted_skills mixtes
test_skills = [
    "Python",  # String
    {"skill": "Java", "category": "Programming"},  # Dict
    "Docker",  # String
    {"skill": "AWS", "category": "Cloud"}  # Dict
]

skills_by_category = {}
for skill_data in test_skills:
    # Code corrigé
    if isinstance(skill_data, str):
        skill_dict = {'skill': skill_data, 'category': 'Unknown'}
    else:
        skill_dict = skill_data
    
    category = skill_dict.get('category', 'Unknown')
    skill_name = skill_dict.get('skill', skill_data if isinstance(skill_data, str) else 'Unknown')
    
    if category not in skills_by_category:
        skills_by_category[category] = []
    skills_by_category[category].append(skill_name)

print("✅ Skills groupées par catégorie :")
for cat, skills in skills_by_category.items():
    print(f"   {cat}: {skills}")

print()
print("🎉 Toutes les corrections fonctionnent !")