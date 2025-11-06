# installer pymongo et tester la connexion avec la base de donnees
pip install pymongo
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); print(client.list_database_names())"



# avant d'installer les dependances depuis requirements.txt
pip install torch==2.1.1 torchvision==0.16.1 torchaudio==2.1.1
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.1.0+cpu.html
pip install networkx==2.8.8