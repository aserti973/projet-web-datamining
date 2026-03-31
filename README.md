# Hollywood Controversy Knowledge Graph & RAG System

Ce projet académique implémente un pipeline complet d’ingénierie des connaissances, allant de l’extraction d’entités nommées (NER) à la mise en place d’un système de Question-Réponse (RAG) basé sur un graphe RDF massif (plus de **52 000 triplets**).

L’objectif est de modéliser et analyser les réseaux de collaboration au sein de l’industrie cinématographique hollywoodienne.

---

## Prérequis

- **Python** : version 3.9 ou supérieure
- **Ollama** : nécessaire pour exécuter le LLM en local  
  https://ollama.com/

### Installation du modèle LLM

```bash
ollama pull llama3.2
```
## Installation

Installez les dépendances Python ainsi que le modèle linguistique spaCy :
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_trf
```
## Pipeline d’Exécution

Pour reproduire les résultats du projet, exécutez les scripts dans l’ordre suivant depuis la racine :

## 1️⃣ Extraction d’Information (NER)

Extraction des entités nommées (personnes, organisations) à partir de textes bruts.
```bash
python src/ie/ner_extraction.py
```
## 2️⃣ Construction et Expansion du Graphe (Knowledge Graph)
Création du graphe RDF initial
Alignement avec Wikidata (owl:sameAs)
Enrichissement via requêtes SPARQL
```bash
python src/kg/build_initial_kg.py
python src/kg/align_entities.py
python src/kg/expand_kg.py
```
## 3️⃣ Raisonnement Sémantique (SWRL)

Application de règles logiques pour inférer de nouvelles relations implicites
(exemple : workedWith).
```bash
python src/reason/swrl_reasoning.py
```
## 4️⃣ Apprentissage de Représentations (KGE)

Entraînement de modèles de Knowledge Graph Embeddings :

TransE
ComplEx

Objectif : prédiction de liens (link prediction).
```bash
python src/kge/train_kge.py
```
## 5️⃣ Interrogation Sémantique (RAG)

Lancement du système de Question-Réponse basé sur le graphe.

Optimisation importante :
Ce module utilise une approche hybride (API native RDFlib + Python) pour contourner les limitations de performance de SPARQL sur des graphes denses, permettant des réponses en temps quasi instantané.
```bash
python src/rag/rag_sparql.py
```
## Architecture du Projet
```bash
.
├── data/               # Textes sources + extractions NER (CSV)
├── kg_artifacts/      # Ontologie (.owl) + graphe étendu (.nt)
├── src/
│   ├── ie/            # Extraction d'information (NER)
│   ├── kg/            # Construction, alignement et expansion du graphe
│   ├── reason/        # Raisonnement logique (SWRL)
│   ├── kge/           # Modèles d'embeddings (TransE, ComplEx)
│   └── rag/           # Système RAG (Question-Réponse)
├── requirements.txt
└── README.md
```