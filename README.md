# Hollywood Controversy Knowledge Graph & RAG System

Ce projet académique implémente un pipeline complet d'ingénierie des connaissances, allant de l'extraction d'entités nommées (NER) à la création d'un système de Question-Réponse (RAG) basé sur un graphe RDF massif (plus de 52 000 triplets). Il modélise les réseaux de collaborations au sein de l'industrie cinématographique hollywoodienne.

## 🛠 Prérequis et Installation

1. **Environnement Python** : Python 3.9 ou supérieur recommandé.
2. **Ollama** : Le système RAG utilise un LLM en local. Vous devez installer [Ollama](https://ollama.com/) et télécharger le modèle utilisé :
   ollama pull llama3.2
3. Dépendances Python : Installez les bibliothèques requises et le modèle linguistique Spacy :
    pip install -r requirements.txt
    python -m spacy download en_core_web_trf

Ordre d'Exécution du Pipeline
Pour reproduire les résultats du rapport, exécutez les scripts dans l'ordre suivant depuis la racine du projet :

1. Extraction d'Information (NER)
Extrait les entités (Personnes, Organisations) depuis les textes bruts.
    python src/ie/ner_extraction.py

2. Construction et Expansion du Graphe (KG)
Crée le graphe RDF de base, l'aligne avec Wikidata (owl:sameAs), puis l'étend massivement via des requêtes SPARQL.
    python src/kg/build_initial_kg.py
    python src/kg/align_entities.py
    python src/kg/expand_kg.py

3. Raisonnement Sémantique (SWRL)
Applique des règles logiques pour déduire de nouvelles relations implicites (ex: workedWith).
    python src/reason/swrl_reasoning.py

4. Apprentissage de Représentations (KGE)
Entraîne les modèles TransE et ComplEx sur le graphe (Link Prediction).
    python src/kge/train_kge.py

5. Interrogation Sémantique (RAG)
Lance le système de Question-Réponse. Note : Ce module utilise une extraction hybride optimisée (API native RDFlib + Python) pour contourner les limites de temps de calcul de SPARQL sur un graphe dense, offrant une réponse en une fraction de seconde.
    python src/rag/rag_sparql.py

Architecture du Projet
data/ : Contient les textes sources et les extractions CSV (NER).

kg_artifacts/ : Contient l'ontologie de base (.owl) et le graphe final étendu (expanded.nt).

src/ : Code source divisé par modules :

ie/ : Information Extraction

kg/ : Knowledge Graph construction & expansion

kge/ : Knowledge Graph Embeddings

rag/ : Retrieval-Augmented Generation

reason/ : Inférence logique