import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
import urllib.parse
import os

INPUT_CSV = "data/extracted_knowledge.csv"
OUTPUT_TTL = "kg_artifacts/initial_graph.ttl"

# Création d'un "Namespace" personnalisé pour votre projet privé
# C'est comme le préfixe de votre propre base de données
EX = Namespace("http://cinema-controversy.org/entity/")
SCHEMA = Namespace("http://schema.org/")

def build_graph():
    print("Initialisation du Graphe RDF...")
    g = Graph()
    
    # Lier les préfixes pour que le fichier final soit lisible
    g.bind("ex", EX)
    g.bind("schema", SCHEMA)
    
    print("Lecture des entités extraites...")
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"Erreur: Le fichier {INPUT_CSV} est introuvable.")
        return

    # On se concentre uniquement sur les PERSONNES pour commencer votre organigramme
    persons = df[df["Type"] == "PERSON"]["Entity"].unique()
    
    triplets_count = 0
    
    for person_name in persons:
        # Nettoyage du nom pour en faire un lien valide (ex: "Harvey Weinstein" -> "Harvey_Weinstein")
        safe_name = urllib.parse.quote(person_name.replace(" ", "_"))
        person_uri = EX[safe_name]
        
        # Ajout du triplet 1 : Cette URI est une Personne
        g.add((person_uri, RDF.type, SCHEMA.Person))
        
        # Ajout du triplet 2 : Le nom lisible de cette personne
        g.add((person_uri, RDFS.label, Literal(person_name, datatype=XSD.string)))
        
        triplets_count += 2

    # Création du dossier de destination s'il n'existe pas
    os.makedirs("kg_artifacts", exist_ok=True)
    
    # Sauvegarde du graphe au format Turtle (.ttl)
    g.serialize(destination=OUTPUT_TTL, format="turtle")
    
    print(f"\nTerminé ! {triplets_count} triplets ont été créés.")
    print(f"Votre graphe initial a été sauvegardé dans : {OUTPUT_TTL}")

if __name__ == "__main__":
    build_graph()